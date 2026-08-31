#!/usr/bin/env python3
"""sms_palette.py — verdade da cor no SMSForge.

O Master System tem paleta mestra FIXA: cada entrada de CRAM guarda um codigo
de 6 bits (2 por canal RGB, valores 0..3). Nao existe "qualquer RGB".

CONTRATO DE COR deste workspace:
- Verdade = codigo 6-bit (canais 0..3).
- RGB de contrato para assets = canal * 85 -> {0, 85, 170, 255}.
  (Derivacao linear documentada. O RGB fisico de saida varia por revisao de
  console/DAC; recalibracao contra captura real fica registrada como tecnica
  futura na matriz de maestria. Codigos sao estaveis; adjetivos nao.)
- Luma derivada: Y = 0.30R + 0.59G + 0.11B sobre o RGB de contrato (escala 0..255).
- Piso de contraste padrao: delta-Y >= 17 (~meio degrau de canal). Calibravel
  via schema scene_budget; nunca "olho nu".
"""

STEP = 85
CHANNELS = (0, STEP, STEP * 2, 255)

def code_rgb(code):
    """code = (r,g,b) com canais 0..3 -> RGB de contrato."""
    r, g, b = code
    for ch in (r, g, b):
        if ch not in (0, 1, 2, 3):
            raise ValueError(f"canal fora dos codigos 6-bit: {ch}")
    return (r * STEP, g * STEP, b * STEP)

ALL_CONTRACT_RBG = {code_rgb((r, g, b)) for r in range(4) for g in range(4) for b in range(4)}

def is_contract_color(rgb):
    return rgb in ALL_CONTRACT_RBG

def nearest_code(rgb):
    best, bd = None, 10 ** 9
    for r in range(4):
        for g in range(4):
            for b in range(4):
                c = code_rgb((r, g, b))
                d = sum((c[i] - rgb[i]) ** 2 for i in range(3))
                if d < bd:
                    best, bd = (r, g, b), d
    return best

def luma(rgb):
    return int(round(0.30 * rgb[0] + 0.59 * rgb[1] + 0.11 * rgb[2]))

LUMA_FLOOR_DEFAULT = 17

def contrast_ok(rgb_a, rgb_b, floor=LUMA_FLOOR_DEFAULT):
    return abs(luma(rgb_a) - luma(rgb_b)) >= floor

if __name__ == "__main__":
    assert code_rgb((3, 3, 3)) == (255, 255, 255)
    assert code_rgb((0, 0, 0)) == (0, 0, 0)
    assert not is_contract_color((128, 128, 128))
    assert is_contract_color((170, 85, 0))
    assert contrast_ok((255, 255, 255), (0, 0, 0))
    # par proximo real: (85,85,0) vs (0,85,85) -> dY ~16 < piso
    assert not contrast_ok(code_rgb((1, 1, 0)), code_rgb((0, 1, 1)))
    print("[SELF-CHECK OK] sms_palette")
