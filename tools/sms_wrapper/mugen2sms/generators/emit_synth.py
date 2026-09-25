"""Emite o header de arte do personagem SINTETICO dos testes (mini) — fixture
committavel para as cenas do runtime sem tocar em arte real (politica do GDD:
Ken nunca entra no git). Deterministico: mesma saida byte a byte em qualquer maquina.

Uso (de tools/sms_wrapper):
  python3 -m mugen2sms.generators.emit_synth > ../../SMS_projects/luta_mugen/inc/gen/mini_art.h
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path


def main(argv=None) -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from mugen2sms import character as CH
    from mugen2sms.source import Source
    from mugen2sms.analysis.fidelity import classify_character
    from mugen2sms.analysis.sms_budget import SmsLimits
    from mugen2sms.generators import smsdev
    from mugen2sms.tests.make_fixtures import build

    with tempfile.TemporaryDirectory() as td:
        ch = CH.load(Source(build(Path(td) / "minichar")))
    fid = classify_character(ch, SmsLimits())
    with tempfile.TemporaryDirectory() as out:
        man = smsdev.generate(ch, fid, Path(out))
        hdr = Path(out, "mini_art.h").read_text(encoding="ascii")
    sys.stdout.write(hdr)
    print(f"/* fixture sintetico: {man.stats} — gerado por emit_synth, nao editar */",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
