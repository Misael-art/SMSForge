#!/usr/bin/env python3
"""Gate PROCEDENCIA — cada simbolo visual em res/ precisa de origem declarada.

Le doc/asset_provenance_manifest.json do projeto:
{"assets": [{"file": "res/hero.png", "origin": "rascunho/hero.png",
             "author": "...", "tool": "none|ai_imagegen:<pipeline>",
             "sha256": "<sha256 do arquivo original em rascunho/>"}]}

Reprova:
- arquivo de asset sem entrada no manifest
- origin apontando para rascunho/ inexistente
- sha256 divergente (arquivo mudou sem re-declarar origem)
- origin "code" para personagem/inimigo/boss/cenario_final (pixel nascido de codigo)

Uso: audit_provenance.py --project <dir> [--self-check]
Exit: 0 | 1 reprova | 3 uso
"""
import sys, os, json, hashlib, argparse

VISUAL_EXT = (".png",)
BANNED_CODE_ORIGINS = {"personagem", "inimigo", "boss", "cenario_final"}

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(65536), b""):
            h.update(blk)
    return h.hexdigest()

def audit(project):
    errors = []
    res_dir = os.path.join(project, "res")
    man_path = os.path.join(project, "doc", "asset_provenance_manifest.json")
    assets_on_disk = []
    if os.path.isdir(res_dir):
        for root, _, files in os.walk(res_dir):
            for fn in sorted(files):
                if fn.endswith(VISUAL_EXT):
                    assets_on_disk.append(os.path.relpath(os.path.join(root, fn), project))
    entries = {}
    if os.path.exists(man_path):
        try:
            man = json.load(open(man_path))
            for a in man.get("assets", []):
                entries[a["file"].replace("\\", "/")] = a
        except (json.JSONDecodeError, KeyError) as e:
            return [f"manifest invalido: {e}"]
    elif assets_on_disk:
        return ["doc/asset_provenance_manifest.json ausente mas existem assets visuais"]
    for f in assets_on_disk:
        if f not in entries:
            errors.append(f"{f}: sem proveniencia declarada")
    for f, a in entries.items():
        fp = os.path.join(project, f)
        src = os.path.join(project, a.get("origin", ""))
        role = a.get("role", "")
        tool = a.get("tool", "")
        if tool == "code" and role.lower() in BANNED_CODE_ORIGINS:
            errors.append(f"{f}: pixel nascido de codigo como '{role}' e proibido")
        if not os.path.exists(fp):
            continue
        if not os.path.exists(src):
            errors.append(f"{f}: origin '{a.get('origin')}' nao existe em rascunho/")
            continue
        want = a.get("sha256", "")
        got = sha256(src)
        if want != got:
            errors.append(f"{f}: sha256 de origin mudou (declare novamente a origem)")
    return errors

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.self_check:
        import tempfile, shutil
        from png_io import write_indexed_png
        d = tempfile.mkdtemp(prefix="smsprov_")
        os.makedirs(os.path.join(d, "res"), exist_ok=True)
        os.makedirs(os.path.join(d, "doc"), exist_ok=True)
        write_indexed_png(os.path.join(d, "res", "x.png"), 8, 8,
                          [(0, 0, 0), (255, 255, 255)], [bytes([1] * 8)] * 8)
        open(os.path.join(d, "rascunho_x.png"), "wb").write(b"orig")
        digest = hashlib.sha256(b"orig").hexdigest()
        man = {"assets": [{"file": "res/x.png", "origin": "rascunho_x.png",
                           "author": "t", "tool": "code", "role": "personagem",
                           "sha256": digest}]}
        json.dump(man, open(os.path.join(d, "doc", "asset_provenance_manifest.json"), "w"))
        e1 = audit(d)
        assert any("nascido de codigo" in x or "proibido" in x for x in e1), e1
        man["assets"][0]["tool"] = "none"
        man["assets"][0]["sha256"] = "0" * 64
        json.dump(man, open(os.path.join(d, "doc", "asset_provenance_manifest.json"), "w"))
        e2 = audit(d)
        assert any("mudou" in x for x in e2), e2
        shutil.rmtree(d)
        print("[SELF-CHECK OK] provenance")
        return 0
    errors = audit(args.project)
    if errors:
        for e in errors:
            print(f"[FAIL] {e}")
        return 1
    print("[PASS] procedencia integral")
    return 0

if __name__ == "__main__":
    sys.exit(main())
