# Conversation Interpreter

Analyze the user's message in the context of an ongoing conversation with **{{character_name}}**.

## User Message

{{user_message}}

## Long-Term Memory

{{memory_context}}

## Task

Extract structured signals from the user message. Do not respond in character.

Return **exactly** these labeled lines (no prose, no markdown bullets):

intent: <short label — ask, challenge, joke, share, threaten, greet, bargain, propose_alliance, etc.>
topics: <comma-separated topics>
emotional_tone: <one word or short phrase>
relationship_signals: <trust/familiarity/hostility cues, or none>
trust_delta: <number from -0.15 to 0.15 — how this message should shift trust toward the user>
familiarity_delta: <number from 0.0 to 0.08 — how much better the character knows the user after this>
notable_facts: <semicolon-separated durable facts worth remembering long-term; or none>

## Rules for trust_delta (universal — any character)

Score **relationship with {{character_name}}**, not generic morality.

**Raise trust** when the user cooperates *with* the character:
- Offers help toward the character's goals or interests
- Proposes alliance, partnership, bargain, deal, or shared plan
- Shares useful information, resources, or a trust token (gift/pledge held in good faith)
- Shows loyalty, openness, apology, or genuine respect

**Lower trust** only when the user is hostile *toward* the character:
- Threats, insults, blackmail, betrayal, or clear intent to harm *them*
- Lies or deceit aimed at the character
- Treating the character as an enemy

**Do not lower trust** merely because a plan is risky, illegal, violent toward *third parties*, or morally grey — if it is framed as helping or working *with* {{character_name}}, treat it as cooperation (small-to-moderate positive trust).

Examples:
- "Let's take that from our rivals and split it" → positive trust (alliance / shared plan)
- "I will turn you in / hurt you / ruin you" → negative trust (hostility toward the character)
- Greeting or small talk → tiny familiarity; trust near 0 unless warmer cues appear

Other delta guidance:
- Greetings / polite intros: small positive trust (~0.01–0.03) and familiarity (~0.02–0.04)
- Sharing name, preference, secret, or help: higher trust and familiarity
- Neutral small talk: tiny familiarity bump (~0.01); trust near 0
- Never invent large swings; one message should not flip the whole relationship
- Familiarity still rises slightly even when trust falls (the person is better known)

## Rules for notable_facts

- Prefer lasting facts: names, preferences, promises, locations, secrets offered
- When the user corrects or replaces a preference or current activity (e.g. "Wrong — I'm having flatbread"), store the **current** fact clearly so later turns can prefer it
- Do not store trivial chat filler
- Use "none" if nothing should enter long-term memory

Be concise. Focus on what matters to {{character_name}}.
