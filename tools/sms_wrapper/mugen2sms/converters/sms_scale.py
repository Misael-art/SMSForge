"""Contrato de escala do lutador — GDD 2026-09-25 (decisao humana sobre o gate FAIL do S4).

Medicao que originou a regra (s4_generation_report.json, round Ken): pior pose x 2
lutadores = pico 32 sprites/scanline (teto 8, SMSlib) e SAT 256 (teto 64). Ken em
escala nativa MUGEN nao cabe no VDP.

Travado no GDD ("Escala do lutador — TRAVADA"):
- modo de sprite: SPRITEMODE_TALL 8x16 (SMSlib.h:57);
- lutador <=4 sprites/linha (~32 px) x <=3 linhas TALL (~48 px) — 2 lutadores fecham
  o teto exato de 8/scanline, sem flicker (proibido pelo GDD);
- downscale 1:4 FIXO aplicado a todo sprite que nao caiba em 1:1; pose que ainda
  estourar apos a escala vira `manual` (reautoria) e NAO entra no build.

Amostragem nearest topo-esquerda: mesmo metodo de `prepare_sms_pixel_art.py`
(nearest_downscale), que e a doutrina de pixel do SMSForge para reducao.
"""
from __future__ import annotations

from types import SimpleNamespace

SCALE = 4          # 1:4 fixo (GDD)
MAX_COLS = 4       # sprites de 8 px por scanline, por lutador (~32 px)
MAX_TALL_ROWS = 3  # sprites TALL 8x16 de altura (~48 px)


def pose_runtime_size(w_px: int, h_px: int) -> tuple[int, int]:
    """(colunas de 8 px, linhas TALL de 16 px) APOS o downscale 1:4, por excesso."""
    w8 = -(-w_px // SCALE)
    h8 = -(-h_px // SCALE)
    return (-(-w8 // 8), -(-h8 // 16))


def exceeds_budget(w_px: int, h_px: int) -> bool:
    cols, rows = pose_runtime_size(w_px, h_px)
    return cols > MAX_COLS or rows > MAX_TALL_ROWS


def needs_scale(w_px: int, h_px: int) -> bool:
    """1:1 ja cabe no orcamento do lutador? (se nao, entra em downscale)."""
    cols = -(-w_px // 8)
    rows = -(-h_px // 16)
    return cols > MAX_COLS or rows > MAX_TALL_ROWS


def downscale_indexed(sp, k: int = SCALE):
    """Sprite IR (width/height/pixels flat/por palette) -> copia reduzida nearest.

    Paleta e preservada intacta: reduzir pixels nunca aumenta cores uteis; o que
    muda e a frequencia, e `_subpalette` decide por frequencia (sms_tiles.py).
    """
    w, h = max(1, sp.width // k), max(1, sp.height // k)
    src = sp.pixels
    sw = sp.width
    flat = bytearray(w * h)
    for y in range(h):
        sy = min(sp.height - 1, y * k) * sw
        base = y * w
        for x in range(w):
            flat[base + x] = src[sy + min(sw - 1, x * k)]
    return SimpleNamespace(width=w, height=h, pixels=bytes(flat), palette=sp.palette,
                           group=getattr(sp, "group", None), image=getattr(sp, "image", None))
