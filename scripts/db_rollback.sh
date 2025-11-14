#!/usr/bin/env bash
set -euo pipefail
DIR="${1:-}"; PGURL="${PGURL:-}"
if [[ -z "$DIR" || -z "$PGURL" ]]; then echo "Usage: PGURL=... $0 migrations/<RUN-ID>"; exit 1; fi
ROLL="$DIR/99_rollback.sql"
if [[ ! -f "$ROLL" ]]; then echo "No rollback file at $ROLL"; exit 0; fi
mkdir -p docs/run-logs
RUN_ID="$(date -u +"%Y%m%dT%H%M%SZ")"
LOG="docs/run-logs/${RUN_ID}_db-rollback.log"
echo "== DB ROLLBACK ==" | tee "$LOG"
echo "File: $ROLL" | tee -a "$LOG"
PGPASSWORD="" psql "$PGURL" -v ON_ERROR_STOP=1 -f "$ROLL" | tee -a "$LOG"
echo "DONE" | tee -a "$LOG"
