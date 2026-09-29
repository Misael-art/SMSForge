#!/usr/bin/env python3
"""audit_render_glitch.py -- framebuffer video vs the legal images (L091).

The project renders every image the ROM may legally show (e.g. every pose
pair of the scene) as PNGs in --expected-dir, from the same patterns and
positions the ROM uses. Each captured framebuffer frame is compared with
the best-matching legal image on its lit mask (pixels brighter than the
stage). Modes:

  strict   zero flicker: every frame must equal a legal image
           (no expected pixel dark, no unexpected pixel lit).
  flicker  multiplexed sprites allowed: no unexpected lit pixel in any frame
           (residual/corrupt tile, wrong slot), and within every run of
           --window consecutive frames matched to the same legal image the
           union of lit pixels must cover it (nothing omitted for good).

A mismatch within --edge-tolerance px of an edge is ignored (h264 chroma
bleed), so a glitch narrower than that is not detected. The video must be
newer than the ROM; ROM and video SHA-256 are bound into the JSON verdict.
Static simulators (audit_sprite_line_sim.py) do not prove the rendered image.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

LUMA_ON = 24


def grow(mask: np.ndarray, radius: int) -> np.ndarray:
    out = mask.copy()
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            out |= np.roll(np.roll(mask, dy, 0), dx, 1)
    return out


def best_match(lit: np.ndarray, legal: dict, tol: int, mode: str = "strict") -> dict:
    """strict: minimise missing+extra. flicker: a frame shows a subset of a
    legal image, so minimise extra first (a smaller wrong pose would
    otherwise win on 'missing' and turn correct pixels into 'extra')."""
    grown_lit = grow(lit, tol)
    best = None
    for name, exp in legal.items():
        missing = int((exp & ~grown_lit).sum())
        extra = int((lit & ~grow(exp, tol)).sum())
        key = (missing + extra,) if mode == "strict" else (extra, missing)
        if best is None or key < best["key"]:
            best = {"image": name, "missing": missing, "extra": extra, "key": key}
    best.pop("key")
    return best


def judge(frames: list[np.ndarray], legal: dict, mode: str, window: int, tol: int) -> dict:
    per = [best_match(f, legal, tol, mode) | {"index": i} for i, f in enumerate(frames)]
    failures = []
    if mode == "strict":
        failures = [p for p in per if p["missing"] or p["extra"]]
    else:
        failures = [p | {"why": "extra"} for p in per if p["extra"]]
        # Coverage over runs of frames matched to the same legal image.
        run_start = 0
        for i in range(1, len(per) + 1):
            if i == len(per) or per[i]["image"] != per[run_start]["image"]:
                name = per[run_start]["image"]
                for s in range(run_start, i - window + 1):
                    union = np.zeros_like(frames[0])
                    for f in frames[s:s + window]:
                        union |= f
                    if (legal[name] & ~grow(union, tol)).any():
                        failures.append({"index": s, "image": name, "why": "omitted_in_window"})
                        break
                run_start = i
    return {"frames_judged": len(frames), "frames_failed": len(failures),
            "first_failures": failures[:10],
            "max_missing": max((p["missing"] for p in per), default=0),
            "max_extra": max((p["extra"] for p in per), default=0),
            "images_seen": sorted({p["image"] for p in per})}


def load_legal(directory: Path) -> dict:
    from PIL import Image
    legal = {}
    for png in sorted(directory.glob("*.png")):
        img = np.asarray(Image.open(png).convert("L"))
        if img.shape != (192, 256):
            raise ValueError(f"{png}: imagem legal fora da canvas 256x192")
        legal[png.stem] = img > LUMA_ON
    if not legal:
        raise ValueError("nenhuma imagem legal em --expected-dir")
    return legal


def video_frames(video: Path) -> list[np.ndarray]:
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", str(video), "-f", "rawvideo",
                          "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
    arr = np.frombuffer(raw, np.uint8)
    if arr.size % (192 * 256) or not arr.size:
        raise ValueError("video fora da canvas do VDP 256x192 ou vazio")
    return [f > LUMA_ON for f in arr.reshape(-1, 192, 256)]


SUSTAINED = 4


def sustained_start(frames: list[np.ndarray]) -> int:
    for i in range(len(frames)):
        if all(f.any() for f in frames[i:i + SUSTAINED]) and len(frames[i:i + SUSTAINED]) == SUSTAINED:
            return i
    return len(frames)


def is_fresh(video: Path, rom: Path) -> bool:
    return video.stat().st_mtime > rom.stat().st_mtime


def self_check() -> int:
    a = np.zeros((192, 256), bool)
    a[40:56, 30:46] = True
    b = np.zeros((192, 256), bool)
    b[40:56, 120:128] = True
    legal = {"pair": a | b, "alone": a.copy()}
    ok = judge([a | b] * 4, legal, "strict", 2, 1)
    assert ok["frames_failed"] == 0
    omitted = (a | b).copy()
    omitted[40:56, 30:38] = False                       # one 8x16 sprite gone
    assert judge([omitted], {"pair": a | b}, "strict", 2, 1)["frames_failed"] == 1
    residue = (a | b).copy()
    residue[100:108, 200:208] = True                    # stray 8x8 tile
    assert judge([residue], legal, "flicker", 2, 1)["frames_failed"] == 1
    half1, half2 = (a | b).copy(), (a | b).copy()
    half1[40:56, 30:38] = False
    half2[40:56, 38:46] = False
    assert judge([half1, half2] * 3, {"pair": a | b}, "flicker", 2, 1)["frames_failed"] == 0
    assert judge([half1] * 6, {"pair": a | b}, "flicker", 2, 1)["frames_failed"] == 1
    # Flicker subset of the big pose must not be matched to a smaller pose.
    assert judge([half1, half2] * 3, legal, "flicker", 2, 1)["frames_failed"] == 0
    # Mixed poses (pixels from two legal images at once) still fail.
    c = np.zeros((192, 256), bool)
    c[100:116, 60:68] = True
    mixed = {"p": a, "q": c}
    assert judge([a | c], mixed, "flicker", 2, 1)["frames_failed"] == 1
    blank = np.zeros((192, 256), bool)
    flash = blank.copy()
    flash[135, 40] = True
    seq = [blank, flash, blank, blank, a | b, a | b, a | b, a | b]
    assert sustained_start(seq) == 4                     # flash is before content
    with tempfile.TemporaryDirectory() as d:
        v, r = Path(d, "v.mp4"), Path(d, "r.sms")
        v.write_bytes(b"v")
        r.write_bytes(b"r")
        os.utime(v, (1, 1))
        assert not is_fresh(v, r)
        os.utime(v, (4e9, 4e9))
        assert is_fresh(v, r)
    print("[SELF-CHECK OK] audit_render_glitch (strict exato, omissao, residuo, "
          "flicker com cobertura, subconjunto sem vies, pose mista, omissao permanente, captura stale)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--video", type=Path)
    ap.add_argument("--rom", type=Path)
    ap.add_argument("--expected-dir", type=Path, help="PNGs 256x192 das imagens legais")
    ap.add_argument("--mode", choices=("strict", "flicker"), default="strict")
    ap.add_argument("--window", type=int, default=8, help="quadros para cobertura no modo flicker")
    ap.add_argument("--edge-tolerance", type=int, default=1)
    ap.add_argument("--skip", type=int, default=0,
                    help="quadros extras a ignorar apos o primeiro com conteudo")
    ap.add_argument("-o", "--out", type=Path)
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        return self_check()
    if not (a.video and a.rom and a.expected_dir and a.out):
        ap.error("--video, --rom, --expected-dir e --out sao obrigatorios")
    legal = load_legal(a.expected_dir)
    frames = video_frames(a.video)
    # Judging starts at the first sustained content (>= SUSTAINED frames in
    # a row). Anything lit before it is not judged but is REPORTED
    # (pre_content_lit_pixels): a pre-main/power-on flash stays visible in
    # the evidence instead of being silently dropped.
    lead = sustained_start(frames)
    pre_lit = int(sum(int(f.sum()) for f in frames[:lead]))
    frames = frames[lead + a.skip:]
    result = judge(frames, legal, a.mode, a.window, a.edge_tolerance)
    fresh = is_fresh(a.video, a.rom)
    result.update({
        "schema": "render_glitch_v1", "mode": a.mode, "window": a.window,
        "edge_tolerance_px": a.edge_tolerance,
        "rom": str(a.rom), "rom_sha256": hashlib.sha256(a.rom.read_bytes()).hexdigest(),
        "video": str(a.video), "video_sha256": hashlib.sha256(a.video.read_bytes()).hexdigest(),
        "video_newer_than_rom": fresh, "legal_images": len(legal),
        "lead_in_frames_dropped": lead, "pre_content_lit_pixels": pre_lit,
        "extra_skip": a.skip,
        "verdict": "PASS" if fresh and result["frames_judged"] and not result["frames_failed"] else "FAIL",
    })
    a.out.write_text(json.dumps(result, indent=1))
    print(f"[{result['verdict']}] render glitch {a.mode}: {result['frames_failed']}/"
          f"{result['frames_judged']} quadros reprovados, extra max {result['max_extra']}, "
          f"video mais novo que a ROM={fresh}, pixels acesos antes do conteudo={pre_lit}")
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
