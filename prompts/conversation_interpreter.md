# Conversation Interpreter

Analyze the user's message in the context of an ongoing conversation with **{{character_name}}**.

## User Message

{{user_message}}

## Recent Context

{{memory_context}}

## Task

Extract structured signals from the user message. Do not respond in character.

Return:

1. **intent** — what the user is trying to do (ask, challenge, joke, share, threaten, etc.)
2. **topics** — subjects mentioned
3. **emotional_tone** — how the user seems to feel
4. **relationship_signals** — trust, familiarity, or hostility cues
5. **notable_facts** — anything worth remembering if new

Be concise. Focus on what matters to {{character_name}}.
