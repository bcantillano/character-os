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


def test_validate_existing_packs():
    studio = StudioService()
    assert studio.validate_character("lumen").ok
    assert studio.validate_character("captain-redbeard").ok
    assert studio.validate_world("everyday-present").ok
    assert studio.validate_world("caribbean-1790").ok


def test_validate_rejects_bad_character(tmp_path: Path):
    root = tmp_path
    (root / "characters" / "broken").mkdir(parents=True)
    (root / "worlds" / "everyday-present").mkdir(parents=True)
    (root / "worlds" / "everyday-present" / "world.yaml").write_text(
        "id: everyday-present\nname: Everyday Present\ndescription: test\n",
        encoding="utf-8",
    )
    (root / "characters" / "broken" / "character.yaml").write_text(
        "id: broken\nname: Broken\n",
        encoding="utf-8",
    )
    studio = StudioService(root=root, data_dir=root / "data")
    report = studio.validate_character("broken")
    assert not report.ok
    assert any("world" in e.lower() or "missing" in e.lower() for e in report.errors)


def test_edit_character_trait_and_drive(tmp_path: Path):
    root = tmp_path
    (root / "characters").mkdir()
    (root / "worlds" / "everyday-present").mkdir(parents=True)
    (root / "worlds" / "everyday-present" / "world.yaml").write_text(
        "id: everyday-present\nname: Everyday Present\ndescription: test\n",
        encoding="utf-8",
    )
    studio = StudioService(root=root, data_dir=root / "data")
    studio.create_character(
        "edit-bot",
        name="Edit Bot",
        world_id="everyday-present",
    )
    studio.edit_character(
        "edit-bot",
        add_traits=["witty"],
        drives={"curiosity": 0.8},
        add_goal=("scout", "Scout the room carefully"),
    )
    detail = studio.show_character("edit-bot")
    assert "witty" in detail.traits
    assert detail.drives["curiosity"] == 0.8
    assert any(g["id"] == "scout" for g in detail.goals)
    assert studio.validate_character("edit-bot").ok
    assert (root / "characters" / "edit-bot" / "character.yaml.bak").is_file()


def test_edit_character_rolls_back_invalid_drive(tmp_path: Path):
    root = tmp_path
    (root / "characters").mkdir()
    (root / "worlds" / "everyday-present").mkdir(parents=True)
    (root / "worlds" / "everyday-present" / "world.yaml").write_text(
        "id: everyday-present\nname: Everyday Present\ndescription: test\n",
        encoding="utf-8",
    )
    studio = StudioService(root=root, data_dir=root / "data")
    studio.create_character("safe-bot", name="Safe Bot", world_id="everyday-present")
    before = (root / "characters" / "safe-bot" / "character.yaml").read_text(encoding="utf-8")
    with pytest.raises(ValueError):
        studio.edit_character("safe-bot", drives={"curiosity": 9.0})
    after = (root / "characters" / "safe-bot" / "character.yaml").read_text(encoding="utf-8")
    assert after == before
