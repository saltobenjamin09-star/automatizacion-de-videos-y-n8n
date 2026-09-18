import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "video_config.json"


def test_video_config_has_required_structure():
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    for key in ("title", "output", "duration_seconds", "fps", "width", "height", "scenes"):
        assert key in config
    assert config["duration_seconds"] == sum(scene["duration"] for scene in config["scenes"])
    assert config["duration_seconds"] >= 320
    assert config["duration_seconds"] <= 360
    assert config["width"] >= 1280
    assert config["height"] >= 720


def test_scene_accents_are_hex_colors():
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    for scene in config["scenes"]:
        color = scene["accent"]
        assert len(color) == 7
        assert color.startswith("#")
        int(color[1:], 16)
