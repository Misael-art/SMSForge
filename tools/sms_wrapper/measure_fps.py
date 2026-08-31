#!/usr/bin/env python3
"""measure_fps.py — F2 do PLANO_CONTINUACAO: amostra o FPS reportado pelo
próprio emulador no título da janela principal ("Emulicious - NN% (NN fps)").

Uso: measure_fps.py [--samples 6] [--interval 1.0] [-o saida.json]
Exit: 0 com JSON | 2 janela nao encontrada
"""
import sys, os, json, time, argparse, subprocess, re

def xdotool(*args):
    r = subprocess.run(["xdotool", *args], capture_output=True, text=True)
    return r if r.returncode == 0 else None

def find_main_window():
    r = xdotool("search", "--class", "Emulicious")
    ids = r.stdout.split() if r else []
    for i in ids:
        nm = xdotool("getwindowname", i)
        if nm and "fps" in nm.stdout.lower():
            return i, nm.stdout.strip()
    return None, None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=6)
    ap.add_argument("--interval", type=float, default=1.0)
    ap.add_argument("-o", "--out")
    a = ap.parse_args()

    wid, title = find_main_window()
    if not wid:
        print("[FAIL_AMBIENTE] janela do Emulicious com fps no titulo nao encontrada",
              file=sys.stderr)
        return 2
    samples = []
    t_start = time.time()
    for n in range(a.samples):
        _, t = find_main_window()
        m = re.search(r"\((\d+)\s*fps\)", t or "")
        pct = re.search(r"-\s*(\d+)%", t or "")
        samples.append({"t": round(time.time() - t_start, 2),
                        "fps": int(m.group(1)) if m else None,
                        "pct": int(pct.group(1)) if pct else None})
        print(f"[{n+1}/{a.samples}] {t}", flush=True)
        if n < a.samples - 1:
            time.sleep(a.interval)
    fps_vals = [s["fps"] for s in samples if s["fps"] is not None]
    out = {"tool": "emulicious-window-title",
           "window": title, "samples": samples,
           "fps_min": min(fps_vals) if fps_vals else None,
           "fps_max": max(fps_vals) if fps_vals else None,
           "fps_media": round(sum(fps_vals) / len(fps_vals), 1) if fps_vals else None,
           "constante_50_60": all(50 <= v <= 60 for v in fps_vals) if fps_vals else False}
    txt = json.dumps(out, indent=2)
    print(txt)
    if a.out:
        json.dump(out, open(a.out, "w"), indent=2)
        print(f"[OK] salvo em {a.out}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
