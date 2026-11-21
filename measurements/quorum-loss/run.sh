#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."

wait_nodes() {
  for ((attempt=0; attempt<45; attempt++)); do
    status=$(docker compose exec -T cassandra1 nodetool status)
    if [[ $(awk '$1 == "UN" { n++ } END { print n+0 }' <<< "$status") == "$1" ]]; then
      return
    fi
    sleep 2
  done
  echo "Expected $1 Cassandra nodes in UN state." >&2
  return 1
}

measure() {
  wait_nodes "$1"
  docker compose exec -T -e CASSANDRA__HOSTS=cassandra1 backend /app/.venv/bin/python - ONE QUORUM ALL \
    < measurements/one-all/compare.py > "measurements/quorum-loss/results-$1-nodes.csv"
}

measure 3
trap 'docker compose start cassandra2 cassandra3' EXIT
docker compose stop cassandra3
measure 2
docker compose stop cassandra2
measure 1
docker compose start cassandra2 cassandra3
wait_nodes 3
trap - EXIT
