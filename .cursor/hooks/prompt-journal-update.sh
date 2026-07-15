#!/bin/bash
# Reminds the agent to update today's engineering journal before stopping.

TODAY=$(date +%Y-%m-%d)
JOURNAL_FILE="docs/engineering-journal/${TODAY}.md"

cat <<EOF
{
  "followup_message": "Update ${JOURNAL_FILE} before ending this session. Fill in or append to: Today's Goal, What We Learned, Architectural Decisions, Problems, and Future Ideas. If nothing changed in a section, note that briefly."
}
EOF
