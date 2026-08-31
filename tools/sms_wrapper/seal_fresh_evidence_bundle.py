#!/usr/bin/env python3
"""seal_fresh_evidence_bundle.py — evidencia velha nao sustenta claim novo.

Buraco que este gate fecha: `out/evidence/` acumula PNGs soltos sem nada que
os prenda a UMA execucao de UMA ROM. Nada impede reapresentar a captura de tres
semanas atras — de outra versao do binario — como prova da build de hoje.

Regra dura: **a evidencia nao pode ser mais VELHA que a ROM que ela afirma
mostrar.** Se o .sms foi relinkado depois do screenshot, o screenshot mostra
outro programa.

Checagens:
  1. ROM existe e casa em sha256 com a citada no bundle
  2. Todo artefato e POSTERIOR a ROM (mtime) — senao e evidencia orfa
  3. Todo artefato cabe na janela de sessao (--max-age-min, default 120)
  4. Sela o bundle com sha256 de cada artefato + timestamps UTC

Uso:
  seal_fresh_evidence_bundle.py --rom <rom.sms> --artifact <f> [--artifact <f>...]
      [--max-age-min 120] [-o bundle.json] [--self-check]
Exit: 0 selado | 1 evidencia orfa/velha | 3 uso
"""
import sys, os, json, time, hashlib, argparse
from datetime import datetime, timezone

DEFAULT_MAX_AGE_MIN = 120

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).isoformat()

def seal(rom, artifacts, max_age_min=DEFAULT_MAX_AGE_MIN, now=None):
    """Retorna (problems, bundle). `now` injetavel para tornar o gate testavel."""
    now = time.time() if now is None else now
    problems = []
    bundle = {"generated_at": iso(now), "rom": rom,
              "max_age_min": max_age_min, "artifacts": []}

    if not os.path.isfile(rom):
        return [f"ROM inexistente: {rom}"], bundle
    rom_mtime = os.path.getmtime(rom)
    bundle["rom_sha256"] = sha256_file(rom)
    bundle["rom_built_at"] = iso(rom_mtime)

    if not artifacts:
        problems.append("bundle sem artefatos — nada a selar")

    for a in artifacts:
        entry = {"path": a}
        if not os.path.isfile(a):
            problems.append(f"artefato inexistente: {a}")
            entry["ok"] = False
            bundle["artifacts"].append(entry)
            continue
        mt = os.path.getmtime(a)
        entry.update({"sha256": sha256_file(a), "captured_at": iso(mt),
                      "age_min": round((now - mt) / 60.0, 1),
                      "seconds_after_rom": round(mt - rom_mtime, 1)})
        ok = True
        # (2) evidencia anterior a ROM = orfa
        if mt < rom_mtime:
            problems.append(
                f"{os.path.basename(a)} e ANTERIOR a ROM "
                f"({entry['captured_at']} < {bundle['rom_built_at']}) — "
                "mostra outro binario, nao esta build")
            ok = False
        # (3) fora da janela de sessao
        if entry["age_min"] > max_age_min:
            problems.append(
                f"{os.path.basename(a)} tem {entry['age_min']:.0f}min "
                f"(> {max_age_min}min) — evidencia de outra sessao")
            ok = False
        entry["ok"] = ok
        bundle["artifacts"].append(entry)

    bundle["sealed"] = not problems
    return problems, bundle

def _self_check():
    import tempfile, shutil
    d = tempfile.mkdtemp(prefix="smsseal_")
    try:
        now = 1_000_000.0
        rom = os.path.join(d, "x.sms")
        open(rom, "wb").write(b"ROM")
        os.utime(rom, (now - 600, now - 600))          # ROM feita 10min atras

        fresh = os.path.join(d, "fresh.png")
        open(fresh, "wb").write(b"shot")
        os.utime(fresh, (now - 300, now - 300))        # captura 5min atras (depois da ROM)
        p, b = seal(rom, [fresh], now=now)
        assert not p, f"evidencia fresca nao deveria reprovar: {p}"
        assert b["sealed"] and b["artifacts"][0]["sha256"]

        # REPROVA: captura ANTERIOR a ROM
        stale = os.path.join(d, "stale.png")
        open(stale, "wb").write(b"shot")
        os.utime(stale, (now - 900, now - 900))        # 15min atras = antes da ROM
        p, _ = seal(rom, [stale], now=now)
        assert any("ANTERIOR a ROM" in x for x in p), f"faltou pegar evidencia orfa: {p}"

        # REPROVA: fora da janela de sessao
        old_rom = os.path.join(d, "old.sms")
        open(old_rom, "wb").write(b"ROM")
        os.utime(old_rom, (now - 100_000, now - 100_000))
        old_shot = os.path.join(d, "old.png")
        open(old_shot, "wb").write(b"shot")
        os.utime(old_shot, (now - 90_000, now - 90_000))
        p, _ = seal(old_rom, [old_shot], max_age_min=120, now=now)
        assert any("outra sessao" in x for x in p), f"faltou pegar sessao velha: {p}"

        # REPROVA: bundle vazio e ROM ausente
        assert seal(rom, [], now=now)[0], "bundle sem artefatos deveria reprovar"
        assert seal(os.path.join(d, "nao_existe.sms"), [fresh], now=now)[0]
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print("[SELF-CHECK OK] seal_fresh_evidence_bundle (reprova captura anterior "
          "a ROM, evidencia de outra sessao, bundle vazio e ROM ausente)")
    return 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom")
    ap.add_argument("--artifact", action="append", default=[])
    ap.add_argument("--max-age-min", type=int, default=DEFAULT_MAX_AGE_MIN)
    ap.add_argument("-o", "--out")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()

    if a.self_check:
        return _self_check()
    if not a.rom:
        print("[FAIL] --rom obrigatorio (ou use --self-check)", file=sys.stderr)
        return 3

    problems, bundle = seal(a.rom, a.artifact, a.max_age_min)
    if a.out:
        json.dump({"problems": problems, **bundle}, open(a.out, "w"), indent=2)
        print(f"[OK] bundle em {a.out}")
    if problems:
        for p in problems:
            print(f"[FAIL] {p}")
        print("[FAIL] bundle NAO selado: evidencia nao pertence a esta build.")
        return 1
    print(f"[PASS] bundle selado: {len(bundle['artifacts'])} artefato(s) "
          f"posteriores a ROM {bundle['rom_sha256'][:12]}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
