"""Phase 2 Character Studio service tests."""

from pathlib import Path

import pytest

from character_os.studio.service import StudioService


def test_list_characters_includes_lumen_and_redbeard():
    studio = StudioService()
    ids = {c.id for c in studio.list_characters()}
    assert "lumen" in ids
    assert "captain-redbeard" in ids


def test_list_worlds_includes_known_packs():
    studio = StudioService()
    ids = {w.id for w in studio.list_worlds()}
    assert "everyday-present" in ids
    assert "caribbean-1790" in ids


def test_show_character_lumen():
    studio = StudioService()
    detail = studio.show_character("lumen")
    assert detail.name == "Lumen"
    assert detail.world == "everyday-present"
    assert detail.tts_voice == "cedar"
    assert "response_generator" in detail.prompt_overrides


def test_show_world_caribbean():
    studio = StudioService()
    world = studio.show_world("caribbean-1790")
    assert world["id"] == "caribbean-1790"
    assert world["knowledge_count"] >= 1


def test_create_character_scaffold(tmp_path: Path):
    # Use real repo loaders for worlds, but write into a temp characters dir via monkeypatch root.
    # Simpler: create under real characters/ then clean up — prefer tmp root with copied world.
    root = tmp_path
    (root / "characters").mkdir()
    (root / "worlds" / "everyday-present").mkdir(parents=True)
    (root / "worlds" / "everyday-present" / "world.yaml").write_text(
        "id: everyday-present\nname: Everyday Present\ndescription: test\n",
        encoding="utf-8",
    )
    studio = StudioService(root=root, data_dir=root / "data")
    path = studio.create_character(
        "probe-bot",
        name="Probe Bot",
        world_id="everyday-present",
        description="A scaffolded test character.",
    )
    assert (path / "character.yaml").is_file()
    detail = studio.show_character("probe-bot")
    assert detail.name == "Probe Bot"
    assert detail.world == "everyday-present"

    with pytest.raises(FileExistsError):
        studio.create_character(
            "probe-bot",
            name="Probe Bot",
            world_id="everyday-present",
        )


def test_inspect_runtime_empty_db(tmp_path: Path):
    studio = StudioService(data_dir=tmp_path)
    snap = studio.inspect_runtime("lumen")
    assert snap.character_id == "lumen"
    assert isinstance(snap.active_memories, list)
    assert isinstance(snap.drives, dict)
