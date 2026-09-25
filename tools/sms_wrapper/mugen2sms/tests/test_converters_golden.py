"""S4 golden tests: saida de tiles/clsn/cmd/gerador com bytes exatos conhecidos."""
from __future__ import annotations

import re
import struct

from mugen2sms.converters.sms_tiles import to_sms_pose
from mugen2sms.converters.sms_clsn import to_clsn_tables
from mugen2sms.converters.sms_cmd import to_patterns
from mugen2sms.parsers import air, sff, cmd as cmdmod


def sprite(w, h, pixels, palette=None):
    return sff.Sprite(1, 0, 0, 0, w, h, pixels, palette or [(0, 0, 0)] * 256, False, None, 0)


RED = (255, 0, 0)
GREEN = (0, 255, 0)
PAL = [(0, 0, 0), RED, GREEN] + [(255, 255, 255)] * 253


def test_solid_tile_encodes_4planes_msb():
    # 8x8 inteiro na cor 1 (vermelho) -> plano0=0xFF, planos 1-3 zerados por linha
    sp = sprite(8, 8, bytes([1] * 64), PAL)
    pose = to_sms_pose(sp)
    assert pose.tiles == [bytes([0xFF, 0, 0, 0] * 8)]
    assert len(pose.tiles[0]) == 32
    assert pose.unique_tiles == 1 and pose.flips_used == 0


def test_checkerboard_dedups_with_flips():
    # 16x8: tile direito e o espelho H do esquerdo -> 1 tile unico + 1 flip
    row = bytes([1] * 4 + [2] * 4 + [2] * 4 + [1] * 4)
    sp = sprite(16, 8, row * 8, PAL)
    pose = to_sms_pose(sp)
    assert pose.unique_tiles == 1
    assert pose.flips_used == 1
    assert [p.hflip for p in pose.placements] == [False, True]


def test_palette_word_is_header_rgb_macro():
    # SMSlib.h: RGB(r,g,b) = r | g<<2 | b<<4 com canais 0..3
    sp = sprite(8, 8, bytes([1] * 64), PAL)
    pose = to_sms_pose(sp)
    assert pose.palette[1] == 3                 # vermelho puro -> (3,0,0) -> 0b000011
    assert pose.palette[0] == 0                 # indice 0 transparente


def test_edge_padded_with_transparent():
    sp = sprite(9, 1, bytes([1] * 9), PAL)          # 9 px: tile0 cheio, tile1 = 1 px + 7 transparentes
    pose = to_sms_pose(sp)
    # canone lexicografico entre os 4 flips: a linha visivel vira a ULTIMA (vflip),
    # e as duas posicoes apontam para os tiles deduplicados com flags de flip
    assert pose.tiles[0][-4:] == bytes([0xFF, 0, 0, 0])
    assert pose.tiles[1][-4:] == bytes([0x01, 0, 0, 0])   # canone lexicografico poe o px em x7 com flips
    assert all(p.vflip for p in pose.placements)


def test_clsn_tables_are_flat_int16():
    action = air.Action(0, [air.Frame(1, 0, 0, 0, 1, clsn1=[(0, -14, 12, -8)], clsn2=[(-8, -16, 8, 0)])])
    tables = to_clsn_tables({0: action})
    hit, hurt = tables[0][0]                           # anim 0, frame 0
    assert hit == [0, -14, 12, -8]
    assert hurt == [-8, -16, 8, 0]
    struct.pack("<4h", *hit)                    # coube em int16


def test_cmd_patterns_only_sms_pad_survives():
    def command(name, keys, hold=False):
        return cmdmod.Command(name, [cmdmod.Step([cmdmod.Key(k, hold=hold) for k in keys])], 1, 0, 1, name)
    patterns, skipped = to_patterns([
        command("punch", ["a"]),
        command("holdF", ["F"], hold=True),
        command("diag", ["DF"]),
        command("kick", ["b"]),
        command("charge", ["B"]),
    ])
    assert {p.name for p in patterns} == {"punch", "holdF", "charge"}
    assert skipped["diag"] == "diagonal-impossivel-pad"
    assert skipped["kick"] == "botao>pad"
    punch = next(p for p in patterns if p.name == "punch")
    assert punch.steps[0].keys == 0x01                    # A
    holdf = next(p for p in patterns if p.name == "holdF")
    assert holdf.steps[0].dir == 0x08                     # R (F mapeia p/ direita-para-frente no runtime)
    assert holdf.steps[0].hold is True


def test_define_size_matches_array_len():
    from mugen2sms.generators.smsdev import Artifact, render_header
    hdr = render_header([Artifact("FOO_TILES", b"\x01\x02\x03", "sff")], "foo")
    size = re.search(r"#define FOO_TILES_SIZE (\d+)", hdr).group(1)
    decl = re.search(r"const unsigned char FOO_TILES\[(\d+)\]", hdr).group(1)
    n = hdr.split("FOO_TILES[3]")[1].count("0x")
    assert size == decl == str(n) == "3"


def test_generate_synthetic_character_roundtrip(tmp_path):
    from mugen2sms.analysis.fidelity import classify_character
    from mugen2sms.analysis.sms_budget import SmsLimits
    from mugen2sms.character import load
    from mugen2sms.generators.smsdev import generate
    from mugen2sms.source import Source
    from mugen2sms.tests.make_fixtures import build
    root = build(tmp_path / "mini")
    ch = load(Source(root))
    fid = classify_character(ch, SmsLimits())
    man = generate(ch, fid, tmp_path / "gen")
    assert man.entries and man.stats["bytes"] > 0
    hdr = (tmp_path / "gen" / "mini_art.h").read_text(encoding="ascii")
    for e in man.entries:
        assert f"#define {e['symbol']}_SIZE {e['size_bytes']}" in hdr
        assert f"const unsigned char {e['symbol']}[{e['size_bytes']}]" in hdr
    import json
    m = json.loads((tmp_path / "gen" / "mini_manifest.json").read_text())
    assert m["generated_sha256"] == man.generated_sha256


def test_synthetic_cut_passes_scanline_gate(tmp_path):
    """Gate do harness sobre saida gerada commitavel: cena pior-frame do mini passa."""
    import json
    import audit_sprite_line_sim as sim
    from mugen2sms.analysis.fidelity import classify_character
    from mugen2sms.analysis.sms_budget import SmsLimits
    from mugen2sms.character import load
    from mugen2sms.generators.smsdev import _worst_scene, generate
    from mugen2sms.source import Source
    from mugen2sms.tests.make_fixtures import build
    ch = load(Source(build(tmp_path / "mini")))
    fid = classify_character(ch, SmsLimits())
    man = generate(ch, fid, tmp_path / "gen")
    scene = _worst_scene(ch, fid)
    assert scene is not None
    report = sim.simulate(scene)
    assert report["violations"] == [], report
    assert report["peak_per_line"] <= 8
