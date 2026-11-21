#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
dir=measurements/hot-partition

docker compose exec -T -e CASSANDRA__KEYSPACE=store -e CASSANDRA__CONSISTENCY_LEVEL=QUORUM \
  backend /app/.venv/bin/python - "$@" < "$dir/measure.py" > "$dir/results.csv"

docker compose exec -T cassandra1 nodetool flush store events_by_type
# Merge old and new SSTables so deleted rows do not inflate the measurements.
docker compose exec -T cassandra1 nodetool compact store events_by_type
# Sum the segments if Cassandra stored a partition in multiple SSTables.
docker compose exec -T cassandra1 sh -c \
  '/opt/cassandra/tools/bin/sstablepartitions --csv --min-rows 1 /var/lib/cassandra/data/store/events_by_type-*' |
  awk -F, '
    NR == FNR { if (FNR > 1) scenarios[$2] = $1; next }
    FNR == 1 { print "scenario,event_type,bucket,rows,size_bytes"; next }
    {
      split($1, key, ":")
      gsub(/"/, "", key[2])
      if (!(key[2] in scenarios)) next
      partition = scenarios[key[2]] "," substr(key[1], 2) "," key[2]
      rows[partition] += $6
      bytes[partition] += $5
    }
    END { for (p in rows) print p "," rows[p] "," bytes[p] }
  ' "$dir/results.csv" - > "$dir/partitions.csv"
