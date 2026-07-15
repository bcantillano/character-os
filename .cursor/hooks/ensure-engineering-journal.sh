#!/bin/bash
# Creates today's engineering journal file if it does not exist.

set -euo pipefail

JOURNAL_DIR="docs/engineering-journal"
TODAY=$(date +%Y-%m-%d)
JOURNAL_FILE="${JOURNAL_DIR}/${TODAY}.md"

mkdir -p "$JOURNAL_DIR"

if [[ ! -f "$JOURNAL_FILE" ]]; then
  cat > "$JOURNAL_FILE" <<EOF
# ${TODAY}

## Today's Goal

## What We Learned

## Architectural Decisions

## Problems

## Future Ideas
EOF
fi

cat <<EOF
{
  "additional_context": "Engineering journal for this session: ${JOURNAL_FILE}. At session end, update all sections (Today's Goal, What We Learned, Architectural Decisions, Problems, Future Ideas) with what happened in this session. Append to existing content when the file already has entries from earlier today."
}
EOF
