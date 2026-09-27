"""Generate a two-character package for the SMS versus runtime.

Individual cuts still come from scene_cut. This module assigns distinct
mapper pages and joins their runtime tables without carrying either source
archive into the repository.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scene_cut  # noqa: E402

MAKESMS_MAX_MERGES = 8  # devkitSMS makesms/src/makesms.c: MAX_MERGES

_BYTE_ARRAY = re.compile(
    r"^(?P<decl>(?:static\s+)?const\s+unsigned\s+char\s+"
    r"(?P<symbol>[A-Za-z_]\w*)\s*\[\s*(?P<size>\d+)\s*\]\s*"
    r"=\s*\{(?P<body>.*?)\};)",
    re.M | re.S,
)
_BYTE_VALUE = re.compile(r"0x[0-9A-Fa-f]+|\b\d+\b")


def _deduplicate_metasprite_arrays(header: str) -> tuple[str, dict]:
    """Alias only byte-identical META/METAL arrays; keep every pose mapping."""
    canonical_by_bytes: dict[bytes, str] = {}
    aliases: dict[str, str] = {}

    def replace(match: re.Match[str]) -> str:
        symbol = match.group("symbol")
        if not symbol.endswith(("_META", "_METAL")):
            return match.group("decl")
        body = match.group("body")
        values = _BYTE_VALUE.findall(body)
        residue = _BYTE_VALUE.sub("", body)
        if residue.strip(" ,\t\r\n"):
            raise ValueError(f"malformed byte array while deduplicating {symbol}")
        size = int(match.group("size"))
        if len(values) != size:
            raise ValueError(f"{symbol} declares {size} bytes but contains {len(values)}")
        numbers = [int(value, 0) for value in values]
        if any(value > 0xFF for value in numbers):
            raise ValueError(f"{symbol} contains a value outside unsigned char")
        payload = bytes(numbers)
        canonical = canonical_by_bytes.get(payload)
        if canonical is None:
            canonical_by_bytes[payload] = symbol
            return match.group("decl")
        aliases[symbol] = canonical
        return f"#define {symbol} {canonical}"

    output = _BYTE_ARRAY.sub(replace, header)
    size_macros = {name: int(value) for name, value in re.findall(
        r"^#define\s+(\w+_SIZE)\s+(\d+)\s*$", output, re.M)}
    bytes_saved = 0
    for symbol, canonical in aliases.items():
        size = size_macros.get(symbol + "_SIZE")
        canonical_size = size_macros.get(canonical + "_SIZE")
        if size is None or size != canonical_size:
            raise ValueError(f"alias size mismatch: {symbol} -> {canonical}")
        bytes_saved += size
    return output, {"alias_count": len(aliases), "bytes_saved": bytes_saved,
                    "aliases": aliases}


def _metadata_dedup_summary(header: str) -> dict:
    aliases = {name: target for name, target in re.findall(
        r"^#define\s+([A-Za-z_]\w*_META(?:L)?)\s+([A-Za-z_]\w*_META(?:L)?)\s*$",
        header, re.M)}
    sizes = {name: int(value) for name, value in re.findall(
        r"^#define\s+(\w+_SIZE)\s+(\d+)\s*$", header, re.M)}
    return {"alias_count": len(aliases),
            "bytes_saved": sum(sizes[name + "_SIZE"] for name in aliases),
            "aliases": aliases,
            "scope": "exact byte-identical META/METAL arrays only"}


def _pose_rows(text: str) -> tuple[list[str], re.Match[str]]:
    pattern = re.compile(
        r"static const PoseRef\s+poses_all\s*\[[^]]+\]\s*=\s*\{(.*?)\n\};",
        re.S,
    )
    match = pattern.search(text)
    if not match:
        raise ValueError("generated header has no poses_all table")
    rows = [line.strip().rstrip(",") for line in match.group(1).splitlines()
            if line.strip()]
    if not rows or any(not row.startswith("{") or not row.endswith("}")
                       for row in rows):
        raise ValueError("malformed PoseRef table")
    return rows, match


def _palette(text: str) -> list[int]:
    match = re.search(
        r"static const unsigned char\s+cut_sprite_palette\s*\[16\]\s*=\s*\{(.*?)\};",
        text,
        re.S,
    )
    if not match:
        raise ValueError("generated header has no 16-entry sprite palette")
    values = [int(token, 0) for token in
              re.findall(r"0x[0-9A-Fa-f]+|\b\d+\b", match.group(1))]
    if len(values) != 16 or any(value > 0x3F for value in values):
        raise ValueError("malformed sprite palette")
    return values


def _prefix_header(text: str, prefix: str) -> tuple[str, list[str]]:
    rows, match = _pose_rows(text)
    text = text[:match.start()] + text[match.end():]
    text = re.sub(r"\bCUT_", prefix.upper() + "_CUT_", text)
    text = re.sub(r"\bframes_all\b", prefix + "_frames_all", text)
    text = re.sub(r"\banims\b", prefix + "_anims", text)
    text = re.sub(r"\bcut_sprite_palette\b", prefix + "_cut_sprite_palette", text)
    guard = prefix.upper() + "_SCENE_RUNTIME_H"
    text = text.replace("ken_scene_runtime_H", guard)
    text = re.sub(r"\A#ifndef\s+" + guard + r"\s+#define\s+" + guard +
                  r"\s+", "", text, count=1)
    text = re.sub(r"\n#endif\s*/\*\s*" + guard + r"\s*\*/\s*$", "\n", text)
    if "#ifndef " + guard in text or "#endif /* " + guard + " */" in text:
        raise ValueError("could not remove the generated header guard")
    return text, rows


def merge_headers(p1_text: str, p2_text: str,
                  p1_poses: int, p2_poses: int) -> str:
    p1_rows, _ = _pose_rows(p1_text)
    p2_rows, _ = _pose_rows(p2_text)
    if len(p1_rows) != p1_poses * 2 or len(p2_rows) != p2_poses * 2:
        raise ValueError("PoseRef count disagrees with scene-cut manifest")
    p1_palette, p2_palette = _palette(p1_text), _palette(p2_text)
    p1_text, _ = _prefix_header(p1_text, "ken")
    p2_text, _ = _prefix_header(p2_text, "ryu")

    palette = [0] * 16
    palette[1:8] = p1_palette[1:8]
    palette[9:16] = p2_palette[9:16]
    all_poses = p1_rows[:p1_poses] + p2_rows[p2_poses:]
    lines = [
        "#ifndef VERSUS_SCENE_RUNTIME_H",
        "#define VERSUS_SCENE_RUNTIME_H",
        "",
        p1_text,
        p2_text,
        f"#define VERSUS_POSE_COUNT {p1_poses + p2_poses}",
        "#define KEN_POSE_BASE 0",
        f"#define RYU_POSE_BASE {p1_poses}",
        "static const PoseRef versus_poses[VERSUS_POSE_COUNT] = {",
        *["    " + row + "," for row in all_poses],
        "};",
        "static const unsigned char versus_sprite_palette[16] = {",
        "    " + ", ".join(f"0x{value:02X}" for value in palette) + ",",
        "};",
        "#endif /* VERSUS_SCENE_RUNTIME_H */",
        "",
    ]
    merged, _dedup = _deduplicate_metasprite_arrays("\n".join(lines))
    return merged


def _pack_mapper_images(banks: list[dict], out_dir: Path) -> list[dict]:
    """Concatenate contiguous 16 KiB mapper pages to stay under makesms' cap."""
    ordered = sorted(banks, key=lambda item: item["bank"])
    groups: list[list[dict]] = []
    for item in ordered:
        if not groups or item["bank"] != groups[-1][-1]["bank"] + 1:
            groups.append([item])
        else:
            groups[-1].append(item)
    if len(groups) > MAKESMS_MAX_MERGES:
        raise ValueError(f"mapper layout needs {len(groups)} contiguous file merges; "
                         f"makesms supports at most {MAKESMS_MAX_MERGES}")
    images = []
    for group in groups:
        start, end = group[0]["bank"], group[-1]["bank"]
        path = out_dir / f"versus_scene_banks_{start:02d}.bin"
        payload = bytearray()
        for item in group:
            data = Path(item["path"]).read_bytes()
            if len(data) != 16384:
                raise ValueError(f"bank {item['bank']} has {len(data)} bytes; expected 16384")
            payload.extend(data)
        path.write_bytes(payload)
        images.append({"bank_start": start, "bank_count": end - start + 1,
                       "file": path.name, "path": str(path), "bytes": len(payload),
                       "sha256": hashlib.sha256(payload).hexdigest()})
    return images


def _update_project(project_json: Path, mapper_images: list[dict]) -> None:
    project = json.loads(project_json.read_text(encoding="utf-8"))
    extra = project["toolchain"].get("makesms_extra", [])
    kept: list[str] = []
    i = 0
    while i < len(extra):
        value = extra[i]
        if value == "-mbank" and i + 1 < len(extra):
            spec = extra[i + 1]
            name = Path(spec.split(":", 1)[0]).name
            if name.startswith(("ken_scene_bank", "ryu_scene_bank",
                                "versus_scene_banks_")):
                i += 2
                continue
            kept.extend((value, spec))
            i += 2
        else:
            kept.append(value)
            i += 1
    for item in mapper_images:
        bank_file = Path(item["path"]).resolve()
        project_root = project_json.parent.parent.resolve()
        rel = bank_file.relative_to(project_root).as_posix()
        kept.extend(("-mbank", f"{rel}:0:{item['bank_count']}:{item['bank_start']}"))
    if sum(1 for value in kept if value == "-mbank") > MAKESMS_MAX_MERGES:
        raise ValueError("project manifest exceeds the eight -mbank merge limit")
    project["toolchain"]["makesms_extra"] = kept
    project_json.write_text(json.dumps(project, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")


def generate(p1_source: Path, p1_config: Path, p2_source: Path,
             p2_config: Path, out_dir: Path, p1_first_bank: int = 2,
             p2_first_bank: int = 5, project_json: Path | None = None) -> dict:
    p1_dir, p2_dir = out_dir / "p1_ken", out_dir / "p2_ryu"
    p1 = scene_cut.generate(p1_source, p1_config, p1_dir,
                            first_bank=p1_first_bank)
    p2 = scene_cut.generate(p2_source, p2_config, p2_dir,
                            first_bank=p2_first_bank)
    p1_header = (p1_dir / "ken_scene_runtime.h").read_text(encoding="ascii")
    p2_header = (p2_dir / "ken_scene_runtime.h").read_text(encoding="ascii")
    merged = merge_headers(p1_header, p2_header,
                           int(p1["pose_count_per_fighter"]),
                           int(p2["pose_count_per_fighter"]))
    out_dir.mkdir(parents=True, exist_ok=True)
    header_path = out_dir / "versus_scene_runtime.h"
    header_path.write_text(merged, encoding="ascii")

    banks: list[dict] = []
    for role, manifest, source_dir in (("ken", p1, p1_dir), ("ryu", p2, p2_dir)):
        for bank in manifest["banks"]:
            source_path = source_dir / bank["file"]
            target_path = out_dir / f"{role}_scene_bank{bank['bank']}.bin"
            target_path.write_bytes(source_path.read_bytes())
            item = {**bank, "file": target_path.name, "path": str(target_path),
                    "sha256": hashlib.sha256(target_path.read_bytes()).hexdigest(),
                    "fighter": role}
            banks.append(item)
    bank_ids = [item["bank"] for item in banks]
    if len(set(bank_ids)) != len(bank_ids):
        raise ValueError("P1 and P2 mapper banks overlap")
    mapper_images = _pack_mapper_images(banks, out_dir)

    manifest = {
        "schema": "sms_versus_scene_cut_v1",
        "source_sha256": {"p1_ken": p1["source_sha256"],
                          "p2_ryu": p2["source_sha256"]},
        "source_def": {"p1_ken": p1["source_def"],
                       "p2_ryu": p2["source_def"]},
        "pose_count": {"p1_ken": p1["pose_count_per_fighter"],
                       "p2_ryu": p2["pose_count_per_fighter"]},
        "pose_base": {"p1_ken": 0,
                      "p2_ryu": p1["pose_count_per_fighter"]},
        "runtime_constants": {"p1_ken": p1["runtime_constants"],
                              "p2_ryu": p2["runtime_constants"]},
        "fighter_scale": {"p1_ken": p1.get("fighter_scale"),
                          "p2_ryu": p2.get("fighter_scale")},
        "duration_policy": {"p1_ken": p1.get("duration_policy"),
                            "p2_ryu": p2.get("duration_policy")},
        "banks": banks,
        "mapper_images": mapper_images,
        "header": str(header_path),
        "header_sha256": hashlib.sha256(header_path.read_bytes()).hexdigest(),
        "header_metadata_deduplication": _metadata_dedup_summary(merged),
        "palette_policy": "Ken P1 entries 1-7; Ryu P2 entries 9-15; index 0 transparent",
    }
    manifest_path = out_dir / "versus_scene_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")
    if project_json is not None:
        _update_project(project_json, mapper_images)
    return manifest


def _self_check() -> None:
    p1 = """#ifndef ken_scene_runtime_H
#define ken_scene_runtime_H
static const PoseRef poses_all[2] = {
    { A_BANK, A_OFF, A_SIZE },
    { A_P2_BANK, A_P2_OFF, A_P2_SIZE },
};
#define CUT_POSE_COUNT 1
static const Frame frames_all[1] = { { 1, 0, A_META, A_METAL, 0, A_AXIS, 8, 16 }, };
static const Anim anims[1] = { { 0, 1, 255, frames_all }, };
static const unsigned char cut_sprite_palette[16] = { 0,1,2,3,4,5,6,7,0,9,10,11,12,13,14,15 };
#endif /* ken_scene_runtime_H */
"""
    p2 = (p1.replace("A_P2_", "B_P2_").replace("A_BANK", "B_BANK").replace("A_OFF", "B_OFF")
          .replace("A_SIZE", "B_SIZE").replace("A_META", "B_META")
          .replace("A_METAL", "B_METAL").replace("A_AXIS", "B_AXIS"))
    merged = merge_headers(p1, p2, 1, 1)
    assert "#define KEN_CUT_POSE_COUNT 1" in merged
    assert "#define RYU_CUT_POSE_COUNT 1" in merged
    assert "{ A_BANK, A_OFF, A_SIZE }" in merged
    assert "{ B_P2_BANK, B_P2_OFF, B_P2_SIZE }" in merged
    assert "#define RYU_POSE_BASE 1" in merged

    meta = "#define A_META_SIZE 4\nconst unsigned char A_META[4] = {\n  0, 1, 2, 128,\n};"
    p1 = p1.replace("static const PoseRef", meta + "\nstatic const PoseRef", 1)
    p2 = p2.replace("static const PoseRef", meta.replace("A_META", "B_META") +
                    "\nstatic const PoseRef", 1)
    different = ("#define B_METAL_SIZE 4\n"
                 "const unsigned char B_METAL[4] = {\n  4, 5, 6, 128,\n};")
    p2 = p2.replace("static const PoseRef", different +
                    "\nstatic const PoseRef", 1)
    merged = merge_headers(p1, p2, 1, 1)
    assert "#define B_META A_META" in merged
    assert "const unsigned char B_META[4]" not in merged
    assert "const unsigned char B_METAL[4]" in merged

    with tempfile.TemporaryDirectory(prefix="versus_bank_pack_") as tmp:
        root = Path(tmp)
        banks = []
        for number in (2, 3, 5):
            path = root / f"bank{number}.bin"
            path.write_bytes(bytes((number,)) * 16384)
            banks.append({"bank": number, "path": str(path)})
        images = _pack_mapper_images(banks, root)
        assert [(item["bank_start"], item["bank_count"]) for item in images] == [
            (2, 2), (5, 1)]
        assert (root / images[0]["file"]).read_bytes() == (
            bytes((2,)) * 16384 + bytes((3,)) * 16384)
        assert len(images) <= MAKESMS_MAX_MERGES

        too_many = [{"bank": index * 2, "path": "unused"} for index in range(9)]
        try:
            _pack_mapper_images(too_many, root)
            raise AssertionError("more than eight non-contiguous map images accepted")
        except ValueError as exc:
            assert "makesms supports at most 8" in str(exc)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--p1-source", type=Path)
    parser.add_argument("--p1-config", type=Path)
    parser.add_argument("--p2-source", type=Path)
    parser.add_argument("--p2-config", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--p1-first-bank", type=int, default=2)
    parser.add_argument("--p2-first-bank", type=int, default=5)
    parser.add_argument("--project-json", type=Path)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args(argv)
    if args.self_check:
        _self_check()
        print("[PASS] versus scene cut self-check")
        return 0
    required = (args.p1_source, args.p1_config, args.p2_source,
                args.p2_config, args.out)
    if any(item is None for item in required):
        parser.error("--p1-source/config, --p2-source/config e --out são obrigatórios")
    result = generate(args.p1_source, args.p1_config, args.p2_source,
                      args.p2_config, args.out, args.p1_first_bank,
                      args.p2_first_bank, args.project_json)
    print(f"[OK] versus cut: {result['pose_count']} poses, "
          f"banks {[bank['bank'] for bank in result['banks']]}; "
          f"header={result['header']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
