"""S4.5a — contrato de escala travado no GDD (2026-09-25): downscale 1:4 fixo,
lutador <=4 sprites/scanline (~32 px) x <=3 linhas TALL (~48 px).
Regra do GDD: pose que estourar DEPOIS da escala vira `manual` e nao entra no build.
"""
from __future__ import annotations

from mugen2sms.converters import sms_scale as sc
from mugen2sms.parsers import sff


def sprite(w, h, pixels, palette=None):
    return sff.Sprite(1, 0, 0, 0, w, h, pixels,
                      palette or [(0, 0, 0)] * 256, False, None, 0)


def test_downscale_nearest_preserva_indices_e_palette():
    pal = [(0, 0, 0), (255, 0, 0), (0, 255, 0)] + [(0, 0, 0)] * 253
    px = bytes([1] * (16 * 8) + [2] * (16 * 8))       # 16x16: topo vermelho, base verde
    out = sc.downscale_indexed(sprite(16, 16, px, pal), 4)
    assert (out.width, out.height) == (4, 4)
    assert out.pixels == bytes([1] * 8 + [2] * 8)   # 4x4: 2 linhas 1, 2 linhas 2
    assert out.palette is pal or list(out.palette) == list(pal)


def test_orcamento_pose_sob_escala():
    # 128x112 nativo -> 32x28 -> 4 colunas de 8 px; 28 px = 2 linhas TALL
    assert sc.pose_runtime_size(128, 112) == (4, 2)
    assert not sc.exceeds_budget(128, 112)


def test_orcamento_estoura_apos_escala_vira_manual():
    # 192 px nativos -> 48 pos-escala -> 6 colunas de 8 px > MAX_COLS (4)
    assert sc.exceeds_budget(192, 48)
    # 256 px de altura nativa -> 64 pos-escala -> 4 linhas TALL > MAX_TALL_ROWS (3)
    assert sc.pose_runtime_size(48, 256) == (2, 4)
    assert sc.exceeds_budget(48, 256)


def test_tetos_do_gdd():
    assert (sc.SCALE, sc.MAX_COLS, sc.MAX_TALL_ROWS) == (4, 4, 3)
