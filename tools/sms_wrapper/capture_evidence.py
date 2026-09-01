#!/usr/bin/env python3
"""Gate EVIDENCIA — boot no emulador Emulicious + captura de janela verificada.

Cadeia real (nada simulado):
  1. localiza Emulicious.jar (emulators.json ou layout padrao)
  2. roda a ROM: java -jar Emulicious.jar -remotedebug 4901 rom.sms
  3. fecha dialogos de update, foca a janela principal
  4. captura a janela via spectacle -a (KDE/Wayland; DISPLAY herdado)
  5. detector de imagem vazia reprova capturas sem informacao
  6. escreve bundle emulator_evidence_v1 e encerra o emulador

NOTA HONESTA (licao L005): openMSX foi avaliado e NAO suporta Master System;
o adapter anterior (-machine sms) era especulacao e foi removido.

LIMITACOES DO HOST (L010, 2026-08-30) — captura do frame VIVO do jogo:
  1. DAP readbyte/readword retorna '$0' para QUALQUER endereco (até 1+1 -> $0):
     o avaliador do contexto 'repl' nao avalia de verdade -> NAO usar p/ estado.
  2. import -window <canvas> congela no frame X inicial (render via Java/OpenGL
     em camada nao-pixmap): 3 capturas = hash identico. NAO reflete o estado vivo.
  3. spectacle -a / -f capturam o compositor: janela do jogo misturada com
     interface (contaminacao de cor nas bordas) e foco via windowactivate oscila.
  Consequencia: a LOGICA de vitoria e a RENDERIZACAO estao provadas por outros
  canais (simulacao exata + capturas 283x282), mas o FRAME especifico de um
  estado transitorio (VITORIA) nao e capturavel de forma confiavel neste host.
  Proximo passo: screenshot NATIVO do Emulicious (tecla F12 configurada) que
  grava o framebuffer do canvas direto em disco.

Uso:
  capture_evidence.py --project <dir> --rom <rom.sms> [--out nome]
  capture_evidence.py --check-image <png>     # so valida captura
  capture_evidence.py --self-check

Exit: 0 evidencia ok | 1 captura invalida | 2 ambiente ausente | 3 uso
"""
import sys, os, json, argparse, subprocess, shutil, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from png_io import read_png_luma_samples, read_png_rgb, png_size, PngError

HERE = os.path.dirname(os.path.abspath(__file__))
EMU_JSON = os.path.normpath(os.path.join(HERE, "..", "emuladores", "emulators.json"))
DEFAULT_JAR = os.path.normpath(os.path.join(HERE, "..", "emuladores",
                                            "emulicious", "Emulicious.jar"))

def resolve_jar():
    cfg = {}
    if os.path.exists(EMU_JSON):
        try:
            cfg = json.load(open(EMU_JSON))
        except json.JSONDecodeError:
            cfg = {}
    cand = cfg.get("emulicious_jar") or DEFAULT_JAR
    if not os.path.isabs(cand) and not os.path.exists(cand):
        # relativo no emulators.json -> resolver contra a raiz do workspace
        cand = os.path.normpath(os.path.join(HERE, "..", "..", cand))
    return cand if os.path.exists(cand) else None

def _run(cmd, timeout=30):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (subprocess.TimeoutExpired, OSError):
        return None

def _main_window_id():
    """Janela cujo nome e exatamente 'Emulicious' (ignora dialogos)."""
    r = _run(["xdotool", "search", "--name", "Emulicious"])
    if not r or r.returncode != 0:
        return None
    ids = [x.strip() for x in r.stdout.splitlines() if x.strip().isdigit()]
    for i in ids:
        n = _run(["xdotool", "getwindowname", i])
        if n and n.stdout.strip() == "Emulicious":
            return i
    return None

# Acima disto a "captura" e a tela inteira, nao a janela do emulador (L012).
DESKTOP_PIXELS = 1_500_000

def image_informative(path, min_variance=40.0, box=None):
    """Captura valida tem variacao real de LUMA (tela branca/preta lisa reprova)."""
    try:
        vals = read_png_luma_samples(path, box=box)
    except PngError:
        return False, f"{path}: PNG ilegivel"
    n = len(vals)
    if not n:
        return False, "imagem vazia"
    mean = sum(vals) / n
    var = sum((v - mean) ** 2 for v in vals) / n
    return var >= min_variance, f"variancia de luma={var:.1f} (min {min_variance})"

def viewport_box(path):
    """Metade central da imagem = viewport do jogo dentro da janela do emulador."""
    w, h = png_size(path)
    return (w // 4, h // 4, (3 * w) // 4, (3 * h) // 4)

def _luma_grid(path, box):
    from png_io import PngError as _E
    vals = read_png_luma_samples(path, box=box)   # pode lancar
    return vals

def viewport_diff(path_a, path_b):
    """Fracao de amostras de luma do viewport que mudou (>16 níveis)."""
    box = viewport_box(path_a)
    wa, ha = png_size(path_a); wb, hb = png_size(path_b)
    if (wa, ha) != (wb, hb):
        return 0.0
    try:
        va = _luma_grid(path_a, box)
        vb = _luma_grid(path_b, box)
    except PngError:
        return 0.0
    if len(va) != len(vb):
        return 0.0
    changed = sum(1 for x, y in zip(va, vb) if abs(x - y) > 16)
    return changed / max(1, len(va))

def press_keys(window_id, spec):
    """Executa spec 'Tecla=ms,Tecla=ms' via xdotool na janela focada.
    Retorna lista [(tecla, ms)] executada."""
    done = []
    for step in [s.strip() for s in spec.split(",") if s.strip()]:
        key, _, ms = step.partition("=")
        ms = int(ms or 400)
        _run(["xdotool", "windowactivate", str(window_id)])
        time.sleep(0.3)
        _run(["xdotool", "keydown", key], timeout=max(10, ms // 1000 + 10))
        time.sleep(ms / 1000.0)
        _run(["xdotool", "keyup", key])
        done.append((key, ms))
    return done



def largest_sprite_block(path, min_px=25):
    """Maior aglomerado conexo de cor saturada na area de jogo -> (n, x0, x1, y0, y1).

    Serve para medir DESLOCAMENTO do objeto controlado, em vez de "quanto da tela
    mudou". A metrica global de luma nao distingue o jogador obedecendo de um
    inimigo caindo, de uma morte, ou (antes do L012) do desktop do usuario.
    """
    try:
        w, h, rows = read_png_rgb(path)
    except (PngError, OSError):
        return None
    y_ini = int(h * 0.28)                      # abaixo da barra de titulo/HUD
    pts = {(x, y) for y in range(y_ini, h - 8) for x in range(12, w - 12)
           if max(rows[y][x]) - min(rows[y][x]) > 60 and max(rows[y][x]) > 110}
    seen, best = set(), None
    for pt in pts:
        if pt in seen:
            continue
        stack, comp = [pt], []
        while stack:
            c = stack.pop()
            if c in seen or c not in pts:
                continue
            seen.add(c); comp.append(c)
            x, y = c
            stack += [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]
        if len(comp) < min_px:
            continue
        xs = [a for a, _ in comp]; ys = [b for _, b in comp]
        bw, bh = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
        # Tem que ter FORMA DE SPRITE: colunas de estrelas e bordas de janela
        # formam faixas finas e altissimas e sequestravam a medicao.
        if not (6 <= bw <= 40 and 6 <= bh <= 40):
            continue
        if max(bw, bh) > 3 * min(bw, bh):
            continue
        if best is None or len(comp) > best[0]:
            best = (len(comp), min(xs), max(xs), min(ys), max(ys))
    return best

def _shoot_window(shot, wid, tries=4):
    """Captura a JANELA do emulador, provando pelo tamanho que nao pegou o desktop.

    L012: `spectacle -a` fotografa a janela ATIVA. Se o emulador perde o foco
    (dialogo, outra app, instancia zumbi), a "evidencia" vira um screenshot do
    desktop do usuario — que passa no detector de vacuidade e pode conter
    conteudo pessoal. Aqui isso e detectado, o arquivo e descartado e a captura
    e refeita depois de reativar a janela.
    """
    for attempt in range(tries):
        _run(["xdotool", "windowactivate", str(wid)])
        time.sleep(1.2 if attempt == 0 else 2.0)
        if os.path.exists(shot):
            os.remove(shot)
        r = _run(["spectacle", "-a", "-b", "-n", "-o", shot], timeout=60)
        if not os.path.exists(shot):
            continue
        try:
            w, h = png_size(shot)
        except (PngError, OSError):
            continue
        if w * h < DESKTOP_PIXELS:
            return True, (w, h)
        os.remove(shot)          # desktop: descarta (pode ter conteudo pessoal)
    return False, None

def capture(project, rom, out_name="evidence", keep=False, settle_frames=300,
            press_spec=None):
    jar = resolve_jar()
    if not jar:
        print("[FAIL_AMBIENTE] Emulicious.jar nao encontrado. Instale em "
              "tools/emuladores/emulicious/ ou registre 'emulicious_jar' em "
              "tools/emuladores/emulators.json. Gate NAO simula evidencia.")
        return 2
    missing = [t for t in ("java", "xdotool", "spectacle") if not shutil.which(t)]
    if missing:
        print(f"[FAIL_AMBIENTE] ferramentas ausentes: {', '.join(missing)}")
        return 2
    # L012: com outra instancia viva, xdotool acha a janela errada e o
    # spectacle -a captura a janela ATIVA (ja capturou o desktop do usuario).
    stale = subprocess.run(["pgrep", "-f", "Emulicious.jar"],
                           capture_output=True, text=True)
    if stale.returncode == 0 and stale.stdout.strip():
        print("[FAIL_AMBIENTE] ja existe Emulicious rodando (pid "
              f"{', '.join(stale.stdout.split())}). Encerre antes: "
              "pkill -f Emulicious.jar. Captura com instancia zumbi pega a "
              "janela errada e vira evidencia falsa (L012).")
        return 2
    out_dir = os.path.join(project, "out", "evidence")
    os.makedirs(out_dir, exist_ok=True)
    shot = os.path.join(out_dir, f"{out_name}.png")
    log_path = os.path.join(out_dir, f"{out_name}_emu.log")
    logf = open(log_path, "w")
    # settle: frames de jogo antes da captura (~5s a 60fps)
    proc = subprocess.Popen(
        ["java", "-jar", jar, "-remotedebug", "4901", os.path.abspath(rom)],
        stdout=logf, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        wid = None
        for _ in range(40):                      # ~20s esperando janela
            time.sleep(0.5)
            if proc.poll() is not None:
                break
            r = _run(["xdotool", "search", "--name", "Update Behaviour"])
            if r and r.returncode == 0:          # dialogo de update atrapalha foco
                for d in r.stdout.split():
                    _run(["xdotool", "windowclose", d.strip()])
            wid = _main_window_id()
            if wid:
                time.sleep(max(0.0, settle_frames / 60.0))
                break
        if not wid or proc.poll() is not None:
            print(f"[FAIL] emulador nao abriu janela (log: {log_path})")
            return 1
        ok_win, dim = _shoot_window(shot, wid)
        if not ok_win:
            print("[FAIL] nao foi possivel capturar a JANELA do emulador (so o "
                  "desktop). Arquivos descartados — podem conter conteudo "
                  "pessoal. Verifique foco/instancias (L012).")
            return 1
        ok, why = image_informative(shot)
        ok_vp, why_vp = image_informative(shot, box=viewport_box(shot))
        informative = ok and ok_vp
        bundle = {
            "project": os.path.basename(os.path.abspath(project)),
            "rom": rom,
            "screenshot": shot,
            "informative": informative,
            "detail": f"janela: {why} | viewport central: {why_vp}",
            "tool": "emulicious-2026-03-27+xdotool+spectacle",
            "chain_of_custody": [
                f"launch: java -jar {os.path.basename(jar)} -remotedebug 4901",
                "window: xdotool search/activate 'Emulicious'",
                "capture: spectacle -a (janela ativa)",
                "check: luma da janela INTEIRA e do VIEWPORT CENTRAL",
            ],
        }
        json.dump(bundle, open(os.path.join(out_dir, f"{out_name}.json"), "w"),
                  indent=2)
        if not ok:
            print(f"[FAIL] captura sem informacao ({why}) — tela branca/vazia?")
            return 1
        if not ok_vp:
            print(f"[FAIL] viewport central sem informacao ({why_vp}) — "
                  "ROM nao renderiza? Janela sem o jogo em foco?")
            return 1
        print(f"[PASS] evidencia registrada: {shot}")
        print(f"       janela {why} | viewport {why_vp}")
        # ---- modo gameplay: input script + diffs por passo -----------------
        if press_spec:
            steps = []
            prev = shot
            # o sprite pode sumir em frames de flash (invulnerabilidade):
            # compara sempre contra a ULTIMA posicao conhecida, nao contra None.
            last_blk = largest_sprite_block(shot)
            for i, (key, ms) in enumerate(press_keys(wid, press_spec), 1):
                time.sleep(0.5)
                step_shot = os.path.join(out_dir, f"{out_name}_step{i}.png")
                # L012: passo tambem precisa provar que fotografou a JANELA.
                # Era exatamente aqui que o desktop vazava: a comparacao entre
                # dois screenshots de desktop dava "interacao provada" medindo
                # a area de trabalho do usuario mudando, nao o jogo.
                ok_step, _ = _shoot_window(step_shot, wid)
                if not ok_step:
                    print(f"[FAIL] passo {i}: so foi possivel capturar o desktop, "
                          "nao a janela do emulador (L012). Descartado.")
                    return 1
                frac = viewport_diff(prev, step_shot)
                blk = largest_sprite_block(step_shot)
                dx = dy = None
                if blk and last_blk:
                    dx = ((blk[1] + blk[2]) // 2) - ((last_blk[1] + last_blk[2]) // 2)
                    dy = ((blk[3] + blk[4]) // 2) - ((last_blk[3] + last_blk[4]) // 2)
                if blk:
                    last_blk = blk
                steps.append({"key": key, "ms": ms, "shot": step_shot,
                              "viewport_changed": round(frac, 4),
                              "sprite_bbox": list(blk) if blk else None,
                              "sprite_dx": dx, "sprite_dy": dy})
                prev = step_shot
            # Sinal FORTE: o objeto controlado se deslocou (>=8px = um tile).
            # Sinal fraco: fracao da tela mudou — nao distingue jogador obedecendo
            # de inimigo caindo ou de morte (§28). Por isso o deslocamento manda.
            moved_sprite = any((s.get("sprite_dx") or 0) != 0 and
                               abs(s["sprite_dx"]) >= 8 for s in steps)
            moved = moved_sprite or any(s["viewport_changed"] >= 0.02 for s in steps)
            bundle = json.load(open(os.path.join(out_dir, f"{out_name}.json")))
            bundle["gameplay"] = {"press_script": press_spec, "steps": steps,
                                  "sprite_displacement_proven": moved_sprite,
                                  "interaction_proven": moved}
            json.dump(bundle, open(os.path.join(out_dir, f"{out_name}.json"), "w"),
                      indent=2)
            if not moved:
                print("[FAIL] interacao nao provada: nenhum passo mudou o "
                      "viewport >=2%. Mapeamento de teclas do emulador confere?")
                return 1
            for s in steps:
                print(f"       [{s['key']}={s['ms']}ms] viewport mudou "
                      f"{s['viewport_changed']*100:.1f}%")
            print("[PASS] GAMEPLAY provado por observacao (input -> mudanca)")
        return 0
    finally:
        if not keep and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
        logf.close()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    ap.add_argument("--rom")
    ap.add_argument("--frames", type=int, default=300,
                    help="frames de jogo antes da captura (default 300)")
    ap.add_argument("--out", default="evidence")
    ap.add_argument("--keep", action="store_true",
                    help="nao encerrar o emulador apos a captura")
    ap.add_argument("--press", default=None,
                    help="script de input 'Right=1500,Down=800' p/ modo GAMEPLAY")
    ap.add_argument("--check-image")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.self_check:
        import tempfile
        from png_io import write_indexed_png
        d = tempfile.mkdtemp(prefix="smsev_")
        blank = os.path.join(d, "blank.png")
        write_indexed_png(blank, 32, 24, [(255, 255, 255)], [bytes([0] * 32)] * 24)
        ok, _ = image_informative(blank)
        assert not ok, "captura branca deveria ser reprovada"
        noisy = os.path.join(d, "noisy.png")
        rows = [bytes([(i + j) & 1 for j in range(64)]) for i in range(48)]
        write_indexed_png(noisy, 64, 48, [(0, 0, 0), (255, 255, 255)], rows)
        ok2, _ = image_informative(noisy)
        assert ok2, "captura com padrao deveria passar"
        shutil.rmtree(d)
        print("[SELF-CHECK OK] evidence (detector de imagem vazia)")
        return 0
    if args.check_image:
        ok, why = image_informative(args.check_image)
        print(("[PASS] " if ok else "[FAIL] ") + why)
        return 0 if ok else 1
    if not args.rom:
        print("[FAIL] --rom obrigatorio (ou use --check-image / --self-check)",
              file=sys.stderr)
        return 3
    sys.exit(capture(args.project, args.rom, args.out, args.keep, args.frames,
                     args.press))

if __name__ == "__main__":
    sys.exit(main())
