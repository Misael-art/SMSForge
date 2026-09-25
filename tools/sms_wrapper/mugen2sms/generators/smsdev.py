"""Gerador SMSdev: artefatos dos converters -> headers C + manifest com SHA por simbolo.

Formato pensado para os gates do workspace:
- `#define <SYM>_SIZE <n>` sempre igual ao comprimento do array (`audit_symbol_size_sync.py`);
- header idempotente (guard `#ifndef`), ASCII, `const unsigned char` (sem float/malloc);
- manifest `{symbol, size_bytes, sha256_dos_bytes, source_sha256}` — insumo do
  `audit_rom_asset_binding.py` na S5+.

So viram artefato elementos `direct|approximate` do FidelityReport (S3);
`manual|unsupported` viram linha no relatorio de exclusao — nada silencioso.

Formato dos simbolos por pose (consumido pelo runtime do Plano 2):
  <S>_A<anim>F<frame>_TILES : tiles 4bpp concatenados, 32 B cada
  <S>_A<anim>F<frame>_PAL    : 16 palavras CRAM u8 (RGB r|g<<2|b<<4, SMSlib.h)
  <S>_A<anim>F<frame>_MAP    : triples (tile|hf<<7|vf<<6, x, y) i8, ordem de desenho
  <S>_A<anim>F<frame>_CLSN   : quádruplas int16 (hit vem primeiro, depois hurt), terminador sentinela
"""
from __future__ import annotations

import hashlib
import json
import re
import struct
import sys
from dataclasses import dataclass, field
from pathlib import Path

from ..converters.sms_tiles import to_sms_pose
from ..converters.sms_clsn import to_clsn_tables
from ..converters.sms_cmd import to_patterns


@dataclass
class Artifact:
    symbol: str
    data: bytes
    source: str


@dataclass
class GenerationManifest:
    entries: list[dict] = field(default_factory=list)
    excluded: list[dict] = field(default_factory=list)
    stats: dict = field(default_factory=dict)
    generated_sha256: str = ""


def slug(name: str) -> str:
    s = re.sub(r"[^0-9a-z]+", "_", name.lower()).strip("_")
    return (s or "char").upper()


def render_header(artifacts: list[Artifact], guard: str) -> str:
    lines = [f"#ifndef {guard}_H", f"#define {guard}_H", "",
             "/* gerado por mugen2sms.generators.smsdev - nao editar na mao */", ""]
    for a in artifacts:
        lines.append(f"#define {a.symbol}_SIZE {len(a.data)}")
        lines.append(f"const unsigned char {a.symbol}[{len(a.data)}] = {{")
        for i in range(0, len(a.data), 16):
            lines.append("    " + ", ".join(f"0x{b:02X}" for b in a.data[i:i + 16]) + ",")
        lines.append("};")
        lines.append("")
    lines.append(f"#endif /* {guard}_H */")
    return "\n".join(lines) + "\n"


def _map_bytes(pose) -> bytes:
    out = bytearray()
    for p in pose.placements:
        flags = (1 if p.hflip else 0) << 7 | (1 if p.vflip else 0) << 6
        out.append(p.tile | flags)
        out.append(p.x & 0xFF)
        out.append(p.y & 0xFF)
    return bytes(out)


def generate(ch, fidelity, out_dir: Path) -> GenerationManifest:
    out_dir.mkdir(parents=True, exist_ok=True)
    s = slug(Path(ch.def_path).stem)
    artifacts: list[Artifact] = []
    man = GenerationManifest()
    cls_ok = {"direct", "approximate"}

    by_key = {(sp.group, sp.image): sp for sp in ch.sprites}
    clsn = to_clsn_tables(ch.anims)
    for n, action in sorted(ch.anims.items()):
        for i, fr in enumerate(action.frames):
            el = fidelity.by_id.get(f"anim:{n}.{i}")
            if el is None or el.classe not in cls_ok:
                man.excluded.append({"id": f"anim:{n}.{i}",
                                     "classe": el.classe if el else "ausente",
                                     "motivo": el.motivo if el else "sem registro"})
                continue
            sp = by_key.get((fr.group, fr.image))
            if sp is None:
                man.excluded.append({"id": f"anim:{n}.{i}", "classe": "unsupported",
                                     "motivo": "sprite-ausente"})
                continue
            pose = to_sms_pose(sp)
            stem = f"{s}_A{n}F{i}"
            artifacts.append(Artifact(f"{stem}_TILES", b"".join(pose.tiles), "sff"))
            artifacts.append(Artifact(f"{stem}_PAL", bytes(pose.palette), "sff+act"))
            artifacts.append(Artifact(f"{stem}_MAP", _map_bytes(pose), "air"))
            artifacts.append(Artifact(f"{stem}_AXIS", struct.pack("<2h", fr.x, fr.y), "air"))
            hit, hurt = clsn[n][i]
            if hit or hurt:
                data = b"".join(struct.pack("<h", v) for v in (hit + hurt)) \
                    + struct.pack("<h", -32767)          # sentinela de fim
                artifacts.append(Artifact(f"{stem}_CLSN", data, "air"))

    patterns, skipped = to_patterns(ch.commands)
    for p in patterns:
        data = bytearray([len(p.steps), p.window & 0xFF, p.buffer & 0xFF])
        for st in p.steps:
            data += bytes([st.dir | st.keys << 4, (1 if st.hold else 0) | (2 if st.release else 0)])
        artifacts.append(Artifact(f"{s}_CMD_{re.sub(r'[^0-9a-zA-Z]+', '_', p.name).upper()}",
                                  bytes(data), "cmd"))
    for name, why in skipped.items():
        man.excluded.append({"id": f"cmd:{name}", "classe": "manual", "motivo": why})

    hdr = render_header(artifacts, s.lower())
    (out_dir / f"{s.lower()}_art.h").write_text(hdr, encoding="ascii")
    hdr_bytes = hdr.encode("ascii")
    man.generated_sha256 = hashlib.sha256(hdr_bytes).hexdigest()
    for a in artifacts:
        man.entries.append({"symbol": a.symbol, "size_bytes": len(a.data),
                            "sha256": hashlib.sha256(a.data).hexdigest(),
                            "source": a.source, "source_sha256": ch.source_sha256})
    man.stats = {"artifacts": len(artifacts), "bytes": sum(len(a.data) for a in artifacts),
                 "excluded": len(man.excluded)}
    (out_dir / f"{s.lower()}_manifest.json").write_text(
        json.dumps({"entries": man.entries, "excluded": man.excluded, "stats": man.stats,
                    "generated_sha256": man.generated_sha256}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    return man


def _worst_scene(ch, fid, size="8x8"):
    """Cena pior-frame: maior pose gerada, ego + oponente colados no mesmo y."""
    poses = []
    by_key = {(sp.group, sp.image): sp for sp in ch.sprites}
    for n, action in ch.anims.items():
        for i, fr in enumerate(action.frames):
            el = fid.by_id.get(f"anim:{n}.{i}")
            if el is None or el.classe not in ("direct", "approximate"):
                continue
            sp = by_key.get((fr.group, fr.image))
            if sp is None:
                continue
            tw, th = -(-sp.width // 8), -(-sp.height // 8)
            poses.append((tw * th, tw, th, n, i))
    if not poses:
        return None
    total, tw, th, n, i = max(poses)
    sprites = []
    for off, base in ((0, 0), (tw * 8, 256 - tw * 8)):     # dois lutadores, mesma linha
        for ty in range(th):
            for tx in range(tw):
                sprites.append({"y": 192 - th * 8 + ty * 8, "x": base + tx * 8, "tile": 0})
    return {"sprite_size": size, "zoomed": False, "sprites": sprites, "screen_h": 192,
            "pose_pior": f"anim {n} frame {i} ({tw}x{th} tiles)"}


def main(argv=None) -> int:
    import argparse
    import sys
    from pathlib import Path
    ap = argparse.ArgumentParser(description="gera artefatos SMS a partir de um pacote MUGEN")
    ap.add_argument("pacote", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from ..analysis.fidelity import classify_character
    from ..analysis.sms_budget import SmsLimits
    from ..character import load as ch_load
    from ..source import Source
    import audit_sprite_line_sim as sim
    ch = ch_load(Source(args.pacote))
    fid = classify_character(ch, SmsLimits())
    man = generate(ch, fid, args.out)
    scene = _worst_scene(ch, fid)
    (args.out / "worst_scene.json").write_text(json.dumps(scene, indent=2), encoding="utf-8")
    verdict = sim.simulate(scene)
    report = {"stats": man.stats, "excluded_by_classe":
              {c: sum(1 for e in man.excluded if e["classe"] == c) for c in
               ("approximate", "manual", "unsupported", "ausente")},
              "fidelity_totals": fid.totals, "generated_sha256": man.generated_sha256,
              "gate_scanline": {"peak_per_line": verdict["peak_per_line"],
                                "sat_entries": verdict["sprites"],
                                "violations": verdict["violations"][:6],
                                "veredito": "PASS" if not verdict["violations"] else "FAIL"}}
    (args.out / "s4_generation_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[{'GATE ' + report['gate_scanline']['veredito']}] {man.stats} "
          f"peak={verdict['peak_per_line']}/linha sat={verdict['sprites']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
