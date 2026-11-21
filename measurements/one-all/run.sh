#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/../.."

dir=measurements/one-all
export COMPOSE_FILE="docker-compose.yml:$dir/compose.local.yml"

[[ -f frontend/dist/index.html ]] || (npm ci --prefix frontend && npm run build --prefix frontend)
docker compose up -d --build --wait
docker compose exec -T backend /app/.venv/bin/python -c "$(cat "$dir/load_events.py")" < "$dir/events.json"
docker compose exec -T backend /app/.venv/bin/python - < "$dir/compare.py" > "$dir/results.csv"
echo "$dir/results.csv"
