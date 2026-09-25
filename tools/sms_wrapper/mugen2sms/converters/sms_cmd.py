"""Comandos MUGEN -> patterns de buffer para o interpretador do Plano 2.

Pad SMS: 4 direcionais fisicos (diagonal e mecanicamente impossivel no cross-pad)
+ 1 botao + start (SMSlib le o porta paralela; nao ha definicao de bot extras).
Convencao: F/B viram R/L relativos a frente; o runtime inverte pela facing.
"""
from __future__ import annotations

from dataclasses import dataclass, field

DIR_BITS = {"U": 0x01, "D": 0x02, "B": 0x04, "F": 0x08, "N": 0x00}   # B=retrato, N=nenhum
KEY_BITS = {"a": 0x01, "s": 0x02}                                    # A / START
DIAGONALS = {"DF", "DB", "UF", "UB"}


@dataclass
class StepCode:
    dir: int = 0
    keys: int = 0
    hold: bool = False
    release: bool = False
    rel_time: int = 0


@dataclass
class Pattern:
    name: str
    window: int                                   # ticks maximos do comando
    buffer: int
    steps: list[StepCode] = field(default_factory=list)


def to_patterns(commands) -> tuple[list[Pattern], dict[str, str]]:
    """(patterns suportadas, {nome: motivo} das que exigem reautoria manual)."""
    out, skipped = [], {}
    for c in commands:
        bad = _unsupported(c)
        if bad:
            skipped[c.name] = bad
            continue
        steps = []
        for st in c.steps:
            code = StepCode()
            for k in st.keys:
                if k.key in DIAGONALS or (k.four_way and k.key in ("F", "B", "U", "D")):
                    # $F aceita diagonais -> seria preciso segurar duas setas: fora do pad
                    bad = "diagonal-impossivel-pad"
                    break
                if k.key in DIR_BITS:
                    code.dir |= DIR_BITS[k.key]
                elif k.key in KEY_BITS:
                    code.keys |= KEY_BITS[k.key]
                else:
                    bad = "botao>pad"
                    break
                code.hold = code.hold or k.hold
                code.release = code.release or k.release
                code.rel_time = max(code.rel_time, k.release_time)
            if bad:
                break
            steps.append(code)
        if bad:
            skipped[c.name] = bad
            continue
        out.append(Pattern(c.name, c.time, c.buffer_time, steps))
    return out, skipped


def _unsupported(c) -> str | None:
    for st in c.steps:
        for k in st.keys:
            if k.key in DIAGONALS or (k.four_way and k.key in ("F", "B", "U", "D")):
                return "diagonal-impossivel-pad"
            if len(k.key) == 1 and k.key.islower() and k.key not in KEY_BITS and k.key != "n":
                return "botao>pad"
    if c.errors:
        return "cmd-com-erro-de-parse"
    return None
