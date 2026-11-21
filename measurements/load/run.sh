#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/../.."

docker compose exec -T backend /app/.venv/bin/python \
  -c "$(cat measurements/one-all/load_events.py)" < measurements/one-all/events.json
docker compose exec -T -e CASSANDRA__CONSISTENCY_LEVEL=QUORUM backend /app/.venv/bin/python - \
  < measurements/load/measure.py > measurements/load/results.csv
echo measurements/load/results.csv
