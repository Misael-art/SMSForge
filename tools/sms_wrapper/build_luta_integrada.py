#!/usr/bin/env python3
"""Build the luta_mugen 72-88 integrated study.

Hand-written sources, headers and generators live in
SMS_projects/luta_mugen/integrada/ (tracked). Tile banks, the scene header
and the ROM stay in out/local_study/luta_integrada/ because they are derived
from restricted character data and are gitignored. This recipe copies the
tracked sources into that tree, regenerates pose metadata, builds via
build_inner.py, then checks RAM layout and the banks the runtime reads.

  python3 tools/sms_wrapper/build_luta_integrada.py [--check-only]
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANON = ROOT / "SMS_projects" / "luta_mugen" / "integrada"
STUDY = ROOT / "SMS_projects" / "luta_mugen" / "out" / "local_study" / "luta_integrada"
HAND_HEADERS = ("fight.h", "input.h", "luta.h", "stream.h")


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print("+", " ".join(cmd))
    r = subprocess.run(cmd, cwd=cwd)
    if r.returncode != 0:
        raise SystemExit(r.returncode)


def sync() -> None:
    if not (CANON / "src").is_dir():
        raise SystemExit(f"[FAIL] fontes canonicas ausentes: {CANON}")
    if not (STUDY / "inc" / "versus_scene_runtime_full_generated.h").is_file():
        raise SystemExit(f"[FAIL] header de cena ausente em {STUDY}/inc "
                         "(dado derivado local, nao versionado)")
    for src in sorted((CANON / "src").glob("*.c")):
        shutil.copy2(src, STUDY / "src" / src.name)
    for name in HAND_HEADERS:
        shutil.copy2(CANON / "inc" / name, STUDY / "inc" / name)
    tool_dst = STUDY / "tools"
    tool_dst.mkdir(parents=True, exist_ok=True)
    for src in sorted((CANON / "tools").glob("*.py")):
        shutil.copy2(src, tool_dst / src.name)
    shutil.copy2(CANON / ".mddev" / "project.json", STUDY / ".mddev" / "project.json")


def regenerate() -> None:
    py = sys.executable
    run([py, str(CANON / "tools" / "gen_pose_table.py"),
         "--header", str(STUDY / "inc" / "versus_scene_runtime_full_generated.h"),
         "--banks", str(STUDY / "assets" / "banks" / "versus_scene_banks_02.bin"),
         "--out", str(STUDY / "inc" / "pose_table.h"),
         "--bank-out", str(STUDY / "assets" / "banks" / "pose_meta_37.bin")])
    run([py, str(CANON / "tools" / "trim_scene_header.py"),
         "--header", str(STUDY / "inc" / "versus_scene_runtime_full_generated.h"),
         "--out", str(STUDY / "inc" / "scene_trimmed.h")])
    parts = [
        STUDY / "assets" / "banks" / "versus_scene_banks_02.bin",
        STUDY / "assets" / "banks" / "pose_meta_37.bin",
    ]
    out = STUDY / "assets" / "banks" / "banks_integrada.bin"
    out.write_bytes(b"".join(p.read_bytes() for p in parts))


def measure() -> None:
    py = sys.executable
    rom = STUDY / "out" / "rom" / "scale_pilot_80px.sms"
    mp = STUDY / "out" / "obj" / "scale_pilot_80px.map"
    sources = sorted((STUDY / "src").glob("*.c"))
    run([py, str(CANON / "tools" / "check_ram_layout.py"),
         "--map", str(mp), "--rom", str(rom),
         "--sources", *[str(s) for s in sources]])
    run([py, str(CANON / "tools" / "check_rom_binding.py"),
         "--rom", str(rom),
         "--image", str(STUDY / "assets" / "banks" / "banks_integrada.bin"),
         "--base-bank", "2",
         "--pose-header", str(STUDY / "inc" / "pose_table.h"),
         "--meta-blob", str(STUDY / "assets" / "banks" / "pose_meta_37.bin")])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check-only", action="store_true",
                    help="mede o mapa e a ROM ja gerados, sem recompilar")
    ap.add_argument("--self-check", action="store_true",
                    help="roda o self-check das duas medicoes usadas pela receita")
    args = ap.parse_args()
    py = sys.executable
    if args.self_check:
        run([py, str(CANON / "tools" / "check_ram_layout.py"), "--self-check"])
        run([py, str(CANON / "tools" / "check_rom_binding.py"), "--self-check"])
        print("[PASS] build_luta_integrada self-check")
        return 0
    sync()
    if args.check_only:
        measure()
        return 0
    regenerate()
    run([py, str(ROOT / "tools" / "sms_wrapper" / "build_inner.py"),
         "--project", str(STUDY)])
    measure()
    return 0


if __name__ == "__main__":
    main()
