"""Build a banked, two-palette runtime cut from real MUGEN character data.

The source archive stays outside the repository.  This generator writes only
derived artifacts to the caller-selected output directory and emits a compact
C table consumed by the SMS fight runtime.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import struct
import sys
import tempfile
from collections import Counter
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from mugen2sms import character as character_loader
from mugen2sms.analysis.fidelity import classify_character
from mugen2sms.analysis.sms_budget import SmsLimits
from mugen2sms.converters import sms_scale as scale
from mugen2sms.generators import smsdev
from mugen2sms.generators.runtime_format import decode_indices
from mugen2sms.source import Source
from mugen2sms.converters.sms_tiles import _pal

BANK_PAGE = 16384
STREAM_CHUNK_BYTES = 64
PALETTE_COLORS_PER_SIDE = 7


def _nearest_word(rgb: tuple[int, int, int]) -> int:
    r, g, b = _pal.nearest_code(rgb)
    return r | (g << 2) | (b << 4)


def _word_rgb(word: int) -> tuple[int, int, int]:
    return _pal.code_rgb((word & 3, (word >> 2) & 3, (word >> 4) & 3))


def _distance(a: int, b: int) -> int:
    ar, ag, ab = _word_rgb(a)
    br, bg, bb = _word_rgb(b)
    return (ar - br) ** 2 + (ag - bg) ** 2 + (ab - bb) ** 2


def _palette_codebook(entries: list[smsdev.Artifact], by_symbol: dict[str, smsdev.Artifact]) -> list[int]:
    counts: Counter[int] = Counter()
    for entry in entries:
        if not entry.symbol.endswith("_TILES"):
            continue
        palette = by_symbol[entry.symbol.removesuffix("_TILES") + "_PAL"].data
        blob = entry.data
        for offset in range(0, len(blob), 32):
            for index in decode_indices(blob[offset:offset + 32]):
                if index:
                    counts[palette[index]] += 1
    return [word for word, _ in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
            if word != 0][:PALETTE_COLORS_PER_SIDE]


def _remap_blob(blob: bytes, palette: bytes, codebook: list[int], offset: int) -> bytes:
    """Map each local pose palette to the shared seven-color character line."""
    if len(palette) != 16 or not codebook:
        raise ValueError("pose palette/codebook is empty or malformed")
    index_map = [0] * 16
    for index in range(1, 16):
        word = palette[index]
        # Index 0 in CRAM is transparent; opaque black is kept in an available
        # codebook slot when present, never mapped to transparency.
        slot = min(range(len(codebook)), key=lambda n: (_distance(word, codebook[n]), n))
        index_map[index] = slot + 1 + offset
    out = bytearray()
    for pos in range(0, len(blob), 32):
        pixels = decode_indices(blob[pos:pos + 32])
        mapped = [0 if value == 0 else index_map[value] for value in pixels]
        encoded = bytearray()
        for row in range(8):
            planes = [0, 0, 0, 0]
            for x in range(8):
                color = mapped[row * 8 + x]
                for plane in range(4):
                    planes[plane] |= ((color >> plane) & 1) << (7 - x)
            encoded.extend(planes)
        out.extend(encoded)
    return bytes(out)


def _scale_signed(value: int, divisor: int) -> int:
    # C-style truncation toward zero; AIR coordinates can be negative.
    return int(value / divisor)


def _correct_frame_metadata(artifacts: list[smsdev.Artifact], ch, actions: dict,
                            by_key: dict, uniformly_scaled: bool = False) -> None:
    by_symbol = {a.symbol: a for a in artifacts}
    slug = smsdev.slug(Path(ch.def_path).stem)
    for action_id, action in actions.items():
        for frame_index, frame in enumerate(action.frames):
            sprite = by_key[(frame.group, frame.image)]
            divisor = (1 if uniformly_scaled else
                       (scale.SCALE if scale.needs_scale(sprite.width, sprite.height) else 1))
            stem = f"{slug}_A{action_id}F{frame_index}"
            axis = by_symbol.get(stem + "_AXIS")
            if axis:
                ax = _scale_signed(frame.x - sprite.axis_x, divisor)
                ay = _scale_signed(frame.y - sprite.axis_y, divisor)
                axis.data = struct.pack("<2h", ax, ay)
            clsn = by_symbol.get(stem + "_CLSN")
            if clsn:
                values = [struct.unpack_from("<h", clsn.data, pos)[0]
                          for pos in range(0, len(clsn.data), 2)]
                scaled = [value if value == -32767 else _scale_signed(value, divisor)
                          for value in values]
                clsn.data = b"".join(struct.pack("<h", value) for value in scaled)


def _selected_variant(ch, actions: dict[int, object], palette: list[tuple[int, int, int]] | None):
    variant = replace(ch, anims=actions, commands=ch.commands)
    if palette is not None:
        variant.sprites = [replace(sprite, palette=palette) for sprite in ch.sprites]
    return variant


def _artifacts(manifest) -> list[smsdev.Artifact]:
    return [smsdev.Artifact(entry["symbol"], entry["blob"], entry["source"])
            for entry in manifest.entries]


def _palette_metas(stem: str, p1_by_symbol: dict[str, smsdev.Artifact],
                   p2_by_symbol: dict[str, smsdev.Artifact]) -> list[smsdev.Artifact]:
    """Keep each color variant's metasprite IDs paired with its tile pool."""
    output = []
    for suffix in ("_META", "_METAL"):
        symbol = stem + suffix
        p1_meta, p2_meta = p1_by_symbol.get(symbol), p2_by_symbol.get(symbol)
        if p1_meta is None or p2_meta is None:
            raise ValueError(f"palette-specific metasprite is missing: {symbol}")
        output.append(copy.copy(p1_meta))
        output.append(smsdev.Artifact(stem + "_P2" + suffix,
                                      p2_meta.data, p2_meta.source))
    return output


def _runtime_table(roles: list[dict], role_frames: dict[str, list[dict]],
                   pose_count: int, artifacts: list[smsdev.Artifact],
                   bank_map: dict[str, tuple[int, int]], palette: list[int],
                   runtime: dict[str, int]) -> str:
    symbols = {artifact.symbol for artifact in artifacts}
    lines = ["", "/* Runtime tables: generated from AIR/SFF/ACT/CNS/CMD. */",
             f"#define CUT_POSE_COUNT {pose_count}", "",
             f"#define CUT_MAX_LIFE {runtime['life']}",
             f"#define CUT_WALK_FWD_Q8 {runtime['walk_fwd']}",
             f"#define CUT_WALK_BACK_Q8 {runtime['walk_back']}",
             f"#define CUT_JUMP_VY_Q8 {runtime['jump_vy']}",
             f"#define CUT_GRAVITY_Q8 {runtime['gravity']}",
             f"#define CUT_DAMAGE_PUNCH {runtime['damage_punch']}",
             f"#define CUT_DAMAGE_KICK {runtime['damage_kick']}",
             f"#define CUT_DAMAGE_SPECIAL {runtime['damage_special']}",
             f"#define CUT_SPECIAL_VEL_Q8 {runtime['special_vel']}",
             f"#define CUT_HITSTOP {runtime['hitstop']}",
             f"#define CUT_HIT_PUSH_PX {runtime['hit_push']}",
             f"#define CUT_GUARD_PUSH_PX {runtime['guard_push']}",
             f"#define CUT_STREAM_CHUNK_BYTES {STREAM_CHUNK_BYTES}", ""]
    for index, role in enumerate(roles):
        lines.append(f"#define CUT_ANIM_{role['role'].upper()} {index}")
    lines += ["",
             "static const PoseRef poses_all[CUT_POSE_COUNT * 2] = {"]
    for suffix in ("", "_P2"):
        for role in roles:
            for frame in role_frames[role["role"]]:
                stem = frame["stem"]
                tile_symbol = stem + suffix + "_TILES"
                if tile_symbol not in bank_map:
                    raise ValueError(f"missing bank entry for {tile_symbol}")
                lines.append(f"    {{ {tile_symbol}_BANK, {tile_symbol}_OFF, {tile_symbol}_SIZE }},")
    lines += ["};", "", "static const Frame frames_all[CUT_POSE_COUNT] = {"]
    pose_index = 0
    for role in roles:
        for frame in role_frames[role["role"]]:
            stem = frame["stem"]
            clsn = stem + "_CLSN" if stem + "_CLSN" in symbols else "0"
            lines.append(
                f"    {{ {frame['duration']}, {pose_index}, {stem}_META, {stem}_METAL, "
                f"{clsn}, {stem}_AXIS, {frame['width']}, {frame['height']}, "
                f"{stem}_P2_META, {stem}_P2_METAL }},")
            pose_index += 1
    lines += ["};", "", f"static const Anim anims[{len(roles)}] = {{"]
    start = 0
    for role in roles:
        count = len(role_frames[role["role"]])
        loop = role.get("loop_start")
        loop_value = 255 if loop is None else int(loop)
        lines.append(f"    {{ {role['action']}, {count}, {loop_value}, frames_all + {start} }},")
        start += count
    lines += ["};", "", "static const unsigned char cut_sprite_palette[16] = {"]
    lines.append("    " + ", ".join(f"0x{value:02X}" for value in palette) + ",")
    lines += ["};", ""]
    return "\n".join(lines)


def _q8(value: str | int | float) -> int:
    return int(Decimal(str(value)) * 256)


def _hitdef_value(ch, state_id: int, name: str, default: int) -> int:
    state = ch.states.get(state_id)
    if state is None:
        return default
    for controller in state.controllers:
        if controller.source_type != "hitdef":
            continue
        for param in controller.params:
            if param.name == name and param.const is not None:
                return int(param.const)
    return default


def _controller_value(ch, state_id: int, source_type: str,
                      name: str) -> int | float | None:
    state = ch.states.get(state_id)
    if state is None:
        return None
    for controller in state.controllers:
        if controller.source_type != source_type:
            continue
        for param in controller.params:
            if param.name == name and param.const is not None:
                return param.const
    return None


def generate(source_path: Path, config_path: Path, out_dir: Path,
             first_bank: int = 2,
             project_json: Path | None = None) -> dict:
    ch = character_loader.load(Source(source_path))
    fidelity = classify_character(ch, SmsLimits())
    config = json.loads(config_path.read_text(encoding="utf-8"))
    roles = config["actions"]
    selected: dict[int, object] = {}
    for role in roles:
        action_id = int(role["action"])
        action = ch.anims.get(action_id)
        if action is None:
            raise ValueError(f"{role['role']}: AIR action {action_id} is missing")
        loop_start = role.get("loop_start")
        if loop_start is not None and not 0 <= int(loop_start) < len(action.frames):
            raise ValueError(f"{role['role']}: loop_start {loop_start} is outside the AIR action")
        for frame_index, frame in enumerate(action.frames):
            element = fidelity.by_id.get(f"anim:{action_id}.{frame_index}")
            if element is None or element.classe not in ("direct", "approximate"):
                kind = element.classe if element else "unclassified"
                raise ValueError(f"{role['role']}: anim:{action_id}.{frame_index} is {kind}")
            if frame.blend:
                raise ValueError(f"{role['role']}: anim:{action_id}.{frame_index} uses unsupported blend")
        selected[action_id] = action

    scale_profile = config.get("fighter_scale")
    scale_report = None
    uniformly_scaled = False
    source_sizes = {(sprite.group, sprite.image): [sprite.width, sprite.height]
                    for sprite in ch.sprites}
    if scale_profile is not None:
        idle_roles = [role for role in roles if role.get("role") == "idle"]
        if len(idle_roles) != 1:
            raise ValueError("uniform fighter scale requires exactly one idle role")
        target_px = int(scale_profile.get("target_idle_opaque_height_px", 80))
        accepted = scale_profile.get("accepted_height_px", [72, 88])
        if (not isinstance(accepted, list) or len(accepted) != 2 or
                not all(isinstance(v, int) and not isinstance(v, bool) for v in accepted)):
            raise ValueError("fighter_scale.accepted_height_px must be [min,max]")
        idle_action_id = int(idle_roles[0]["action"])
        before_bounds, before_frames = scale.measure_idle_opaque_bounds(ch, ch.anims[idle_action_id])
        input_height = before_bounds[3] - before_bounds[2] + 1
        numerator, denominator = scale.target_ratio(input_height, target_px,
                                                    (accepted[0], accepted[1]))
        selected_ids = set(selected)
        original_durations = {aid: [frame.time for frame in ch.anims[aid].frames]
                              for aid in selected_ids}
        original_counts = {aid: [len(frame.clsn1) + len(frame.clsn2)
                                 for frame in ch.anims[aid].frames]
                           for aid in selected_ids}
        ch = scale.scale_character(ch, selected_ids, numerator, denominator)
        selected = {aid: ch.anims[aid] for aid in selected_ids}
        by_key = {(sprite.group, sprite.image): sprite for sprite in ch.sprites}
        after_bounds, after_frames = scale.measure_idle_opaque_bounds(ch, ch.anims[idle_action_id])
        output_height = after_bounds[3] - after_bounds[2] + 1
        if not accepted[0] <= output_height <= accepted[1]:
            raise ValueError(f"uniform scale produced idle height {output_height}px outside "
                             f"{accepted[0]}..{accepted[1]}px")
        durations_preserved = all(
            [frame.time for frame in ch.anims[aid].frames] == original_durations[aid]
            for aid in selected_ids)
        boxes_preserved = all(
            [len(frame.clsn1) + len(frame.clsn2) for frame in ch.anims[aid].frames]
            == original_counts[aid] for aid in selected_ids)
        scale_report = {
            "policy": "uniform_per_character_scene_contract",
            "ratio": {"numerator": numerator, "denominator": denominator},
            "target_idle_opaque_height_px": target_px,
            "accepted_height_px": accepted,
            "source_idle_opaque_bounds_xyxy": before_bounds,
            "source_idle_opaque_height_px": input_height,
            "runtime_idle_opaque_bounds_xyxy": after_bounds,
            "runtime_idle_opaque_height_px": output_height,
            "idle_frame_bounds_source": before_frames,
            "idle_frame_bounds_runtime": after_frames,
            "selected_action_frame_counts_preserved": all(
                len(ch.anims[aid].frames) == len(original_durations[aid])
                for aid in selected_ids),
            "selected_action_air_durations_preserved": durations_preserved,
            "selected_action_clsn_box_counts_preserved": boxes_preserved,
            "sampling": "nearest_neighbor_indexed_pixels",
            "source_sizes_by_group_image": {
                f"{group}:{image}": size for (group, image), size in source_sizes.items()},
            "runtime_note": "AIR values are preserved in generated tables; runtime timing still "
                            "depends on pose streaming and requires emulator measurement."
        }
        if not durations_preserved or not boxes_preserved:
            raise ValueError("uniform scaling changed animation timing or CLSN box counts")
        uniformly_scaled = True

    palette_by_name = {name.lower(): colors for name, colors in ch.palettes}
    p1_name = config["palette_p1"].lower()
    p2_name = config["palette_p2"].lower()
    if p1_name not in palette_by_name or p2_name not in palette_by_name:
        raise ValueError(f"ACT palette missing: requested {p1_name}/{p2_name}; available={list(palette_by_name)}")
    p1_ch = _selected_variant(ch, selected, palette_by_name[p1_name])
    p2_ch = _selected_variant(ch, selected, palette_by_name[p2_name])
    by_key = {(sprite.group, sprite.image): sprite for sprite in ch.sprites}

    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="scene_cut_", dir=out_dir) as tmp:
        p1_manifest = smsdev.generate(p1_ch, fidelity, Path(tmp) / "p1",
                                      pre_scaled=uniformly_scaled,
                                      omit_blank_sprites=uniformly_scaled)
        p2_manifest = smsdev.generate(p2_ch, fidelity, Path(tmp) / "p2",
                                      pre_scaled=uniformly_scaled,
                                      omit_blank_sprites=uniformly_scaled)
        p1_artifacts = _artifacts(p1_manifest)
        p2_artifacts = _artifacts(p2_manifest)
        _correct_frame_metadata(p1_artifacts, p1_ch, selected, by_key,
                                uniformly_scaled=uniformly_scaled)
        _correct_frame_metadata(p2_artifacts, p2_ch, selected, by_key,
                                uniformly_scaled=uniformly_scaled)
        p1_by_symbol = {a.symbol: a for a in p1_artifacts}
        p2_by_symbol = {a.symbol: a for a in p2_artifacts}
        slug = smsdev.slug(Path(ch.def_path).stem)
        required = [f"{slug}_A{role['action']}F{i}_TILES"
                    for role in roles for i in range(len(selected[int(role['action'])].frames))]
        if len(set(required)) != len(required):
            raise ValueError("action roles reuse a source action; runtime pose identity would be ambiguous")
        for symbol in required:
            if symbol not in p1_by_symbol or symbol not in p2_by_symbol:
                raise ValueError(f"asset generation omitted required tiles: {symbol}")

        # Histogram colors only where generated pixels use them.  Each side has
        # seven stable indices; the P2 tiles are shifted into CRAM entries 9-15.
        p1_codebook = _palette_codebook([p1_by_symbol[s] for s in required], p1_by_symbol)
        p2_codebook = _palette_codebook([p2_by_symbol[s] for s in required], p2_by_symbol)
        if not p1_codebook or not p2_codebook:
            raise ValueError("selected art rendered fully transparent")

        palette_words = [0] * 16
        for index, word in enumerate(p1_codebook, 1):
            palette_words[index] = word
        for index, word in enumerate(p2_codebook, 9):
            palette_words[index] = word

        final: list[smsdev.Artifact] = []
        for symbol in required:
            stem = symbol[:-6]
            p1_tiles = p1_by_symbol[symbol]
            p2_tiles = p2_by_symbol[symbol]
            p1_pal = p1_by_symbol[stem + "_PAL"].data
            p2_pal = p2_by_symbol[stem + "_PAL"].data
            final.append(smsdev.Artifact(symbol, _remap_blob(p1_tiles.data, p1_pal, p1_codebook, 0), "sff+act"))
            final.append(smsdev.Artifact(symbol[:-6] + "_P2_TILES",
                                         _remap_blob(p2_tiles.data, p2_pal, p2_codebook, 8), "sff+act"))
            for suffix in ("_META", "_METAL", "_AXIS", "_CLSN"):
                if suffix == "_META":
                    final.extend(_palette_metas(stem, p1_by_symbol, p2_by_symbol))
                    continue
                if suffix == "_METAL":
                    continue
                artifact = p1_by_symbol.get(stem + suffix)
                palette2_artifact = p2_by_symbol.get(stem + suffix)
                if suffix in ("_AXIS", "_CLSN"):
                    if artifact and palette2_artifact and artifact.data != palette2_artifact.data:
                        raise ValueError(f"palette variants changed geometry/collision metadata: {stem + suffix}")
                    if artifact:
                        final.append(copy.copy(artifact))
        # Export the small runtime input contract under stable names. The C
        # core never depends on a character's DEF/command symbol prefix; the
        # selected character cut maps these aliases to that DEF's command
        # names. This lets a different character's cut link unchanged C.
        commands = config.get("commands", {})
        command_symbols = {a.symbol: a for a in p1_artifacts
                           if a.source == "cmd"}
        slug_upper = slug.upper() + "_CMD_"
        for alias, requested_name in commands.items():
            wanted = slug_upper + re.sub(r"[^0-9a-zA-Z]+", "_",
                                         requested_name).upper()
            matches = [a for symbol, a in command_symbols.items()
                       if symbol == wanted]
            if len(matches) != 1:
                raise ValueError(f"command alias {alias}: expected one {wanted}, "
                                 f"found {len(matches)}")
            final.append(smsdev.Artifact("CUT_CMD_" + alias.upper(),
                                         matches[0].data,
                                         "cmd"))

        # Pack each complete pose within one mapper page.  No pose crosses a
        # bank boundary because stream.c maps one 16 KB page per upload.
        pages: list[bytearray] = []
        bank_map: dict[str, tuple[int, int]] = {}
        for artifact in final:
            if not artifact.symbol.endswith("_TILES"):
                continue
            if len(artifact.data) > BANK_PAGE:
                raise ValueError(f"single pose exceeds a mapper page: {artifact.symbol}")
            if not pages or len(pages[-1]) + len(artifact.data) > BANK_PAGE:
                pages.append(bytearray())
            page_index = len(pages) - 1
            bank_map[artifact.symbol] = (first_bank + page_index, len(pages[-1]))
            pages[-1].extend(artifact.data)

    for index, page in enumerate(pages):
        path = out_dir / f"ken_scene_bank{first_bank + index}.bin"
        path.write_bytes(bytes(page).ljust(BANK_PAGE, b"\0"))

        header = smsdev.render_header(final, "ken_scene_runtime", bank_map)
        guard_end = "#endif /* ken_scene_runtime_H */\n"
        if not header.endswith(guard_end):
            raise ValueError("unexpected generated header guard")
        header = header[:-len(guard_end)]
        pose_frames: dict[str, list[dict]] = {}
        source_frames = {}
        for role in roles:
            aid = int(role["action"])
            action = selected[aid]
            pose_frames[role["role"]] = []
            for i, frame in enumerate(action.frames):
                sprite = by_key[(frame.group, frame.image)]
                divisor = (1 if uniformly_scaled else
                           (scale.SCALE if scale.needs_scale(sprite.width, sprite.height) else 1))
                width = max(1, sprite.width // divisor)
                height = max(1, sprite.height // divisor)
                symbol_stem = f"{slug}_A{aid}F{i}"
                tile_symbol = symbol_stem + "_TILES"
                p2_symbol = symbol_stem + "_P2_TILES"
                stream_ticks = (max(len(p1_by_symbol[tile_symbol].data),
                                    len(p2_by_symbol[tile_symbol].data)) +
                                STREAM_CHUNK_BYTES - 1) // STREAM_CHUNK_BYTES
                duration = (255 if frame.time < 0 else
                            max(1, min(254, frame.time),
                                1 if uniformly_scaled else stream_ticks))
                pose_frames[role["role"]].append({"stem": symbol_stem, "duration": duration,
                                                    "raw_duration": frame.time,
                                                    "stream_ticks": stream_ticks,
                                                    "width": width, "height": height})
                source_frames[f"anim:{aid}.{i}"] = {
                    "class": fidelity.by_id[f"anim:{aid}.{i}"].classe,
                    "size_source": source_sizes[(frame.group, frame.image)],
                    "size_after_pre_scale": [sprite.width, sprite.height],
                    "size_runtime": [width, height],
                    "scale": (scale_report["ratio"] if scale_report else divisor),
                    "uniform_scale_ratio": (scale_report["ratio"]
                                             if scale_report else None),
                    "duration_air": frame.time,
                    "duration_runtime": duration,
                    "stream_ticks": stream_ticks,
                    "clsn1": len(frame.clsn1), "clsn2": len(frame.clsn2),
                }
        velocity = ch.constants.get("velocity", {})
        movement = ch.constants.get("movement", {})
        data = ch.constants.get("data", {})
        jump_parts = [part.strip() for part in velocity.get("jump.neu", "0,-8").split(",")]
        if len(jump_parts) < 2:
            raise ValueError("velocity.jump.neu must contain x,y")
        punch_role = next(role for role in roles if role["role"] == "punch")
        kick_role = next(role for role in roles if role["role"] == "kick")
        special_role = next(role for role in roles if role["role"] == "special")
        punch_state = int(punch_role.get("state", punch_role["action"]))
        kick_state = int(kick_role.get("state", kick_role["action"]))
        special_state = int(special_role.get("state", special_role["action"]))
        special_speed = special_role.get("velocity_fwd")
        if special_speed is None:
            special_speed = _controller_value(ch, special_state, "velset", "x[0]")
        if special_speed is None or Decimal(str(special_speed)) == 0:
            special_vel_q8 = abs(_q8(velocity.get("walk.fwd", "2")))
        else:
            special_vel_q8 = abs(_q8(special_speed))
        runtime = {
            "life": int(data.get("life", "1000")),
            "walk_fwd": _q8(velocity.get("walk.fwd", "2")),
            "walk_back": _q8(velocity.get("walk.back", "-1.5")),
            "jump_vy": -_q8(jump_parts[1]),
            "gravity": _q8(movement.get("yaccel", "0.5")),
            "damage_punch": _hitdef_value(ch, punch_state, "damage[0]", 5),
            "damage_kick": _hitdef_value(ch, kick_state, "damage[0]", 8),
            "damage_special": _hitdef_value(ch, special_state, "damage[0]",
                                               _hitdef_value(ch, kick_state,
                                                             "damage[0]", 8) * 3),
            "special_vel": special_vel_q8,
            "hitstop": _hitdef_value(ch, punch_state, "pausetime[0]", 8),
            "hit_push": abs(_hitdef_value(ch, punch_state, "ground.velocity[0]", -3)),
            "guard_push": abs(_hitdef_value(ch, punch_state, "guard.velocity[0]", -5)),
        }
        header += _runtime_table(roles, pose_frames, len(required), final, bank_map,
                                 palette_words, runtime)
        header += guard_end
        (out_dir / "ken_scene_runtime.h").write_text(header, encoding="ascii")

    generated = {"source_sha256": ch.source_sha256,
                 "source_def": ch.def_path,
                 "palette_p1_act": p1_name, "palette_p2_act": p2_name,
                 "palette_p1_words": p1_codebook, "palette_p2_words": p2_codebook,
                 "palette_index_shift_p2": 8,
                 "runtime_constants": runtime,
                 "roles": [{"role": role["role"], "action": int(role["action"]),
                            "loop_start": role.get("loop_start"),
                            "frame_count": len(pose_frames[role["role"]])}
                           for role in roles],
                 "commands": commands,
                 "frames": source_frames,
                 "pose_count_per_fighter": len(required),
                 "stream_chunk_bytes": STREAM_CHUNK_BYTES,
                 "duration_policy": ("air_exact_candidate_stream_timing_unproven"
                                     if uniformly_scaled else "air_duration_extended_to_stream_ticks"),
                 "fighter_scale": scale_report,
                 "bank_page_bytes": BANK_PAGE,
                 "banks": [],
                 "asset_sha256": {}}
    for bank in range(first_bank, first_bank + len(pages)):
        path = out_dir / f"ken_scene_bank{bank}.bin"
        generated["banks"].append({"bank": bank, "file": path.name,
                                    "used_bytes": len(pages[bank - first_bank]),
                                    "file_bytes": path.stat().st_size,
                                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    header_path = out_dir / "ken_scene_runtime.h"
    generated["asset_sha256"][header_path.name] = hashlib.sha256(header_path.read_bytes()).hexdigest()
    manifest_path = out_dir / "ken_scene_manifest.json"
    manifest_path.write_text(json.dumps(generated, ensure_ascii=False, indent=2), encoding="utf-8")
    active_bank_files = {entry["file"] for entry in generated["banks"]}
    for stale in out_dir.glob("ken_scene_bank*.bin"):
        if stale.name not in active_bank_files:
            stale.unlink()
    if project_json is not None:
        project = json.loads(project_json.read_text(encoding="utf-8"))
        extra = project["toolchain"].get("makesms_extra", [])
        kept = []
        i = 0
        while i < len(extra):
            value = extra[i]
            if value == "-mbank" and i + 1 < len(extra):
                bank_spec = extra[i + 1]
                if Path(bank_spec.split(":", 1)[0]).name.startswith("ken_scene_bank"):
                    i += 2
                    continue
                kept.extend((value, bank_spec))
                i += 2
            else:
                kept.append(value)
                i += 1
        for entry in generated["banks"]:
            kept.extend(("-mbank", f"out/local_study/generated/scene_cut/{entry['file']}:0:1:{entry['bank']}"))
        project["toolchain"]["makesms_extra"] = kept
        project_json.write_text(json.dumps(project, ensure_ascii=False, indent=2) + "\n",
                                encoding="utf-8")
    print(f"[OK] {len(required)} poses/fighter, {len(pages)} banks, "
          f"palette slots P1=1-7 P2=9-15; source={ch.source_sha256}")
    return generated


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="local-only MUGEN archive or directory")
    parser.add_argument("--config", type=Path, required=True, help="action and palette cut JSON")
    parser.add_argument("--out", type=Path, required=True, help="ignored local output directory")
    parser.add_argument("--first-bank", type=int, default=2)
    parser.add_argument("--project-json", type=Path,
                        help="atualiza makesms_extra para mapear exatamente os bancos gerados")
    args = parser.parse_args(argv)
    generate(args.source, args.config, args.out, args.first_bank,
             args.project_json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
