#!/usr/bin/env bash
set -euo pipefail
DIR="${1:-}"; MODE="${2:-run}"; PGURL="${PGURL:-}"
if [[ -z "$DIR" || -z "$PGURL" ]]; then echo "Usage: PGURL=... $0 migrations/<RUN-ID> [--dry-run]"; exit 1; fi
if [[ ! -d "$DIR" ]]; then echo "Folder not found: $DIR"; exit 1; fi
mkdir -p docs/run-logs
RUN_ID="$(date -u +"%Y%m%dT%H%M%SZ")"
LOG="docs/run-logs/${RUN_ID}_db-migrate.log"
echo "== DB MIGRATE ==" | tee "$LOG"
echo "Folder: $DIR" | tee -a "$LOG"; echo "PGURL: (redacted)" | tee -a "$LOG"; echo "Mode: ${MODE}" | tee -a "$LOG"; echo "" | tee -a "$LOG"
shopt -s nullglob; FILES=("$DIR"/*.sql)
if (( ${#FILES[@]} == 0 )); then echo "No .sql files in $DIR" | tee -a "$LOG"; exit 0; fi
for f in "${FILES[@]}"; do
  echo "--> $f" | tee -a "$LOG"
  if [[ "$MODE" == "--dry-run" ]]; then
    echo "[dry-run] would psql -v ON_ERROR_STOP=1 -f $f" | tee -a "$LOG"
  else
    PGPASSWORD="" psql "$PGURL" -v ON_ERROR_STOP=1 -f "$f" | tee -a "$LOG"
  fi
  echo "" | tee -a "$LOG"
done
echo "DONE" | tee -a "$LOG"
