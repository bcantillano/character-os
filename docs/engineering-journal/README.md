# Engineering Journal

One markdown file per development session.

## Naming

```
YYYY-MM-DD.md
```

Examples: `2026-07-13.md`, `2026-07-18.md`

## Template

Every session file uses this structure:

```markdown
# YYYY-MM-DD

## Today's Goal

## What We Learned

## Architectural Decisions

## Problems

## Future Ideas
```

## Automation

- **Session start**: `.cursor/hooks/ensure-engineering-journal.sh` creates today's file if missing.
- **Session end**: `.cursor/hooks/prompt-journal-update.sh` reminds the agent to fill in the journal.
- **Cursor rule**: `.cursor/rules/engineering-journal.mdc` enforces journal updates every session.
