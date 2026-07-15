# Conversation Interpreter

Analyze the user's message in the context of an ongoing conversation with **{{character_name}}**.

## User Message

{{user_message}}

## Long-Term Memory

{{memory_context}}

## Task

Extract structured signals from the user message. Do not respond in character.

Return **exactly** these labeled lines (no prose, no markdown bullets):

intent: <short label — ask, challenge, joke, share, threaten, greet, bargain, etc.>
topics: <comma-separated topics>
emotional_tone: <one word or short phrase>
relationship_signals: <trust/familiarity/hostility cues, or none>
notable_facts: <semicolon-separated durable facts worth remembering long-term; or none>

Rules for notable_facts:
- Prefer lasting facts: names, preferences, promises, locations, secrets offered
- Do not store trivial chat filler
- Use "none" if nothing should enter long-term memory

Be concise. Focus on what matters to {{character_name}}.
