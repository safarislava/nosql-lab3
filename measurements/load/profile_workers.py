"""Measure wall time of repository calls in every twentieth measured operation."""
import csv
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stdout
from functools import wraps
from threading import local
from time import perf_counter_ns

from infrastructure.persistence.cassandra.history_repository import CassandraHistoryRepository

worker = local()
output = csv.writer(sys.stdout, lineterminator="\n")
output.writerow(("operation", "clients", "samples", "phase", "mean_ms_per_sample"))


def timed_call(phase, method, *args, **kwargs):
    started = perf_counter_ns()
    try:
        return method(*args, **kwargs)
    finally:
        worker.times[phase] += perf_counter_ns() - started


class TimedFuture:
    def __init__(self, future):
        self.future = future

    def result(self):
        return timed_call("await_results", self.future.result)


def instrument(method):
    @wraps(method)
    def wrapped(*args, **kwargs):
        if getattr(worker, "times", None) is None:
            return method(*args, **kwargs)
        result = timed_call(method.__name__, method, *args, **kwargs)
        return TimedFuture(result) if method.__name__ == "_execute_async" else result
    return wrapped


for name in ("_execute", "_row_to_event", "_execute_async"):
    setattr(CassandraHistoryRepository, name, instrument(getattr(CassandraHistoryRepository, name)))


class ProfiledPool(ThreadPoolExecutor):
    def map(self, fn, attempts):
        if len(attempts) != benchmark["ATTEMPTS"]:
            return super().map(fn, attempts)
        profiles = []

        def sampled(index):
            if index % 20:
                return fn(index)
            worker.times = Counter()
            try:
                return timed_call("total", fn, index)
            finally:
                profiles.append(worker.times)
                worker.times = None

        results = list(super().map(sampled, attempts))
        totals = Counter()
        for profile in profiles:
            totals.update(profile)
        for phase, nanoseconds in totals.items():
            output.writerow((benchmark["operation"].__name__, benchmark["clients"],
                             len(profiles), phase, round(nanoseconds / len(profiles) / 1e6, 4)))
        return iter(results)


# Replace only the benchmark's executor, leaving the driver's pools intact.
source = sys.stdin.read()
pool_import = "from concurrent.futures import ThreadPoolExecutor"
if source.count(pool_import) != 1:
    sys.exit("Expected measure.py on stdin")
benchmark = {"__name__": "__main__", "ThreadPoolExecutor": ProfiledPool}
with redirect_stdout(sys.stderr):
    exec(compile(source.replace(pool_import, ""), "measure.py", "exec"), benchmark)
