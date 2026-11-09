#!/usr/bin/env bash
# Run on the server, nightly from cron: dump the database and upload it to R2 under backups/.
set -euo pipefail

cd "$(dirname "$0")/.."
compose="docker compose -f docker-compose.prod.yml"
key="backups/$(date -u +%Y-%m-%d).dump"

# The dump streams from the db container straight into the api container, which uploads it.
$compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom' \
  | $compose exec -T api python -m app.backup "$key"
