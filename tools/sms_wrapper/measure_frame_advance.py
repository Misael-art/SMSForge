#!/usr/bin/env python3
"""measure_frame_advance.py — o LOOP DA ROM avancou? (nao "o host aguentou")

Licao L013. O `measure_fps.py` le o titulo da janela ("Emulicious - 100%
(60 fps)"). Isso e a velocidade de EMULACAO: quanto o host conseguiu
processar. Uma ROM parada num `while(1){}` mantem o titulo em 60 fps, porque
o Z80 emulado continua girando a 3.58MHz — so nao esta desenhando nada novo.
O eixo `fps_constante` fechado so pelo titulo prova o emulador, nao o jogo.

A L013 ja tinha proposto o instrumento certo (contador na tela) e ele foi
substituido pelo mais fraco. Aqui ele volta, sem a parte fragil:

  A L013 dizia "OCR de digitos hex". Ler o glifo exige conhecer a fonte
  (SMS_autoSetUpTextRenderer traz a do SMSlib, que so existe dentro do
  SMSlib.lib). Nao e preciso: para medir TAXA basta contar QUANTAS VEZES o
  bloco 8x8 do digito MUDOU. Nao importa que digito e — importa que trocou.

  O HUD da arena_nocturna imprime tres nibbles de g_frame (hud.c:80-86):
      (29,0) = (g_frame>>7)&0xF   -> troca a cada 128 frames
      (30,0) = (g_frame>>3)&0xF   -> troca a cada   8 frames
      (31,0) =  g_frame    &0xF   -> troca a cada   1 frame

  fps = (n_trocas - 1) * periodo_do_digito / (t_ultima_troca - t_primeira)

  Medir entre a PRIMEIRA e a ULTIMA troca, e nao sobre a janela inteira,
  elimina a quantizacao de borda (a janela comeca e acaba no meio de um
  periodo). Com periodo 128 numa janela de 16s a borda vale +-8 fps — foi ela
  que fez uma ROM de 60 fps ser medida como 63.

Anti-aliasing (Nyquist): amostrar mais rapido que a troca, se nao transicoes
se perdem e o fps sai BAIXO (nunca alto — o erro e conservador). O digito de
128 frames troca a cada ~2.1s a 60fps. A folga e conferida sobre o intervalo
MEDIDO, nunca sobre o pedido na linha de comando.

Uso: measure_frame_advance.py --rom X.sms [--cell 29,0] [--period 128]
                              [--seconds 12] [-o saida.json] [--self-check]
Exit: 0 avanco provado | 1 ROM nao avancou / fora da faixa | 2 ambiente
"""
import sys, os, json, time, argparse, subprocess, shutil, hashlib, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from png_io import read_png_rgb, PngError            # noqa: E402
import capture_evidence as CE                        # noqa: E402
from emulator_session import require_no_stale        # noqa: E402

TILE = 8
MIN_OVERSAMPLE = 3.0     # amostras por troca do digito; abaixo disso nao mede
# Um tile de texto tem 2 tons (fundo + traco); o backdrop piscando pode somar
# mais um. Acima disso ha OUTRA coisa sobre a celula — no laboratorio, um
# inimigo caindo (ex[]=190 passa por cima da coluna 24). A amostra e
# descartada em vez de virar "avanco do contador": descartar so pode fazer o
# fps medido sair BAIXO (o erro e conservador), nunca inflado.
MAX_CELL_COLORS = 4
# Amostras consecutivas para um estado ser considerado real (anti-rasgo).
MIN_RUN = 2
# Estados completos minimos para a mediana significar alguma coisa.
MIN_STATES = 5
# Dispersao maxima em torno da mediana para o ritmo ser chamado de CONSTANTE.
TOLERANCIA = 0.10
FPS_MIN, FPS_MAX = 50, 60


def cell_signature(rows, x0, y0, col, row):
    """Assinatura do bloco 8x8 do tile (col,row) da area de jogo. PURA.

    `rows` e o formato de png_io.read_png_rgb: lista de linhas, cada linha uma
    lista de tuplas (r,g,b) — NAO bytes planos.

    Assina a FORMA do glifo, nao as cores. O laboratorio pisca a cor de fundo
    a cada 8 frames (main.c:219, SMS_setBackdropColor) e os pixels de cor 0 do
    tile deixam o backdrop aparecer. Um hash do RGB cru contava esse flash como
    troca do contador: 18 trocas em 25s onde 60fps dariam 11.7, resultando num
    "92 fps" que nao media coisa alguma.

    Binarizar por "este pixel e a cor dominante da celula?" e imune a isso: se
    o fundo inteiro muda de cor, ele continua sendo o dominante e a mascara nao
    se mexe. So a troca do desenho do digito muda a mascara.
    """
    px, py = x0 + col * TILE, y0 + row * TILE
    cells = [rows[py + dy][px + dx][:3]
             for dy in range(TILE) for dx in range(TILE)]
    if len(set(cells)) > MAX_CELL_COLORS:
        return None            # celula contaminada; amostra descartada
    modal = max(set(cells), key=cells.count)
    mask = bytes(1 if c != modal else 0 for c in cells)
    return hashlib.sha1(mask).hexdigest()[:12]


def count_transitions(signatures):
    """Quantas vezes a assinatura mudou em relacao a anterior. PURA."""
    return sum(1 for a, b in zip(signatures, signatures[1:]) if a != b)


def debounce(samples, min_run=MIN_RUN):
    """Descarta estados que duram menos que `min_run` amostras. PURA.

    `import` fotografa a janela enquanto o emulador repinta, entao de vez em
    quando o digito sai RASGADO: metade do glifo velho, metade do novo. Esse
    estado intermediario existe por 1 amostra e transforma uma troca real em
    duas, inflando o fps (media de 1.52s entre trocas onde o real e 2.13s ->
    "84 fps" numa ROM travada em SMS_waitForVBlank a 60Hz).

    Com sobreamostragem de ~24x um estado legitimo aparece em dezenas de
    amostras seguidas; um de 1 amostra e rasgo. Descartar so pode ATRASAR o
    reconhecimento de uma troca em uma amostra (~0.09s), nunca inventar uma.
    """
    out, i, n = [], 0, len(samples)
    while i < n:
        j = i
        while j < n and samples[j][1] == samples[i][1]:
            j += 1
        if (j - i) >= min_run:
            out.extend(samples[i:j])
        i = j
    return out


def transition_times(samples):
    """Instantes em que a assinatura mudou. samples = [(t, sig), ...]. PURA."""
    return [t for (_, a), (t, b) in zip(samples, samples[1:]) if a != b]


def state_durations(samples):
    """Duracao de cada estado COMPLETO do digito, em segundos. PURA.

    Um estado = intervalo em que a assinatura nao muda. Mede-se de inicio a
    inicio (nao de primeira a ultima amostra, que subestima em um intervalo de
    amostragem). O primeiro e o ultimo estado sao cortados pela janela de
    observacao e por isso NAO entram.
    """
    inicios = [samples[0][0]]
    for (_, a), (t, b) in zip(samples, samples[1:]):
        if a != b:
            inicios.append(t)
    if len(inicios) < 3:
        return []
    return [b - a for a, b in zip(inicios, inicios[1:])][1:]


def _median(v):
    v = sorted(v)
    n = len(v)
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2.0


def fps_from_transition_times(times, period_frames):
    """fps pelo INTERVALO entre a 1a e a ultima troca. PURA.

    Contar trocas e dividir pela janela total quantiza nas bordas: a janela
    comeca e termina no meio de um periodo, entao o resultado erra ate +-1
    troca (+-8 fps com periodo 128 numa janela de 16s) — foi o que produziu um
    "63 fps" numa ROM que roda a 60. Entre a primeira e a ultima troca, ao
    contrario, decorreram EXATAMENTE (n-1)*period frames. Sem borda, sem erro
    de arredondamento; sobra so a latencia de amostragem.
    """
    if len(times) < 2:
        return None
    span = times[-1] - times[0]
    if span <= 0:
        return None
    return round((len(times) - 1) * period_frames / span, 1)


def fps_from_transitions(transitions, period_frames, seconds):
    """fps = transicoes * frames_por_troca / segundos. PURA."""
    if seconds <= 0:
        return None
    return round(transitions * period_frames / seconds, 1)


def oversample_ok(interval_s, period_frames, fps_expected=60.0):
    """Amostragem respeita Nyquist com folga? PURA.

    `interval_s` tem de ser o intervalo MEDIDO, nao o pedido: cada captura leva
    ~1.5s (ativar janela + assentar), entao um --interval de 0.3s vira 1.5s na
    pratica. Checar o parametro em vez do realizado declarava folga de 7.1x
    onde a real era 1.4x.
    """
    if interval_s <= 0:
        return False, None
    troca_s = period_frames / fps_expected
    return (troca_s / interval_s) >= MIN_OVERSAMPLE, round(troca_s / interval_s, 1)


def verdict(samples, period_frames):
    """samples = [(t, assinatura), ...] em ordem cronologica.

    Usa a MEDIANA da duracao dos estados, nao a contagem de transicoes. Contar
    e dividir faz UM rasgo que sobreviva ao debounce contaminar todo o
    resultado (mediu-se 72 fps numa ROM travada em SMS_waitForVBlank a 60Hz).
    A mediana ignora outliers, e a dispersao em volta dela e exatamente o que o
    eixo se chama: fps CONSTANTE, nao fps medio.
    """
    brutas = len(samples)
    samples = debounce(samples)
    base = {"amostras": brutas, "amostras_estaveis": len(samples),
            "periodo_frames": period_frames, "fps_estimado": None,
            "sobreamostragem": None, "sobreamostragem_ok": False,
            "loop_da_rom_avancou": False, "aprovado": False}
    if len(samples) < 2:
        return {**base, "transicoes": 0, "estados_completos": 0}
    trans = count_transitions([x[1] for x in samples])
    span = samples[-1][0] - samples[0][0]
    interval = span / (len(samples) - 1)
    ok_ns, ratio = oversample_ok(interval, period_frames)
    dur = state_durations(samples)
    base.update({"transicoes": trans, "janela_s": round(span, 2),
                 "intervalo_medido_s": round(interval, 3),
                 "sobreamostragem": ratio, "sobreamostragem_ok": ok_ns,
                 "loop_da_rom_avancou": trans > 0,
                 "estados_completos": len(dur)})
    if len(dur) < MIN_STATES:
        base["motivo"] = (f"{len(dur)} estado(s) completo(s); "
                          f"{MIN_STATES} e o minimo para medir")
        return base
    # Passo 1: mediana bruta. Passo 2: um rasgo PARTE um estado em dois pedacos
    # curtos, e os pedacos puxam a mediana para baixo; descarta-se o que for
    # curto demais para ser um periodo e remediana-se. Estimar o periodo e
    # classificar artefato com o MESMO limiar seria circular — foi o erro da
    # primeira versao, que tolerava +-50% e depois media o desvio dentro
    # daquela mesma faixa.
    med0 = _median(dur)
    if med0 <= 0:
        return base
    inteiros = [d for d in dur if d >= 0.6 * med0] or dur
    med = _median(inteiros)
    if med <= 0:
        return base
    artefatos = [d for d in dur if abs(d - med) / med > TOLERANCIA]
    limite = max(1, len(dur) // 3)
    fps = round(period_frames / med, 1)
    base.update({
        "duracao_mediana_s": round(med, 3),
        "estados_fora_da_tolerancia": len(artefatos),
        "limite_de_artefatos": limite,
        "constante": len(artefatos) <= limite,
        "fps_estimado": fps,
        "aprovado": bool(trans > 0 and ok_ns and len(artefatos) <= limite
                         and FPS_MIN <= fps <= FPS_MAX),
    })
    return base


def self_check():
    # A fixture usa EXATAMENTE o formato de png_io.read_png_rgb (linhas de
    # tuplas rgb). Um self-check com bytes planos passava enquanto a ferramenta
    # estourava IndexError no PNG real — self-check calibrado no formato errado
    # nao e prova de nada (§20).
    w, h = 40, 24
    rows = [[(0, 0, 0)] * w for _ in range(h)]
    rows[9][8] = (255, 0, 0)                   # pixel em (8,9)
    a = cell_signature(rows, 0, 8, 1, 0)       # tile col=1,row=0 a partir de y0=8
    rows[9][8] = (0, 0, 0)
    b = cell_signature(rows, 0, 8, 1, 0)
    assert a != b, "assinatura tem de mudar quando o pixel do bloco muda"
    # bloco VIZINHO nao pode ser afetado -> nao esta lendo a area errada
    rows[9][8] = (255, 0, 0)
    c1 = cell_signature(rows, 0, 8, 2, 0)
    rows[9][8] = (0, 0, 0)
    assert c1 == cell_signature(rows, 0, 8, 2, 0), "bloco vizinho vazou"

    # INVARIANCIA AO FLASH DE BACKDROP: mesmo desenho sobre fundo de outra cor
    # tem de dar a MESMA assinatura, senao o piscar do fundo vira "avanco".
    def glyph(bg, fg):
        g = [[bg] * w for _ in range(h)]
        for (dx, dy) in ((1, 1), (2, 1), (1, 3)):
            g[8 + dy][8 + dx] = fg
        return g
    s_azul = cell_signature(glyph((0, 0, 40), (255, 255, 255)), 0, 8, 1, 0)
    s_verde = cell_signature(glyph((0, 60, 0), (255, 255, 255)), 0, 8, 1, 0)
    assert s_azul == s_verde, "troca de cor de fundo nao pode contar como troca"
    outro = [[(0, 0, 40)] * w for _ in range(h)]
    outro[8 + 5][8 + 5] = (255, 255, 255)
    assert cell_signature(outro, 0, 8, 1, 0) != s_azul, "glifo diferente tem de diferir"

    # CELULA CONTAMINADA (sprite por cima): amostra descartada, nao "avanco"
    sujo = [[(0, 0, 40)] * w for _ in range(h)]
    for k in range(6):
        sujo[8 + k][8 + k] = (10 * k, 200 - 9 * k, 30 + 7 * k)
    assert cell_signature(sujo, 0, 8, 1, 0) is None, \
        "celula com muitos tons tem de ser descartada, nao assinada"

    assert count_transitions(["a", "a", "b", "b", "c"]) == 2
    assert count_transitions(["a"]) == 0
    assert count_transitions([]) == 0

    def series(n_amostras, dt, period_s, t0=0.0):
        """Serie sintetica: assinatura troca a cada `period_s` segundos."""
        out = []
        for i in range(n_amostras):
            t = t0 + i * dt
            out.append((t, f"sig{int(t / period_s)}"))
        return out

    # 60 fps com digito de 128 frames -> troca a cada 2.1333s
    v = verdict(series(300, 0.09, 128 / 60.0), 128)
    assert v["aprovado"] and 59 <= v["fps_estimado"] <= 61, f"caso bom reprovou: {v}"
    assert v["constante"], f"ritmo regular tem de ser constante: {v}"

    # REPROVA: ROM congelada. O titulo diria 60fps; aqui nao ha troca nenhuma.
    v = verdict([(i * 0.09, "parado") for i in range(300)], 128)
    assert not v["aprovado"] and not v["loop_da_rom_avancou"], \
        "ROM sem avanco nao pode passar — e exatamente o caso que a L013 pega"

    # REPROVA: 30 fps (troca a cada 4.2667s)
    v = verdict(series(600, 0.09, 128 / 30.0), 128)
    assert v["loop_da_rom_avancou"] and 29 <= v["fps_estimado"] <= 31
    assert not v["aprovado"], f"30fps nao pode fechar o eixo: {v}"

    # REPROVA: amostragem sem folga de Nyquist (intervalo MEDIDO de 1.5s contra
    # troca de 2.13s = 1.4x). Era o caso real que se declarava 7.1x por olhar o
    # parametro pedido (0.3s) em vez do realizado.
    v = verdict(series(30, 1.5, 128 / 60.0), 128)
    assert not v["sobreamostragem_ok"] and not v["aprovado"], \
        f"folga de {v['sobreamostragem']}x nao pode fechar o eixo: {v}"

    # ANTI-RASGO: um estado intruso de 1 amostra nao pode virar 2 trocas
    limpo = series(300, 0.09, 128 / 60.0)
    sujo = list(limpo)
    sujo[40] = (sujo[40][0], "RASGO")
    sujo[150] = (sujo[150][0], "RASGO2")
    assert count_transitions([x[1] for x in sujo]) > \
           count_transitions([x[1] for x in limpo]), "fixture nao injetou rasgo"
    v = verdict(sujo, 128)
    assert 59 <= v["fps_estimado"] <= 61, f"rasgo contaminou o fps: {v}"

    # RASGO PERSISTENTE (2 amostras, sobrevive ao debounce): a mediana tem de
    # aguentar. Era este caso que fazia contar-e-dividir reportar 72 fps.
    sujo2 = list(limpo)
    for k in (60, 61, 200, 201):
        sujo2[k] = (sujo2[k][0], f"RASGO{k // 100}")
    v = verdict(sujo2, 128)
    assert 59 <= v["fps_estimado"] <= 61, f"mediana nao aguentou o rasgo: {v}"
    assert v["estados_fora_da_tolerancia"] >= 2, \
        f"os pedacos curtos tinham de ser marcados como artefato: {v}"
    bruto = fps_from_transitions(v["transicoes"], 128, v["janela_s"])
    assert abs(bruto - 60) > abs(v["fps_estimado"] - 60), \
        f"contar-e-dividir ({bruto}) deveria errar mais que a mediana ({v['fps_estimado']})"

    # REPROVA: ritmo IRREGULAR (fps medio na faixa, mas engasgando)
    irregular, t, flip = [], 0.0, 0
    for i in range(400):
        irregular.append((t, f"s{flip}"))
        t += 0.09
        if t > (1.2 if flip % 2 else 3.0):
            pass
    # serie explicita: estados alternando 1.2s e 3.0s (media ~2.1s = 60fps)
    irregular, t, k = [], 0.0, 0
    for k in range(14):
        dur = 1.2 if k % 2 else 3.0
        n = int(dur / 0.09)
        for j in range(n):
            irregular.append((t + j * 0.09, f"e{k}"))
        t += n * 0.09
    v = verdict(irregular, 128)
    assert not v["constante"] and not v["aprovado"], \
        f"ritmo irregular nao pode fechar um eixo chamado fps_CONSTANTE: {v}"

    ok, _ = oversample_ok(0.2, 128)
    assert ok, "0.2s contra troca de 2.1s tem de passar"

    print("[SELF-CHECK OK] measure_frame_advance (reprova ROM congelada que o "
          "titulo diria 60fps, reprova amostragem sem folga de Nyquist e "
          "reprova 30fps, amostragem sem folga e ritmo irregular; fps pela mediana "
          "das duracoes de estado, imune a rasgo de captura)")
    return 0


def run(rom, cell, period, seconds, interval, settle, out):
    jar = CE.resolve_jar()
    if not jar or not os.path.exists(jar):
        print("[FAIL_AMBIENTE] Emulicious.jar nao encontrado", file=sys.stderr)
        return 2
    if not shutil.which("xdotool") or not shutil.which("import"):
        print("[FAIL_AMBIENTE] xdotool/import ausentes", file=sys.stderr)
        return 2
    # L057: a busca de janela e por NOME. Com outra instancia viva, o marcador
    # medido pode ser o de outra ROM — e o resultado sai como taxa DESTA.
    if not require_no_stale(why="medicao de avanco de frame"):
        return 2
    col, row = cell
    tmp = tempfile.mkdtemp(prefix="frame_advance_")
    # O modo sem remote-debug permite que o Emulicious entre em turbo quando
    # a janela não está sendo acompanhada. Nesse estado o título mostra
    # centenas de fps e o marcador muda mais rápido que a captura; isso mede
    # o host, não o contrato VBlank do SMS. O mesmo lançamento usado pelo gate
    # de evidência fixa a execução normal em 50/60 Hz.
    proc = subprocess.Popen(
        ["java", "-jar", jar, "-remotedebug", "4901", "-set", "Update=0",
         os.path.abspath(rom)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        wid = None
        for _ in range(30):
            time.sleep(1.0)
            wid = CE._main_window_id()
            if wid:
                break
        if not wid:
            print("[FAIL_AMBIENTE] janela do emulador nao apareceu", file=sys.stderr)
            return 2
        time.sleep(3.0)                      # deixa a ROM sair do boot
        # Medir na geometria nativa do Emulicious. Redimensionar a janela cria
        # uma subjanela XCanvasPeer esticada e com letterbox; nesse modo não há
        # uma coordenada fixa do viewport para o HUD. A geometria nativa
        # observada é 256x217, com a canvas SMS 256x192 em (0,25), e já dá
        # sobreamostragem suficiente para o dígito de 128 frames.
        # Uma unica ativacao. O laco de amostragem NAO pode chamar
        # windowactivate a cada tiro: era isso que fazia o intervalo real ser
        # ~1.5s (folga de Nyquist de 1.4x) enquanto o parametro dizia 0.3s.
        # `import -window <id>` fotografa a janela pelo ID mesmo sem foco, e
        # por ser alvo-por-ID continua impossivel pegar o desktop (L007/L017).
        CE._run(["xdotool", "windowactivate", str(wid)])
        # O boot determinístico inclui title + warmup antes da atração. Sem
        # assentamento, os primeiros estados do marcador misturam title,
        # troca de name table e arena; a mediana então acusa um ritmo falso.
        # O tempo é explícito para que a evidência registre a condição de
        # observação, e não uma suposição escondida no código.
        time.sleep(max(0.0, settle))
        samples, descartadas = [], 0
        shot = os.path.join(tmp, "s.png")
        deadline = time.time() + seconds
        while time.time() < deadline:
            if os.path.exists(shot):
                os.remove(shot)
            r = CE._run(["import", "-window", str(wid), shot], timeout=20)
            t = time.time()
            if r and r.returncode == 0 and os.path.exists(shot):
                try:
                    w, h, rows = read_png_rgb(shot)
                    if w * h < CE.DESKTOP_PIXELS:
                        x0, y0, _, _ = CE.game_area(w, h)
                        sig = cell_signature(rows, x0, y0, col, row)
                        if sig is not None:
                            samples.append((t, sig))
                        else:
                            descartadas += 1
                except (PngError, OSError, IndexError):
                    pass
            if interval > 0:
                time.sleep(interval)
        if len(samples) < 2:
            print("[FAIL_AMBIENTE] captura nao produziu amostras suficientes",
                  file=sys.stderr)
            return 2
        v = verdict(samples, period)
        v.update({"rom": os.path.abspath(rom), "celula": [col, row],
                  "amostras_descartadas": descartadas,
                  "assentamento_s": settle})
        print(json.dumps(v, indent=2, ensure_ascii=False))
        if out:
            json.dump(v, open(out, "w"), indent=2, ensure_ascii=False)
        if not v["aprovado"]:
            print("[FAIL] avanco do loop da ROM nao provado", file=sys.stderr)
            return 1
        print(f"[OK] loop da ROM avancou: {v['transicoes']} trocas do digito, "
              f"fps={v['fps_estimado']}")
        return 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom")
    ap.add_argument("--cell", default="29,0",
                    help="tile (coluna,linha) do digito do contador")
    ap.add_argument("--period", type=int, default=128,
                    help="frames entre duas trocas daquele digito")
    ap.add_argument("--seconds", type=float, default=20.0)
    ap.add_argument("--interval", type=float, default=0.0,
                help="pausa extra entre tiros; 0 = tao rapido quanto o import permitir")
    ap.add_argument("--settle", type=float, default=10.0,
                    help="segundos de title/warmup antes da amostragem (default 10)")
    ap.add_argument("-o", "--out")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        return self_check()
    if not a.rom:
        print("[ERRO] --rom obrigatorio", file=sys.stderr)
        return 2
    col, row = (int(v) for v in a.cell.split(","))
    return run(a.rom, (col, row), a.period, a.seconds, a.interval, a.settle, a.out)


if __name__ == "__main__":
    sys.exit(main())
