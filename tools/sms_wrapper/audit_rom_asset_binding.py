#!/usr/bin/env python3
"""audit_rom_asset_binding.py — mapa source → res → símbolo → ROM SHA.

Boot no emulador não prova que a arte autoral está no binário. Este gate
exige um mapa machine-readable ligando cada asset crítico ao SHA da ROM.

Uso:
  audit_rom_asset_binding.py --project <dir> [--rom <path>] [--map <json>]
  audit_rom_asset_binding.py --self-check
Exit: 0 vinculado | 1 rom_asset_binding_unproven | 3 uso
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_map(project: str, explicit=None):
    candidates = []
    if explicit:
        candidates.append(explicit)
    candidates.extend([
        os.path.join(project, "doc", "rom_asset_binding.json"),
        os.path.join(project, "out", "logs", "rom_asset_binding.json"),
    ])
    for path in candidates:
        if path and os.path.isfile(path):
            try:
                data = json.load(open(path, encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                return None, path, [f"mapa ilegível ({exc})"]
            return data, path, []
    return None, None, []


def audit(project: str, rom_path=None, map_path=None, require=False):
    problems = []
    data, used, load_errs = load_map(project, map_path)
    problems += load_errs
    if data is None:
        if require:
            problems.append("rom_asset_binding_unproven: mapa ausente "
                            "(doc/rom_asset_binding.json)")
        return problems, {"present": False, "entries": 0}

    if data.get("schema") not in {"rom_asset_binding_v1", "rom_asset_binding_v1.schema.json"}:
        problems.append("rom_asset_binding_unproven: schema ausente ou desconhecido")

    declared_sha = (data.get("rom_sha256") or "").lower()
    rom = rom_path or data.get("rom_path")
    if rom and not os.path.isfile(rom):
        alt = rom if os.path.isabs(rom) else os.path.join(project, rom)
        if os.path.isfile(alt):
            rom = alt
        elif not os.path.isabs(rom):
            # ja veio prefixado com o project relativo ao cwd
            pass
    if not rom or not os.path.isfile(rom):
        problems.append("rom_asset_binding_unproven: ROM do mapa não encontrada")
        actual_sha = None
    else:
        actual_sha = sha256_file(rom)
        if not declared_sha:
            problems.append("rom_asset_binding_unproven: rom_sha256 ausente no mapa")
        elif actual_sha != declared_sha:
            problems.append(
                f"rom_asset_binding_unproven: SHA da ROM diverge "
                f"(mapa={declared_sha[:12]}… arquivo={actual_sha[:12]}…)"
            )
        size = data.get("rom_size_bytes")
        if size is not None and os.path.getsize(rom) != int(size):
            problems.append(
                f"rom_asset_binding_unproven: tamanho da ROM diverge "
                f"(mapa={size} arquivo={os.path.getsize(rom)})"
            )

    entries = data.get("entries") or []
    if not entries:
        problems.append("rom_asset_binding_unproven: mapa sem entradas")

    seen_symbols = set()
    for i, entry in enumerate(entries):
        label = entry.get("symbol") or entry.get("res_path") or f"entry[{i}]"
        res_rel = entry.get("res_path")
        if not res_rel:
            problems.append(f"{label}: res_path ausente")
            continue
        res_abs = res_rel if os.path.isabs(res_rel) else os.path.join(project, res_rel)
        if not os.path.isfile(res_abs):
            problems.append(f"{label}: res_path inexistente ({res_rel})")
            continue
        actual = sha256_file(res_abs)
        declared = (entry.get("sha256") or "").lower()
        if not declared:
            problems.append(f"{label}: sha256 do asset ausente")
        elif actual != declared:
            problems.append(
                f"{label}: sha256 do PNG diverge do mapa "
                f"(mapa={declared[:12]}… arquivo={actual[:12]}…)"
            )
        src = entry.get("source")
        if src:
            src_abs = src if os.path.isabs(src) else os.path.join(project, src)
            if not os.path.isfile(src_abs):
                problems.append(f"{label}: source inexistente ({src})")
        symbol = entry.get("symbol")
        if not symbol:
            problems.append(f"{label}: symbol ausente (vínculo res→código não provado)")
        elif symbol in seen_symbols:
            problems.append(f"{label}: symbol duplicado '{symbol}'")
        else:
            seen_symbols.add(symbol)
        generated = entry.get("generated")
        if generated:
            gen_abs = generated if os.path.isabs(generated) else os.path.join(project, generated)
            if not os.path.isfile(gen_abs):
                problems.append(f"{label}: generated inexistente ({generated})")

    report = {
        "present": True,
        "map_path": used,
        "rom_sha256": actual_sha,
        "declared_rom_sha256": declared_sha,
        "entries": len(entries),
        "ok": not problems,
    }
    return problems, report


def _write_png(path, w=8, h=8):
    from png_io import write_indexed_png
    pal = [(0, 0, 0), (255, 255, 255)] + [(0, 0, 0)] * 14
    pixels = [bytes([1] * w) for _ in range(h)]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_indexed_png(path, w, h, pal, pixels)


def _self_check() -> int:
    d = tempfile.mkdtemp(prefix="smsbind_")
    try:
        res = os.path.join(d, "res", "sprites", "hero.png")
        src = os.path.join(d, "rascunho", "hero.png")
        gen = os.path.join(d, "out", "assets", "hero_tiles.c")
        rom = os.path.join(d, "out", "rom", "game.sms")
        os.makedirs(os.path.join(d, "doc"), exist_ok=True)
        os.makedirs(os.path.dirname(gen), exist_ok=True)
        os.makedirs(os.path.dirname(rom), exist_ok=True)
        _write_png(res)
        _write_png(src)
        open(gen, "w").write("const unsigned char hero_tiles[] = {0};\n")
        open(rom, "wb").write(b"SMSROM" + b"\x00" * 64)
        good = {
            "schema": "rom_asset_binding_v1",
            "rom_path": "out/rom/game.sms",
            "rom_sha256": sha256_file(rom),
            "rom_size_bytes": os.path.getsize(rom),
            "entries": [{
                "source": "rascunho/hero.png",
                "res_path": "res/sprites/hero.png",
                "symbol": "hero_tiles",
                "generated": "out/assets/hero_tiles.c",
                "sha256": sha256_file(res),
            }],
        }
        json.dump(good, open(os.path.join(d, "doc", "rom_asset_binding.json"), "w"))
        p, _ = audit(d, require=True)
        assert not p, f"mapa válido não deveria reprovar: {p}"

        # SHA da ROM errado
        bad = dict(good)
        bad["rom_sha256"] = "0" * 64
        json.dump(bad, open(os.path.join(d, "doc", "rom_asset_binding.json"), "w"))
        p, _ = audit(d, require=True)
        assert any("SHA da ROM diverge" in x for x in p), f"faltou SHA ROM: {p}"

        # PNG divergente
        bad = dict(good)
        bad["entries"] = [dict(good["entries"][0], sha256="1" * 64)]
        json.dump(bad, open(os.path.join(d, "doc", "rom_asset_binding.json"), "w"))
        p, _ = audit(d, require=True)
        assert any("sha256 do PNG diverge" in x for x in p), f"faltou SHA PNG: {p}"

        # mapa ausente + require
        os.remove(os.path.join(d, "doc", "rom_asset_binding.json"))
        p, _ = audit(d, require=True)
        assert any("mapa ausente" in x for x in p), f"faltou mapa ausente: {p}"

        # sem require, ausência não é blocker (projeto lab ainda sem mapa)
        p, _ = audit(d, require=False)
        assert not p, f"ausência sem --require não pode reprovar: {p}"
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print("[SELF-CHECK OK] rom_asset_binding "
          "(válido passa; SHA ROM/PNG divergem; mapa ausente só com --require)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    ap.add_argument("--rom")
    ap.add_argument("--map")
    ap.add_argument("--require", action="store_true",
                    help="mapa ausente REPROVA (entrega / ready_for_aaa)")
    ap.add_argument("--json")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.self_check:
        return _self_check()
    problems, report = audit(args.project, rom_path=args.rom,
                             map_path=args.map, require=args.require)
    if args.json:
        json.dump({"problems": problems, "report": report},
                  open(args.json, "w"), indent=2, ensure_ascii=False)
    if problems:
        for p in problems:
            print(f"[FAIL] {p}")
        return 1
    print("[OK] rom_asset_binding")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
