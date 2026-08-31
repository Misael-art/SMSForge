#!/usr/bin/env python3
"""audit_deterministic_boot.py — gate de boot preservavel/deterministico (porta do SGDK Forge).

Regra do SMSForge (§24): boot deterministico = MESMO estado inicial toda execucao,
para que evidencia comparavel exista. Este gate executa a ROM no Emulicious
2x e compara o estado do playfield (sprites no SAT + pixels nao-pretos).

Sem emulador configurado -> FAIL_AMBIENTE (honesto, nao simula).

Uso:
  audit_deterministic_boot.py --project <dir> --rom <rom.sms> [--runs 2]
  audit_deterministic_boot.py --self-check
Exit: 0 deterministico | 1 divergente | 2 ambiente ausente | 3 uso
"""
import sys, os, json, argparse, subprocess, time, hashlib

def capture_playfield_hash(rom, jar, runs=2):
    """Langa a ROM `runs` vezes, captura o playfield via Emulicious e devolve
    lista de hashes. Retorna None se emulador/import indisponivel."""
    hashes = []
    for _ in range(runs):
        proc = subprocess.Popen(["java", "-jar", jar, os.path.abspath(rom)],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                start_new_session=True)
        canvas = None
        t0 = time.time()
        while time.time() - t0 < 25:
            time.sleep(0.4)
            r = subprocess.run(["xdotool", "search", "--name", "XCanvasPeer"],
                               capture_output=True, text=True)
            for i in (r.stdout.split() if r else []):
                g = subprocess.run(["xdotool", "getwindowgeometry", "--shell", i],
                                   capture_output=True, text=True)
                kv = dict(l.split("=") for l in g.stdout.strip().splitlines() if "=" in l)
                if kv.get("WIDTH") == "256":
                    canvas = i
                    break
            if canvas:
                break
        if not canvas:
            if proc.poll() is None:
                proc.terminate()
            return None
        # espera curta p/ VDP estabilizar o frame de init (displayOn) sem
        # esperar a animacao do loop divergir
        time.sleep(0.5)
        png = f"/tmp/smsforge_det_{hashlib.md5(rom.encode()).hexdigest()[:8]}_{_}.png"
        if os.path.exists(png):
            os.remove(png)
        subprocess.run(["import", "-window", canvas, png],
                       capture_output=True, timeout=40)
        if proc.poll() is None:
            proc.terminate()
        if not os.path.exists(png) or os.path.getsize(png) < 100:
            return None
        hashes.append(hashlib.md5(open(png, "rb").read()).hexdigest())
        time.sleep(1)   # garante que a 1a instancia encerrou p/ a proxima
    return hashes

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    ap.add_argument("--rom")
    ap.add_argument("--runs", type=int, default=2)
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.self_check:
        # determinismo e' verificavel apenas por execucao real; aqui valida a
        # logica de comparacao de hashes (que independe do emulador).
        h = {"a": "1", "b": "1"}
        assert len(set(h.values())) == 1, "hashes iguais => determinismo"
        h2 = {"a": "1", "b": "2"}
        assert len(set(h2.values())) != 1, "hashes diferentes => divergencia"
        print("[SELF-CHECK OK] deterministic_boot (logica de comparacao)")
        return 0
    if not args.rom:
        print("[FAIL] --rom obrigatorio (boot deterministico exige ROM p/ comparar)",
              file=sys.stderr)
        return 3
    import shutil
    jar = shutil.which("Emulicious.jar") or "/mnt/sdcard/Projects/SMSForge/tools/emuladores/emulicious/Emulicious.jar"
    if not os.path.exists(jar):
        jar = os.path.join(os.path.dirname(__file__), "..", "emuladores", "emulicious", "Emulicious.jar")
    if not os.path.exists(jar):
        print("[FAIL_AMBIENTE] Emulicious.jar nao encontrado; "
              "nao posso verificarcar boot deterministico (gate nao simula)")
        return 2
    hashes = capture_playfield_hash(args.rom, jar, args.runs)
    if hashes is None:
        print("[FAIL_AMBIENTE] nao consegui capturar playfield (import/canvas indisponivel)")
        return 2
    if len(set(hashes)) == 1:
        print(f"[PASS] boot deterministico: {args.runs} execucoes com estado identico")
        return 0
    print(f"[FAIL] boot NAO deterministico: hashes divergentes {hashes}")
    return 1

if __name__ == "__main__":
    sys.exit(main())
