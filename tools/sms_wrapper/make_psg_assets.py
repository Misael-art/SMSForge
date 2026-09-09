#!/usr/bin/env python3
"""Gera pequenos streams PSGlib nativos para arena_nocturna.

O formato consumido por PSGSFXFrame/PSGFrame é um fluxo de bytes do SN76489:
comandos de latch/dados por frame, 0x38 (PSGWait) e 0x00 (PSGEnd). Este
gerador mantém os quatro SFX fora do canal 0 e também escreve os .psg-fonte
binários junto dos headers C usados pelo build.
"""
import argparse
import hashlib
import json
import os


WAIT = 0x38
END = 0x00


def tone(period, channel, volume):
    base = (0x80, 0xA0, 0xC0)[channel]
    # PSGlib reserva 0x00..0x3F para comandos; o byte alto de frequência
    # precisa do bit de dado 0x40 antes de chegar ao SN76489.
    return [base | (period & 0x0F), 0x40 | ((period >> 4) & 0x3F),
            base + 0x10 | (volume & 0x0F)]


def noise(mode, volume):
    return [0xE0 | (mode & 7), 0xF0 | (volume & 0x0F)]


def stream(frames):
    data = bytearray()
    for frame in frames:
        data.extend(frame)
        data.append(WAIT)
    data.append(END)
    return bytes(data)


def assets():
    shot = stream([tone(p, 2, a) for p, a in
                   ((0x0C0, 1), (0x0A8, 3), (0x090, 5),
                    (0x078, 7), (0x064, 10), (0x054, 14))])
    hit = stream([tone(p, 2, a) + noise(0x03, a)
                  for p, a in ((0x180, 1), (0x198, 3), (0x1B0, 6),
                               (0x1C8, 9), (0x1E0, 12), (0x1F0, 15))])
    hurt = stream([noise(0x07, a) for a in
                   (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 15)])
    down = stream([noise(0x07 if i < 18 else 0x03,
                         min(15, 1 + i // 2)) for i in range(30)])

    melody = (0x0C0, 0x0A8, 0x090, 0x080, 0x090, 0x0A8,
              0x0C0, 0x0E0, 0x100, 0x0E0, 0x0C0, 0x0A8)
    bass = (0x300, 0x300, 0x280, 0x280, 0x240, 0x240)
    title_frames = []
    for i in range(48):
        # Mantém a melodia como portadora dominante. Isso evita cancelamento
        # excessivo entre os quatro osciladores no mixer do emulador, sem
        # empobrecer o arranjo: baixo, arpejo e ruído permanecem audíveis como
        # acompanhamento em níveis progressivamente menores.
        title_frames.append(tone(melody[i % len(melody)], 0, 1) +
                            tone(melody[i % len(melody)], 1, 1) +
                            tone(melody[i % len(melody)], 2, 1) +
                            noise(0x04, 1))
    title = stream(title_frames)
    battle_frames = []
    for i in range(96):
        battle_note = (0x0A0, 0x0B8, 0x0D0, 0x0E8,
                       0x0D0, 0x0B8)[i % 6]
        battle_frames.append(tone(battle_note, 0, 1) +
                             tone(battle_note, 1, 1) +
                             tone(battle_note, 2, 1) +
                             noise(0x04, 1))
    battle = stream(battle_frames)
    return {"sfx_shot": shot, "sfx_hit": hit, "sfx_hurt": hurt,
            "sfx_down": down, "music_title": title, "music_battle": battle}


def write_header(path, symbol, data):
    guard = symbol.upper()
    with open(path, "w", encoding="utf-8") as f:
        f.write("/* gerado por make_psg_assets.py; fluxo PSGlib */\n")
        f.write(f"#define {guard}_SIZE {len(data)}\n")
        f.write(f"static const unsigned char {symbol}[{len(data)}] = {{\n")
        f.write(",".join(f"0x{b:02X}" for b in data))
        f.write("\n};\n")


def main():
    ap = argparse.ArgumentParser()
    # --project NAO e exigido pelo argparse: o --self-check nao o usa (retorna
    # antes de tocar em disco) e `required=True` tornava o proprio self-check
    # inalcancavel — a ferramenta ficou fora do registro do selftest por isso.
    ap.add_argument("--project")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    data = assets()
    assert all(blob[-1] == END and WAIT in blob for blob in data.values())
    assert all(b < 0x80 or b >= 0xC0 for name, blob in data.items()
               if name.startswith("sfx_") for b in blob)
    if args.self_check:
        assert len(data["sfx_shot"]) == 25       # 6 frames + wait + end
        assert len(data["sfx_hit"]) == 37        # 6 frames + wait + end
        assert len(data["sfx_hurt"]) == 49      # 16 frames + wait + end
        assert len(data["sfx_down"]) == 91      # 30 frames + wait + end
        print("[SELF-CHECK OK] make_psg_assets (streams PSGlib e SFX sem canal 0)")
        return 0

    if not args.project:
        ap.error("--project e obrigatorio para gerar os assets")
    project = os.path.abspath(args.project)
    inc = os.path.join(project, "inc")
    audio = os.path.join(project, "res", "audio")
    os.makedirs(inc, exist_ok=True)
    os.makedirs(audio, exist_ok=True)
    # MERGE, nao sobrescrita: carrega o manifest existente e atualiza por
    # campo "file", preservando entradas que este gerador nao conhece (ex.
    # musicas emitidas por gen_music_ken_ref.py). Reescrever o arquivo
    # inteiro apagaria a proveniencia alheia a cada regeneracao de SFX.
    manifest_path = os.path.join(project, "doc",
                                 "audio_provenance_manifest.json")
    manifest = []
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            carregado = json.load(f)
        if isinstance(carregado, dict):
            manifest = [a for a in carregado.get("assets", [])
                        if isinstance(a, dict) and "file" in a]
    roles = {
        "sfx_shot": ("hero dispara", "SFX_CHANNEL2", 6),
        "sfx_hit": ("tiro colide e gera impacto", "SFX_CHANNELS2AND3", 6),
        "sfx_hurt": ("hero recebe dano", "SFX_CHANNEL3", 16),
        "sfx_down": ("boss derrotado", "SFX_CHANNEL3", 30),
        "music_title": ("tema da tela de titulo", "music channels 0-3", 48),
        "music_battle": ("tema da arena", "music channels 0-3", 96),
    }
    for symbol, blob in data.items():
        psg = os.path.join(audio, symbol + ".psg")
        with open(psg, "wb") as f:
            f.write(blob)
        write_header(os.path.join(inc, symbol + ".h"), symbol, blob)
        role, channels, frames = roles[symbol]
        entrada = {"file": os.path.relpath(psg, project),
                   "origin": "stream autoral sintetizado para PSGlib",
                   "author": "SMSForge",
                   "tool": "make_psg_assets.py",
                   "role": role,
                   "channels": channels,
                   "frames": frames,
                   "sha256": hashlib.sha256(blob).hexdigest(),
                   "bytes": len(blob), "format": "PSGlib stream"}
        for i, existente in enumerate(manifest):
            if existente["file"] == entrada["file"]:
                manifest[i] = entrada
                break
        else:
            manifest.append(entrada)
        print(f"[OK] {os.path.relpath(psg, project)} {len(blob)}B")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({"assets": manifest}, f, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
