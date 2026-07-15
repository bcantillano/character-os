# Prompts

Editable Markdown templates for LLM pipeline stages.

The engine loads these at runtime and injects context variables. Business logic stays in Python — prompts only describe *how* the LLM should reason or speak, never *what* state to update.

## Default Templates

| File | Pipeline stage |
|------|----------------|
| `conversation_interpreter.md` | Parse user input |
| `decision_engine.md` | Choose character behavior |
| `internal_thoughts.md` | Private monologue |
| `response_generator.md` | Spoken dialogue |

## Overrides

Characters can override any template via the `prompts` block in `character.yaml`:

```yaml
prompts:
  response_generator: characters/captain-redbeard/assets/response_generator.md
```

## Variables

Common template variables (engine-provided):

- `{{character_name}}` — display name
- `{{character_description}}` — identity summary
- `{{personality_summary}}` — formatted traits and voice
- `{{emotional_state}}` — current emotion labels and intensity
- `{{active_goals}}` — current goals
- `{{relevant_knowledge}}` — world + character facts for this turn
- `{{memory_context}}` — recent episodic memory
- `{{user_message}}` — latest user input
- `{{internal_thoughts}}` — prior monologue (response stage only)
