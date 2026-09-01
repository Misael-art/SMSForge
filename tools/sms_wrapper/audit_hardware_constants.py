#!/usr/bin/env python3
"""audit_hardware_constants.py — numero de outro console nao passa por lei do SMS.

L001 disse que portar metodologia exige RE-DERIVAR os limites do hardware alvo.
A licao recorreu duas vezes depois de escrita:
  - L006: a matriz afirmava sprite "8x8 ou 16x16" (SMS e 8x8 ou 8x16) e custou
    dias de sprite invisivel;
  - L003: a matriz afirmava "X+32" e "early clock 32px" (numeros do Mega Drive,
    onde o offset de sprite e 128) — refutados em emulador.

Nos dois casos o defeito tinha a mesma forma: **um NUMERO errado afirmado como
fato duro** num documento que nenhum gate lia. Este gate le.

Nao tenta adivinhar "contaminacao" por prosa (isso reprovaria as proprias notas
de correcao, que citam o Mega Drive de proposito). Ele confere as GRANDEZAS do
SMS contra uma tabela canonica: onde o documento afirmar um numero para uma
grandeza conhecida, o numero tem que ser o do Master System.

Uso: audit_hardware_constants.py [--root <workspace>] [--json <out>] [--self-check]
Exit: 0 coerente | 1 numero de outro hardware | 3 uso
"""
import sys, os, re, json, glob, argparse

# Grandezas canonicas do Master System. Fonte: SMS_GLOBAL + headers devkitSMS;
# cada uma ja custou (ou quase custou) um bug quando trocada pela do MegaDrive.
CANON = [
    # (rotulo, regex com um grupo numerico, valor correto, valor tipico do MD)
    ("sprites por scanline",
     r"(\d+)\s*sprites?\s*(?:por|\/|na |numa )\s*(?:scanline|linha)", 8, 20),
    # Só a forma que declara CAPACIDADE. "4 entradas na SAT por entidade" e
    # afirmacao legitima sobre custo, nao sobre o limite — a regex larga
    # anterior reprovava isso e o >8 de "mais de 8 sprites/linha".
    ("capacidade da SAT",
     r"SAT\s*(?:tem|de|com|:|=)\s*(\d+)\s*(?:entradas|sprites)", 64, 80),
    ("VRAM em KB", r"VRAM\s*(?:=|:|de)?\s*(\d+)\s*KB", 16, 64),
    ("RAM em KB", r"\bRAM\s*(?:=|:|de)?\s*(\d+)\s*KB", 8, 64),
    ("subpaletas", r"(\d+)\s*subpaletas", 2, 4),
    ("largura da tela", r"(\d+)\s*[x×]\s*192", 256, 320),
]

# "DMA" so pode aparecer negado: o SMS nao tem DMA. Frases de negacao aceitas.
NEG_DMA = ("sem dma", "nao existe dma", "não existe dma", "nao ha dma",
           "não há dma", "inexistente", "não tem dma", "nao tem dma")

def _docs(root):
    pats = [os.path.join(root, "doc", "**", "*.md"),
            os.path.join(root, "tools", "sms_wrapper", ".agent", "**", "*.md"),
            os.path.join(root, "AGENTS.md")]
    out = []
    for p in pats:
        out += glob.glob(p, recursive=True)
    return sorted(set(out))

def check_text(texto, origem="<texto>"):
    problems = []
    linhas = texto.splitlines()
    for linha_n, linha in enumerate(linhas, 1):
        # Prosa em markdown quebra linha: a frase que marca "isto e uma lista de
        # fixtures REPROVADAS" pode estar 1-2 linhas acima do numero.
        ctx = " ".join(linhas[max(0, linha_n - 3):linha_n]).lower()
        low = linha.lower()
        for rotulo, rx, correto, md in CANON:
            for m in re.finditer(rx, linha, re.I):
                val = int(m.group(1))
                if val == correto:
                    continue
                # ">8 sprites/linha" e "mais de 8" afirmam o limite CORRETO
                antes = linha[max(0, m.start() - 12):m.start()].lower()
                # So ">N" / "mais de N" AFIRMAM o limite correto (N e o teto).
                # "maximo de N" afirma que o teto E N — se N esta errado, e erro.
                if any(t in antes for t in (">", "≥", "mais de", "acima de",
                                            "excesso")):
                    continue
                # descricao de caso de TESTE (o gate reprova 9 numa scanline)
                if any(w in ctx for w in ("reprov", "rejeit", "fixture",
                                          "selftest", "invalid")):
                    continue
                # linha que declara a correcao/refutacao pode citar o numero errado
                if any(w in low for w in ("corrigido", "refutad", "dizia",
                                          "heranca", "herança", "mega drive",
                                          "megadrive", "errado")):
                    continue
                extra = " (numero do Mega Drive)" if val == md else ""
                problems.append(
                    f"{os.path.basename(origem)}:{linha_n}: {rotulo} = {val}, "
                    f"mas no Master System e {correto}{extra}")
        # "dma" como SUBSTRING casava dentro de "Roadmap" — 3 falsos positivos.
        # E citar DMA para negar/comparar e legitimo. So reprova quando o texto
        # MANDA USAR DMA, que e a falha real (instrucao de outro console).
        if re.search(r"\b(?:via|use|usar|usando|com|por|atraves de)\s+DMA\b",
                     linha, re.I) and not any(n in low for n in NEG_DMA):
            problems.append(
                f"{os.path.basename(origem)}:{linha_n}: manda usar DMA — "
                "o VDP do Master System NAO tem DMA (a janela de VBlank e o "
                "orcamento)")
    return problems

def audit(root):
    problems = []
    for f in _docs(root):
        try:
            problems += check_text(open(f, encoding="utf-8", errors="replace").read(), f)
        except OSError as e:
            problems.append(f"{f}: ilegivel ({e})")
    return problems

def _self_check():
    # REPROVA numeros do Mega Drive afirmados como lei do SMS
    p = check_text("Maximo de 20 sprites por scanline no modo H40.")
    assert any("Mega Drive" in x for x in p), f"faltou pegar 20 sprites/scanline: {p}"
    p = check_text("A SAT tem 80 entradas.")
    assert p, "faltou pegar SAT com 80 entradas"
    p = check_text("VRAM = 64 KB disponiveis.")
    assert p, "faltou pegar VRAM de 64KB"
    p = check_text("Use 4 subpaletas de 16 cores.")
    assert p, "faltou pegar 4 subpaletas"
    p = check_text("Resolucao 320x192.")
    assert p, "faltou pegar largura 320"
    p = check_text("Transferir tiles via DMA no vblank.")
    assert any("DMA" in x for x in p), "faltou pegar DMA afirmado"
    p = check_text("SAT tem 80 entradas.")
    assert p, "faltou pegar capacidade de SAT errada"

    # APROVA os numeros corretos do SMS
    assert not check_text("Maximo 8 sprites por scanline; SAT com 64 entradas.")
    assert not check_text("VRAM = 16 KB, RAM = 8 KB, 2 subpaletas, tela 256x192.")
    assert not check_text("Nao existe DMA: toda transferencia cabe no VBlank.")
    assert not check_text("sem DMA no Master System")
    # REGRESSOES REAIS encontradas ao rodar no acervo (2026-09-01):
    assert not check_text("> **Roadmap:** 02_roadmap_waves.md"), \
        "'dma' dentro de 'Roadmap' nao pode reprovar"
    assert not check_text("| Sprites/scanline | >8 sprites/linha, >64 na SAT |"), \
        "'>8 sprites/linha' afirma o limite CORRETO"
    assert not check_text("Metasprite 16x16 = 4 entradas na SAT por entidade."), \
        "custo por entidade nao e capacidade da SAT"
    assert not check_text("| DMA queue | transferencias manuais dentro do VBlank |"), \
        "citar DMA para comparar/negar e legitimo"
    assert not check_text("gate reprovou 9 sprites numa scanline"), \
        "descricao de caso de teste nao e afirmacao de lei"
    # caso real do acervo: a frase que marca a lista esta 2 linhas acima
    assert not check_text("Cada gate aprovou fixture valida E reprovou a invalida:\n"
                          "grid fora de 8x8; sprite 12x12;\n"
                          "9 sprites numa scanline; SAT >64;"), \
        "lista de fixtures reprovadas quebrada em linhas nao e afirmacao de lei"
    # APROVA a linha que documenta a correcao citando o numero errado
    assert not check_text("Corrigido: dizia 20 sprites por scanline (Mega Drive).")
    print("[SELF-CHECK OK] hardware_constants (reprova numero de outro console "
          "afirmado como lei; aceita os do SMS e as notas de correcao)")
    return 0

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.normpath(os.path.join(here, "..", "..")))
    ap.add_argument("--json")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        return _self_check()
    problems = audit(a.root)
    if a.json:
        json.dump({"problems": problems, "clean": not problems},
                  open(a.json, "w"), indent=2)
    if problems:
        for p in problems:
            print(f"[FAIL] {p}")
        print(f"[FAIL] {len(problems)} grandeza(s) com numero de outro hardware. "
              "Re-derive do Master System (L001).")
        return 1
    print("[PASS] grandezas do SMS coerentes na doutrina")
    return 0

if __name__ == "__main__":
    sys.exit(main())
