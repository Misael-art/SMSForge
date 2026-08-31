#!/usr/bin/env python3
"""screenshot_semantic_gate.py — captura nao-vazia ainda pode ser MENTIRA.

`capture_evidence.py` ja reprova tela branca/lisa (variancia de luma). Este gate
ataca o degrau SEGUINTE: a captura tem informacao, mas
  (a) nao veio de um Master System (mockup/render/foto passando por emulador);
  (b) e a MESMA imagem ja usada para sustentar outro claim (reuso);
  (c) esta sendo citada para provar algo que um screenshot nao prova.

O gate NAO julga qualidade artistica e NAO transforma captura em prova de
gameplay ou de fps — ele declara explicitamente o que a imagem nao prova.

Checagens:
  1. Informativa      — variancia de luma (reusa capture_evidence.image_informative)
  2. Nao-monotona     — cor dominante nao pode ocupar quase toda a tela
  3. Conformidade de paleta — as cores tem que cair perto da paleta mestra 6-bit.
     Um SMS so consegue emitir 64 cores; um mockup/IA/foto nao passa.
  4. Anti-reuso       — sha256 diferente de capturas ja usadas em outros claims
  5. Escopo de claim  — o relatorio lista o que a imagem NAO prova

Uso:
  screenshot_semantic_gate.py <shot.png> [--claim boot|gameplay|visual]
      [--against <shot_ja_usado.png> ...] [--json <saida>] [--self-check]
Exit: 0 aprovada | 1 reprovada | 3 uso
"""
import sys, os, json, hashlib, argparse
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from png_io import read_png_rgb, png_size, PngError          # noqa: E402
from sms_palette import nearest_code, code_rgb               # noqa: E402

# Tolerancia por canal entre a cor capturada e a cor de contrato mais proxima.
# Emulador + escala de janela + compressao do screenshot deslocam a cor; um
# mockup/foto erra MUITO mais que isso.
CHANNEL_TOLERANCE = 40
# Fracao minima de pixels que precisa cair dentro da tolerancia.
PALETTE_CONFORMANCE_MIN = 0.80
# Cor dominante nao pode passar disso (tela quase lisa mas com ruido).
DOMINANT_RATIO_MAX = 0.985
MIN_VARIANCE = 40.0
# Captura de DESKTOP INTEIRO nao e evidencia: o viewport vira uma fracao minuscula
# da imagem e o resto e papel de parede. Calibrado em 2026-08-31 contra o acervo
# real do laboratorio_01: capturas legitimas da janela = 283x282 (~80k px);
# boot_v002.png e gameplay_A.png = 2560x1080 com 91.6% de cor de desktop.
DESKTOP_PIXELS = 1_500_000

# O que um screenshot, sozinho, NUNCA prova.
NEVER_PROVEN_BY_SCREENSHOT = {
    "gameplay": "screenshot nao prova interacao — exige diff entre passos de input",
    "fps_constante": "screenshot nao prova taxa de quadros — exige measure_fps.py",
    "audio": "screenshot nao prova audio — exige captura de onda",
    "validado_budget": "screenshot nao prova orcamento — exige medicao worst-frame",
}

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def palette_conformance(rgb_pixels):
    """Fracao de pixels perto de alguma cor da paleta mestra 6-bit."""
    if not rgb_pixels:
        return 0.0, None
    cache, inside = {}, 0
    for px in rgb_pixels:
        if px not in cache:
            target = code_rgb(nearest_code(px))
            cache[px] = max(abs(px[i] - target[i]) for i in range(3)) <= CHANNEL_TOLERANCE
        if cache[px]:
            inside += 1
    return inside / len(rgb_pixels), None

def _sample_pixels(path, max_px=20000):
    w, h, rows = read_png_rgb(path)
    total = w * h
    step = max(1, total // max_px)
    out, i = [], 0
    for row in rows:
        for x in range(w):
            if i % step == 0:
                out.append(tuple(row[x]))
            i += 1
    return out, w, h

def evaluate(path, claim=None, against=()):
    """Retorna (problems, report). Funcao pura o suficiente para self-check."""
    problems = []
    report = {"screenshot": path, "claim": claim}
    if not os.path.isfile(path):
        return [f"captura inexistente: {path}"], report
    try:
        pixels, w, h = _sample_pixels(path)
    except (PngError, OSError) as e:
        return [f"PNG ilegivel: {e}"], report

    report["sha256"] = sha256_file(path)
    report["width"], report["height"] = w, h

    # 1. informativa (variancia de luma) — reusa o detector ja provado
    from capture_evidence import image_informative
    ok_var, detail = image_informative(path, min_variance=MIN_VARIANCE)
    report["informative"] = ok_var
    report["variance_detail"] = detail
    if not ok_var:
        problems.append(f"captura sem informacao: {detail}")

    # 2. cor dominante
    counts = Counter(pixels)
    dom, dom_n = counts.most_common(1)[0]
    ratio = dom_n / len(pixels)
    report["dominant_color"] = list(dom)
    report["dominant_ratio"] = round(ratio, 4)
    if ratio > DOMINANT_RATIO_MAX:
        problems.append(f"cor dominante ocupa {ratio:.3%} da tela "
                        f"(max {DOMINANT_RATIO_MAX:.1%}) — tela praticamente lisa")

    # 2b. captura nao recortada (desktop inteiro)
    report["uncropped_desktop"] = (w * h) >= DESKTOP_PIXELS
    if report["uncropped_desktop"]:
        problems.append(
            f"captura de {w}x{h} = desktop inteiro, nao a janela do emulador — "
            "o viewport vira fracao minuscula da imagem; recorte a janela "
            "(capture_evidence.py captura a janela ativa)")

    # 3. conformidade de paleta (origem SMS)
    conf, _ = palette_conformance(pixels)
    report["palette_conformance"] = round(conf, 4)
    report["distinct_colors"] = len(counts)
    if conf < PALETTE_CONFORMANCE_MIN and not report["uncropped_desktop"]:
        problems.append(
            f"conformidade de paleta {conf:.1%} < {PALETTE_CONFORMANCE_MIN:.0%} — "
            "cores fora da paleta mestra 6-bit; isto nao parece captura de "
            "Master System (mockup/render/foto?)")

    # 4. anti-reuso
    reused = []
    for other in against:
        if os.path.isfile(other) and sha256_file(other) == report["sha256"]:
            reused.append(other)
    report["reused_from"] = reused
    if reused:
        problems.append(f"captura IDENTICA a evidencia ja usada: {', '.join(reused)} "
                        "— mesma imagem nao sustenta dois claims distintos")

    # 5. escopo de claim
    report["does_not_prove"] = NEVER_PROVEN_BY_SCREENSHOT
    if claim in NEVER_PROVEN_BY_SCREENSHOT:
        problems.append(f"claim '{claim}' invalido por screenshot: "
                        f"{NEVER_PROVEN_BY_SCREENSHOT[claim]}")
    report["semantic_capture_valid"] = not problems
    return problems, report

def _self_check():
    import tempfile, shutil
    from png_io import write_png_rgb
    d = tempfile.mkdtemp(prefix="smsssg_")
    try:
        W = H = 64
        def rows_from(fn):
            return [[fn(x, y) for x in range(W)] for y in range(H)]

        # APROVA: xadrez de cores de contrato (alta variancia, paleta valida)
        good = os.path.join(d, "good.png")
        write_png_rgb(good, W, H, rows_from(
            lambda x, y: (255, 255, 255) if (x // 8 + y // 8) % 2 else (0, 0, 170)))
        p, r = evaluate(good)
        assert not p, f"captura valida nao deveria reprovar: {p}"
        assert r["semantic_capture_valid"]

        # REPROVA: cores fora da paleta mestra (mockup/foto)
        bad_pal = os.path.join(d, "mockup.png")
        write_png_rgb(bad_pal, W, H, rows_from(
            lambda x, y: (17, 200, 133) if (x // 8 + y // 8) % 2 else (211, 47, 99)))
        p, _ = evaluate(bad_pal)
        assert any("conformidade de paleta" in x for x in p), \
            f"faltou reprovar cor fora da paleta mestra: {p}"

        # REPROVA: reuso da mesma imagem para outro claim
        copy = os.path.join(d, "copia.png")
        shutil.copyfile(good, copy)
        p, _ = evaluate(good, against=[copy])
        assert any("IDENTICA" in x for x in p), f"faltou pegar reuso: {p}"

        # REPROVA: claim que screenshot nao sustenta
        p, _ = evaluate(good, claim="fps_constante")
        assert any("fps_constante" in x for x in p), f"faltou barrar claim de fps: {p}"
        p, _ = evaluate(good, claim="gameplay")
        assert any("gameplay" in x for x in p), "faltou barrar claim de gameplay"

        # REPROVA: captura de desktop inteiro (limiar rebaixado para o teste)
        global DESKTOP_PIXELS
        original = DESKTOP_PIXELS
        try:
            DESKTOP_PIXELS = W * H       # a fixture 'good' passa a contar como desktop
            p, _ = evaluate(good)
            assert any("desktop inteiro" in x for x in p), \
                f"faltou reprovar captura nao recortada: {p}"
        finally:
            DESKTOP_PIXELS = original

        # REPROVA: tela praticamente lisa
        flat = os.path.join(d, "flat.png")
        write_png_rgb(flat, W, H, rows_from(lambda x, y: (0, 0, 0)))
        p, _ = evaluate(flat)
        assert p, "tela lisa deveria reprovar"
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print("[SELF-CHECK OK] screenshot_semantic_gate (reprova cor fora da paleta "
          "mestra, reuso de captura, claim que screenshot nao prova e tela lisa)")
    return 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("shot", nargs="?")
    ap.add_argument("--claim", help="o que a captura pretende provar")
    ap.add_argument("--against", nargs="*", default=[],
                    help="capturas ja usadas em outros claims (anti-reuso)")
    ap.add_argument("--json")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()

    if a.self_check:
        return _self_check()
    if not a.shot:
        print("[FAIL] informe a captura (ou use --self-check)", file=sys.stderr)
        return 3

    problems, report = evaluate(a.shot, a.claim, a.against)
    if a.json:
        json.dump({"problems": problems, **report}, open(a.json, "w"), indent=2)
    if problems:
        for p in problems:
            print(f"[FAIL] {p}")
        return 1
    print(f"[PASS] captura semanticamente valida "
          f"(paleta {report['palette_conformance']:.1%}, "
          f"{report['distinct_colors']} cores, dominante "
          f"{report['dominant_ratio']:.1%})")
    print("       NAO prova por si: gameplay, fps, audio, orcamento.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
