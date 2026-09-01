#!/usr/bin/env python3
"""reconcile_claims.py — o eixo marcado como verdadeiro tem lastro no artefato?

`audit_claims.py` checa o TETO do claim (nao prometer mais do que o aprovado).
Este gate checa a COERENCIA: `out/build_record.json` declara os 7 eixos, mas
quem os preenche e o proprio processo que quer entregar. Se `evidence.json`
registra `interaction_proven: false` e o build_record diz `gameplay: true`,
a fabrica esta se contradizendo por escrito.

Regra: eixo `true` no build_record EXIGE artefato que o sustente.

Mapa eixo -> lastro exigido:
  build              out/rom/*.sms existe
  boot_emulador      evidence.json com informative=true
  gameplay           evidence.json com gameplay.interaction_proven=true
  fps_constante      fps.json com constante_50_60=true
  audio              arquivo de audio capturado (audit_audio.py e quem julga)
  validation_report  build_record.steps.pre_gates == pass
  memory_bank_atualizado   doc/10-memory-bank.md existe

Uso: reconcile_claims.py --project <dir> [--json <saida>] [--self-check]
Exit: 0 coerente | 1 eixo sem lastro | 3 uso
"""
import sys, os, json, glob, argparse

def _load(path):
    try:
        return json.load(open(path))
    except (OSError, json.JSONDecodeError):
        return None

def reconcile(project):
    """Retorna (problems, report)."""
    problems = []
    report = {"project": project, "axes": {}}
    rec = _load(os.path.join(project, "out", "build_record.json"))
    if rec is None:
        return ["out/build_record.json ausente ou ilegivel — sem claims a conciliar"], report

    axes = rec.get("axes", {}) or {}
    ev = _load(os.path.join(project, "out", "evidence", "evidence.json")) or {}
    fps = _load(os.path.join(project, "out", "evidence", "fps.json")) or {}
    report["axes_declared"] = axes

    def check(axis, supported, why):
        declared = bool(axes.get(axis))
        report["axes"][axis] = {"declared": declared, "supported": supported}
        if declared and not supported:
            problems.append(f"eixo '{axis}' declarado TRUE mas {why}")

    check("build",
          bool(glob.glob(os.path.join(project, "out", "rom", "*.sms"))),
          "nao ha ROM em out/rom/")
    check("validation_report",
          (rec.get("steps", {}) or {}).get("pre_gates") == "pass",
          "build_record.steps.pre_gates != 'pass'")
    check("boot_emulador",
          bool(ev.get("informative")),
          "evidence.json nao tem informative=true")
    check("gameplay",
          bool((ev.get("gameplay") or {}).get("interaction_proven")),
          "evidence.json registra interaction_proven=false "
          "(input nao mudou o viewport)")
    check("fps_constante",
          bool(fps.get("constante_50_60")),
          "fps.json nao tem constante_50_60=true")
    # §26: wav ANTERIOR a ROM e prova de outro binario. O acervo costuma ter
    # .wav de builds antigas; existir nao basta, precisa ser desta ROM.
    wavs = glob.glob(os.path.join(project, "out", "evidence", "*.wav"))
    roms = glob.glob(os.path.join(project, "out", "rom", "*.sms"))
    fresh_wav = False
    if wavs and roms:
        newest_rom = max(os.path.getmtime(r) for r in roms)
        fresh_wav = any(os.path.getmtime(w) > newest_rom for w in wavs)
    check("audio", fresh_wav,
          "nao ha captura de audio (.wav) POSTERIOR a ROM em out/evidence/ "
          "(wav de build antiga nao prova o binario atual)")
    check("memory_bank_atualizado",
          os.path.isfile(os.path.join(project, "doc", "10-memory-bank.md")),
          "doc/10-memory-bank.md nao existe")

    report["coherent"] = not problems
    return problems, report

def _self_check():
    import tempfile, shutil
    d = tempfile.mkdtemp(prefix="smsrec_")
    try:
        def build(axes, ev=None, fps=None, rom=True, wav=True, mb=True):
            p = tempfile.mkdtemp(dir=d)
            os.makedirs(os.path.join(p, "out", "rom"))
            os.makedirs(os.path.join(p, "out", "evidence"))
            os.makedirs(os.path.join(p, "doc"))
            if rom:
                open(os.path.join(p, "out", "rom", "a.sms"), "wb").write(b"\0")
            if wav:
                open(os.path.join(p, "out", "evidence", "a.wav"), "wb").write(b"\0")
            if mb:
                open(os.path.join(p, "doc", "10-memory-bank.md"), "w").write("x")
            json.dump({"axes": axes, "steps": {"pre_gates": "pass"}},
                      open(os.path.join(p, "out", "build_record.json"), "w"))
            if ev is not None:
                json.dump(ev, open(os.path.join(p, "out", "evidence",
                                                "evidence.json"), "w"))
            if fps is not None:
                json.dump(fps, open(os.path.join(p, "out", "evidence",
                                                 "fps.json"), "w"))
            return p

        all_true = {"build": True, "validation_report": True, "boot_emulador": True,
                    "gameplay": True, "fps_constante": True, "audio": True,
                    "memory_bank_atualizado": True}

        # COERENTE: todo eixo true com lastro
        ok = build(all_true,
                   ev={"informative": True, "gameplay": {"interaction_proven": True}},
                   fps={"constante_50_60": True})
        p, r = reconcile(ok)
        assert not p, f"projeto coerente nao deveria reprovar: {p}"
        assert r["coherent"]

        # REPROVA: gameplay=true com interaction_proven=false (caso real do lab)
        bad = build(all_true,
                    ev={"informative": True, "gameplay": {"interaction_proven": False}},
                    fps={"constante_50_60": True})
        p, _ = reconcile(bad)
        assert any("gameplay" in x for x in p), f"faltou pegar gameplay sem lastro: {p}"

        # REPROVA: fps=true sem fps.json
        p, _ = reconcile(build(all_true,
                               ev={"informative": True,
                                   "gameplay": {"interaction_proven": True}}))
        assert any("fps_constante" in x for x in p), "faltou pegar fps sem lastro"

        # REPROVA: audio=true com wav ANTERIOR a ROM (prova de outro binario)
        stale = build(all_true, ev={"informative": True,
                                    "gameplay": {"interaction_proven": True}},
                      fps={"constante_50_60": True})
        import time as _t
        _rom = glob.glob(os.path.join(stale, "out", "rom", "*.sms"))[0]
        _wav = glob.glob(os.path.join(stale, "out", "evidence", "*.wav"))[0]
        os.utime(_wav, (1000, 1000)); os.utime(_rom, (2000, 2000))
        p, _ = reconcile(stale)
        assert any("'audio'" in x for x in p), f"wav anterior a ROM deveria reprovar: {p}"

        # REPROVA: build=true sem ROM; audio=true sem wav
        p, _ = reconcile(build(all_true,
                               ev={"informative": True,
                                   "gameplay": {"interaction_proven": True}},
                               fps={"constante_50_60": True}, rom=False, wav=False))
        assert any("'build'" in x for x in p), "faltou pegar build sem ROM"
        assert any("'audio'" in x for x in p), "faltou pegar audio sem wav"

        # NAO reprova eixo declarado FALSE sem lastro (honestidade nao e erro)
        p, _ = reconcile(build({"gameplay": False}, ev={"informative": False}))
        assert not any("gameplay" in x for x in p), \
            "eixo declarado false nao pode ser reprovado por falta de lastro"
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print("[SELF-CHECK OK] reconcile_claims (pega eixo TRUE sem lastro no "
          "artefato; nao pune eixo declarado FALSE)")
    return 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    ap.add_argument("--json")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()

    if a.self_check:
        return _self_check()

    problems, report = reconcile(a.project)
    if a.json:
        json.dump({"problems": problems, **report}, open(a.json, "w"), indent=2)
    if problems:
        for p in problems:
            print(f"[FAIL] {p}")
        print(f"[FAIL] {len(problems)} eixo(s) sem lastro. "
              "Eixo verdadeiro no papel e falso no artefato e overclaim.")
        return 1
    print("[PASS] eixos declarados batem com os artefatos de evidencia")
    return 0

if __name__ == "__main__":
    sys.exit(main())
