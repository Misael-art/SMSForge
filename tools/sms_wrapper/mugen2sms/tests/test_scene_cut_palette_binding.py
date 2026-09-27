"""P1/P2 metasprite IDs must target the matching palette tile pool."""
from __future__ import annotations

import pytest

from mugen2sms.generators.scene_cut import _palette_metas, _runtime_table
from mugen2sms.generators.smsdev import Artifact


def test_palette_metadata_is_emitted_as_distinct_artifacts():
    p1 = {
        "F_A0F0_META": Artifact("F_A0F0_META", b"p1-right", "air"),
        "F_A0F0_METAL": Artifact("F_A0F0_METAL", b"p1-left", "air"),
    }
    p2 = {
        "F_A0F0_META": Artifact("F_A0F0_META", b"p2-right", "air"),
        "F_A0F0_METAL": Artifact("F_A0F0_METAL", b"p2-left", "air"),
    }

    emitted = _palette_metas("F_A0F0", p1, p2)

    assert [(item.symbol, item.data) for item in emitted] == [
        ("F_A0F0_META", b"p1-right"),
        ("F_A0F0_P2_META", b"p2-right"),
        ("F_A0F0_METAL", b"p1-left"),
        ("F_A0F0_P2_METAL", b"p2-left"),
    ]


def test_missing_palette_metadata_is_rejected():
    p1 = {"F_A0F0_META": Artifact("F_A0F0_META", b"p1-right", "air"),
          "F_A0F0_METAL": Artifact("F_A0F0_METAL", b"p1-left", "air")}

    with pytest.raises(ValueError, match="palette-specific metasprite is missing"):
        _palette_metas("F_A0F0", p1, {})


def test_runtime_frame_selects_both_palette_metadata_pairs():
    stem = "F_A0F0"
    artifacts = [
        Artifact(stem + suffix, b"x", "air")
        for suffix in ("_META", "_METAL", "_P2_META", "_P2_METAL", "_AXIS")
    ]
    role_frames = {"idle": [{"stem": stem, "duration": 4,
                              "width": 16, "height": 16}]}
    runtime = {key: 0 for key in (
        "life", "walk_fwd", "walk_back", "jump_vy", "gravity",
        "damage_punch", "damage_kick", "damage_special", "special_vel",
        "hitstop", "hit_push", "guard_push")}

    header = _runtime_table(
        [{"role": "idle", "action": 0, "loop_start": 0}], role_frames, 1,
        artifacts,
        {stem + "_TILES": (2, 0), stem + "_P2_TILES": (2, 64)},
        [0] * 16, runtime)

    assert f"{stem}_META, {stem}_METAL, 0, {stem}_AXIS, 16, 16, " \
           f"{stem}_P2_META, {stem}_P2_METAL" in header
