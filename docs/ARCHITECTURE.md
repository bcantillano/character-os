# Architecture

Character OS is composed of independent systems.

The LLM is not the character.

The LLM is only responsible for language generation and reasoning.

Persistent state belongs entirely to Character OS.

## Core Systems

Input

↓

Conversation Interpreter

↓

Character Brain

    Personality

    Knowledge

    Memory

    Emotion

    Goals

    Relationships

↓

Decision Engine

↓

Internal Thoughts

↓

Response Generator

↓

Output

---

Future systems

Vision

Motion

Robotics

Speech

Sensors

Dashboard

These systems should communicate through clean interfaces without tightly coupling to the Character Brain.