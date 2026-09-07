#!/usr/bin/env python3
"""Encurta um fluxo PSG que é repetição exata, sem mudar o que se ouve.

`music_battle` são **240 repetições byte a byte do mesmo frame de 12 bytes**
(2881 B). O PSGlib já volta ao início sozinho ao encontrar PSGEnd (0x00 cai em
`_musicLoop` em PSGlib.c), então as 239 cópias extras não tocam nada que a
primeira não toque — só ocupam ROM. Numa ROM de 32 KB com ~1 KB livre, isso é
o maior desperdício isolado do cartucho.

O corte é seguro por construção: o script só age se o fluxo for periódico
EXATO, e verifica que expandir o resultado reproduz o original frame a frame
antes de gravar. Se o conteúdo tiver melodia (frames diferentes), ele recusa.

Uso: python3 tools/shrink_music_loop.py [--check] [--keep N]
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
INC = os.path.join(HERE, os.pardir, "inc")

WAIT = 0x38
END = 0x00
ALVOS = ["music_battle", "music_title"]


def split_frames(data):
    """Fatia o fluxo em frames; cada frame termina no comando WAIT."""
    frames, cur = [], bytearray()
    for b in data:
        if b == END:
            break
        cur.append(b)
        if b == WAIT:
            frames.append(bytes(cur))
            cur = bytearray()
    return frames, bytes(cur)


def periodo(frames):
    """Menor P tal que frames[i] == frames[i % P] para todo i. None se não houver."""
    n = len(frames)
    for p in range(1, n // 2 + 1):
        if all(frames[i] == frames[i % p] for i in range(n)):
            return p
    return None


def main():
    check = "--check" in sys.argv
    keep = 4
    if "--keep" in sys.argv:
        keep = int(sys.argv[sys.argv.index("--keep") + 1])

    total_antes = total_depois = 0
    for nome in ALVOS:
        path = os.path.join(INC, nome + ".h")
        if not os.path.exists(path):
            continue
        src = open(path).read()
        m = re.search(r"(\w+)\[(\d+)\] = \{(.*?)\};", src, re.S)
        data = bytes(int(x, 0) for x in re.findall(r"0x[0-9a-fA-F]+", m.group(3)))
        frames, resto = split_frames(data)
        p = periodo(frames)
        if p is None:
            print(f"{nome:14s} [SKIP] não é repetição exata "
                  f"({len(frames)} frames distintos) — tem conteúdo a preservar")
            continue
        n_keep = max(p, (keep // p) * p or p)
        novo = b"".join(frames[:n_keep]) + resto + bytes([END])

        # Verificação: reexpandir o encurtado tem de dar o original, frame a frame.
        nf, _ = split_frames(novo)
        if any(nf[i % len(nf)] != frames[i] for i in range(len(frames))):
            print(f"{nome:14s} [ABORT] expansão não bate com o original")
            continue

        total_antes += len(data)
        total_depois += len(novo)
        print(f"{nome:14s} {len(frames)} frames de {len(frames[0])} B, "
              f"período {p} -> mantém {n_keep}  |  {len(data)} B -> {len(novo)} B")
        if check:
            continue

        arr = "\n".join(
            ", ".join(f"0x{b:02X}" for b in novo[i:i + 16]) + ","
            for i in range(0, len(novo), 16))
        out = src
        out = out[:m.start(3)] + "\n" + arr + "\n" + out[m.end(3):]
        out = out.replace(f"{m.group(1)}[{m.group(2)}]", f"{m.group(1)}[{len(novo)}]")
        out = re.sub(rf"#define {nome.upper()}_SIZE \d+",
                     f"#define {nome.upper()}_SIZE {len(novo)}", out)
        out = out.replace(
            "/* gerado por make_psg_assets.py; fluxo PSGlib */",
            "/* gerado por make_psg_assets.py; fluxo PSGlib.\n"
            " * Encurtado por tools/shrink_music_loop.py: o fluxo era repetição\n"
            " * exata e o PSGlib volta ao início sozinho no PSGEnd. Mesmo som,\n"
            " * menos ROM. NAO editar a mao. */")
        open(path, "w").write(out)
        psg = os.path.join(HERE, os.pardir, "res", "audio", nome + ".psg")
        if os.path.isdir(os.path.dirname(psg)):
            open(psg, "wb").write(novo)

    if total_antes:
        print(f"[{'CHECK' if check else 'OK'}] {total_antes} B -> {total_depois} B "
              f"(libera {total_antes - total_depois} B)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
