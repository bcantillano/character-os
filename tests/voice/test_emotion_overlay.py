"""Emotion overlay unit tests."""

from character_os.core.types import EmotionalDrives
from character_os.voice.emotion_overlay import emotion_delivery_overlay


def test_overlay_empty_for_mid_drives():
    drives = EmotionalDrives(
        curiosity=0.5,
        trust=0.5,
        excitement=0.5,
        fear=0.3,
        confidence=0.5,
        energy=0.5,
    )
    assert emotion_delivery_overlay(drives) == ""


def test_overlay_includes_curiosity_and_fear():
    drives = EmotionalDrives(
        curiosity=0.85,
        trust=0.4,
        excitement=0.4,
        fear=0.7,
        confidence=0.5,
        energy=0.5,
    )
    text = emotion_delivery_overlay(drives)
    assert "curiosity" in text.lower()
    assert "softer" in text.lower() or "careful" in text.lower()
