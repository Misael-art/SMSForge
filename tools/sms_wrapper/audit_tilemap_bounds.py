#!/usr/bin/env python3
"""audit_tilemap_bounds.py — escrita na name table fora da area RENDERIZADA.

Licao L011: "VITORIA!" escrito na linha 26 nunca apareceu. Nao era bug de
fonte nem de paleta: XYtoADDR e aritmetica pura, sem checagem de limite.

    #define SMS_PNTAddress  0x3800
    #define XYtoADDR(x,y)   (SMS_PNTAddress|((((y)<<5)+(x))<<1))

A PNT ocupa 28 linhas x 32 colunas x 2 bytes = 0x700 -> 0x3800..0x3EFF.
O modo 192 linhas renderiza apenas as linhas 0..23. Daí duas falhas
diferentes que a lição tratava como uma:

  y em 24..27  -> INVISIVEL. Escreve na cauda nao renderizada da PNT.
                  Nada quebra, nada aparece. Foi este o caso da L011.
  y >= 28      -> CORROMPE. Ultrapassa 0x3EFF e cai em 0x3F00, que e a
                  SAT. Escrever "texto" ali reposiciona sprites.
  x >= 32      -> VAZA PARA A LINHA SEGUINTE. O <<5 nao satura; x=33 na
                  linha 3 e o mesmo endereco que x=1 na linha 4.

So julga coordenada LITERAL (ou #define que resolve para literal). Coordenada
vinda de variavel nao e decidivel estaticamente e e reportada como nao provada,
nunca como aprovada.

Uso: audit_tilemap_bounds.py <arquivo.c|dir> [...] [--self-check]
Exit: 0 aprovado | 1 reprovado | 2 erro de uso
"""
import sys, os, re, argparse

VISIBLE_ROWS_192 = 24   # modo padrao: 192 linhas / 8 = 24
VISIBLE_ROWS_224 = 28   # SMS II, com VDPFEATURE_EXTRAHEIGHT + 224LINES
PNT_ROWS = 28           # capacidade fisica da name table (0x3800..0x3EFF)
COLS = 32

# macro -> indice do argumento que carrega a altura (None = 1 linha so)
XY_MACROS = {
    "SMS_setTileatXY": None,
    "SMS_setNextTileatXY": None,
    "SMS_printatXY": None,
    "SMS_loadTileMapArea": 4,     # (x,y,src,width,height)
    "SMS_loadTileMapColumn": 3,   # (x,y,src,height)
}

def _split_args(s):
    """Divide argumentos no nivel 0 de parenteses/colchetes."""
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch in "([": depth += 1
        elif ch in ")]": depth -= 1
        if ch == "," and depth == 0:
            out.append(cur.strip()); cur = ""
        else:
            cur += ch
    if cur.strip(): out.append(cur.strip())
    return out

def _calls(src, macro):
    """Extrai a lista de argumentos de cada chamada da macro, com o offset."""
    for m in re.finditer(r"\b" + re.escape(macro) + r"\s*\(", src):
        i, depth = m.end() - 1, 0
        for j in range(i, len(src)):
            if src[j] in "([": depth += 1
            elif src[j] in ")]":
                depth -= 1
                if depth == 0:
                    yield m.start(), _split_args(src[i + 1:j])
                    break

def defines(src):
    """#define NAME <inteiro literal> — unica substituicao que arriscamos."""
    d = {}
    for name, val in re.findall(r"^\s*#\s*define\s+(\w+)\s+(.+?)\s*$", src, re.M):
        v = val.split("//")[0].split("/*")[0].strip()
        try:
            d[name] = int(v, 0)
        except ValueError:
            pass
    return d

def literal(expr, defs):
    """Resolve expr para int se for literal puro ou #define; senao None."""
    e = expr.strip().strip("()").strip()
    try:
        return int(e, 0)
    except ValueError:
        pass
    if e in defs:
        return defs[e]
    # soma/subtracao de literais e defines: "BASE+2"
    m = re.fullmatch(r"([\w]+|\d+)\s*([+-])\s*(\d+)", e)
    if m:
        left = literal(m.group(1), defs)
        if left is not None:
            return left + int(m.group(3)) if m.group(2) == "+" else left - int(m.group(3))
    return None

def wrappers(src, base):
    """Macros do projeto que so repassam coordenadas para uma macro XY.

    O laboratorio define `putat(x,y,s) SMS_printatXY((x),(y),...)`. Sem seguir
    isso o gate ve `y='(y)'` e declara tudo indecidivel — cego exatamente no
    codigo que a L011 quebrou. So segue repasse POSICIONAL direto: se a coord
    passada adiante nao for um parametro nu, nao inventa.
    """
    found = {}
    for name, params, body in re.findall(
            r"^\s*#\s*define\s+(\w+)\s*\(([^)]*)\)\s*(.+?)\s*$", src, re.M):
        plist = [p.strip() for p in params.split(",") if p.strip()]
        for macro, hidx in base.items():
            for _, args in _calls(body, macro):
                if len(args) < 2:
                    continue
                xi = _param_index(args[0], plist)
                yi = _param_index(args[1], plist)
                if xi is None or yi is None:
                    continue
                hi = None
                if hidx is not None and len(args) > hidx:
                    hi = _param_index(args[hidx], plist)
                    if hi is None:
                        continue
                found[name] = (xi, yi, hi)
    return found

def _param_index(expr, plist):
    e = expr.strip()
    while e.startswith("(") and e.endswith(")"):
        e = e[1:-1].strip()
    return plist.index(e) if e in plist else None

def visible_rows(src):
    """224 linhas so conta se o codigo LIGA o modo; caso contrario 192."""
    if re.search(r"VDPFEATURE_224LINES|VDPFEATURE_EXTRAHEIGHT", src):
        return VISIBLE_ROWS_224
    return VISIBLE_ROWS_192

def line_of(src, off):
    return src.count("\n", 0, off) + 1

def check_source(src, path="<mem>"):
    """Funcao PURA. Retorna (falhas, indecidiveis) — testavel sem projeto."""
    defs = defines(src)
    rows = visible_rows(src)
    # tabela unificada: nome -> (indice de x, indice de y, indice da altura)
    table = {m: (0, 1, h) for m, h in XY_MACROS.items()}
    table.update(wrappers(src, XY_MACROS))
    # Apaga so o CABECALHO `#define NOME(params)` — `putat(x,y,s)` nao e uma
    # chamada. O CORPO continua sob analise: coordenada literal cravada dentro
    # de uma macro erra igual, e nao pode escapar por morar num #define.
    macro_lines = set()
    def _blank(m):
        macro_lines.add(src.count("\n", 0, m.start()) + 1)
        return " " * len(m.group(0))
    body = re.sub(r"^[ \t]*#[ \t]*define[ \t]+\w+(?:\([^)\n]*\))?", _blank,
                  src, flags=re.M)
    fails, unknown = [], []
    for macro, (xi, yi, hidx) in table.items():
        for off, args in _calls(body, macro):
            if len(args) <= max(xi, yi):
                continue
            ln = line_of(body, off)
            x = literal(args[xi], defs)
            y = literal(args[yi], defs)
            h = 1
            if hidx is not None and len(args) > hidx:
                hv = literal(args[hidx], defs)
                if hv is None:
                    unknown.append((path, ln, macro, "altura nao literal"))
                    continue
                h = hv
            if y is None:
                # dentro do corpo de uma macro a coordenada e do CHAMADOR;
                # reportar aqui seria contar o mesmo caso duas vezes
                if ln not in macro_lines:
                    unknown.append((path, ln, macro, f"y='{args[yi]}' nao literal"))
                continue
            last = y + h - 1
            if last >= PNT_ROWS:
                fails.append((path, ln, macro,
                              f"y={y}..{last} passa de {PNT_ROWS - 1}: sai da PNT "
                              f"e escreve em 0x3F00 (SAT) — corrompe sprites"))
            elif last >= rows:
                fails.append((path, ln, macro,
                              f"y={y}..{last} fora das {rows} linhas renderizadas: "
                              f"escreve na cauda da PNT — INVISIVEL (L011)"))
            if x is None:
                unknown.append((path, ln, macro, f"x='{args[xi]}' nao literal"))
            elif x >= COLS:
                fails.append((path, ln, macro,
                              f"x={x} >= {COLS}: XYtoADDR nao satura, vaza para "
                              f"a linha seguinte"))
            elif x < 0 or y < 0:
                fails.append((path, ln, macro, f"coordenada negativa ({x},{y})"))
    return fails, unknown

SC_OK = """
#define ROW_STATUS 3
void f(void){
  SMS_printatXY(2, ROW_STATUS, "VITORIA");
  SMS_setTileatXY(31, 23, 5);
  SMS_loadTileMapArea(0, 0, map, 32, 24);
}
"""
SC_INVISIBLE = """
void f(void){ SMS_printatXY(2, 26, "VITORIA! 1:REINICIA"); }
"""
SC_SAT = """
void f(void){ SMS_setTileatXY(0, 29, 7); }
"""
SC_COL = """
void f(void){ SMS_setTileatXY(33, 3, 7); }
"""
SC_AREA = """
void f(void){ SMS_loadTileMapArea(0, 20, map, 32, 6); }
"""
SC_224 = """
void g(void){ SMS_VDPturnOnFeature(VDPFEATURE_224LINES); }
void f(void){ SMS_printatXY(2, 26, "ok em 224"); }
"""
SC_VAR = """
void f(unsigned char r){ SMS_printatXY(2, r, "?"); }
"""
# o caso real do laboratorio: a coordenada literal esta no CALLER do wrapper
SC_WRAPPER = """
#define putat(x,y,s)  SMS_printatXY((x),(y),(const unsigned char *)(s))
void f(void){ putat(2, 26, "VITORIA!"); }
"""
SC_WRAPPER_OK = """
#define putat(x,y,s)  SMS_printatXY((x),(y),(const unsigned char *)(s))
void f(void){ putat(2, 3, "VITORIA!"); }
"""
# wrapper que NAO repassa posicionalmente: nao inventar mapeamento
SC_WRAPPER_FIXED = """
#define status(s)  SMS_printatXY(2, 26, (s))
void f(void){ status("x"); }
"""

def self_check():
    f, u = check_source(SC_OK)
    assert not f, f"codigo dentro dos limites nao pode reprovar: {f}"
    assert not u, f"tudo literal, nao deveria haver indecidivel: {u}"

    f, _ = check_source(SC_INVISIBLE)
    assert len(f) == 1 and "INVISIVEL" in f[0][3], f"linha 26 tem de reprovar: {f}"

    f, _ = check_source(SC_SAT)
    assert len(f) == 1 and "SAT" in f[0][3], f"y=29 tem de acusar SAT: {f}"

    f, _ = check_source(SC_COL)
    assert len(f) == 1 and "x=33" in f[0][3], f"x=33 tem de reprovar: {f}"

    # area que COMECA valida e TERMINA fora: y=20 + altura 6 -> ultima linha 25
    f, _ = check_source(SC_AREA)
    assert len(f) == 1 and "y=20..25" in f[0][3], f"altura tem de entrar na conta: {f}"

    # 224 linhas: a MESMA linha 26 passa a ser legitima
    f, _ = check_source(SC_224)
    assert not f, f"em 224 linhas a linha 26 e visivel: {f}"

    # coordenada em variavel: nao provada, nunca aprovada em silencio
    f, u = check_source(SC_VAR)
    assert not f and len(u) == 1, f"y variavel deve virar indecidivel, nao falha: {f} {u}"

    # o caso real: a coordenada mora no CALLER do wrapper do projeto
    f, u = check_source(SC_WRAPPER)
    assert len(f) == 1 and "INVISIVEL" in f[0][3], f"wrapper tem de ser seguido: {f} {u}"
    assert not u, f"wrapper resolvido nao pode deixar residuo indecidivel: {u}"
    f, _ = check_source(SC_WRAPPER_OK)
    assert not f, f"wrapper com linha valida nao pode reprovar: {f}"

    # coordenada literal cravada DENTRO da macro nao escapa por morar num #define
    f, _ = check_source(SC_WRAPPER_FIXED)
    assert len(f) == 1 and "INVISIVEL" in f[0][3], f"literal dentro do #define escapou: {f}"

    print("[SELF-CHECK OK] audit_tilemap_bounds (reprova linha invisivel, "
          "escrita na SAT, coluna >=32 e altura que estoura; aprova 224 linhas; "
          "segue macro-wrapper do projeto; coordenada variavel vira indecidivel)")
    return 0

def collect(paths):
    out = []
    for p in paths:
        if os.path.isdir(p):
            for root, _, files in os.walk(p):
                out += [os.path.join(root, f) for f in files if f.endswith((".c", ".h"))]
        elif p.endswith((".c", ".h")):
            out.append(p)
    return sorted(out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        return self_check()
    files = collect(a.paths)
    if not files:
        print("[ERRO] nenhum .c/.h informado", file=sys.stderr)
        return 2
    fails, unknown = [], []
    for f in files:
        try:
            src = open(f, encoding="utf-8", errors="replace").read()
        except OSError as e:
            print(f"[ERRO] {f}: {e}", file=sys.stderr)
            return 2
        a_, b_ = check_source(src, f)
        fails += a_; unknown += b_
    for path, ln, macro, why in unknown:
        print(f"  [nao provado] {path}:{ln} {macro} — {why}")
    for path, ln, macro, why in fails:
        print(f"  [REPROVA] {path}:{ln} {macro} — {why}")
    if fails:
        print(f"[FAIL] {len(fails)} escrita(s) na name table fora da area util (L011)")
        return 1
    print(f"[OK] audit_tilemap_bounds: {len(files)} arquivo(s), "
          f"nenhuma escrita fora da area renderizada "
          f"({len(unknown)} coordenada(s) dinamica(s) nao provada(s))")
    return 0

if __name__ == "__main__":
    sys.exit(main())
