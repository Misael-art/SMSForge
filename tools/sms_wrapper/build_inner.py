#!/usr/bin/env python3
"""build_inner.py — FONTE UNICA de logica de build do SMSForge.

Nenhum projeto tem logica propria: os shims build.sh/bat delegam AQUI.

Pipeline:
  1. valida esqueleto (.mddev/project.json)
  2. pre-gates: recursos (res/) + procedencia
  3. toolchain: sdcc >= 4.2 + devkitSMS (SMSlib.lib, PSGlib.lib, crt0_sms.rel)
     ausente -> FAIL_AMBIENTE (exit 2) com instrucao. NUNCA simula.
  4. compila src/*.c -> linka (crt0 primeiro, libs depois) -> makesms
  5. registra out/build_record.json + changelog/roms/build_vNNN/rom.sms
  6. SMS_EVIDENCE=1 -> capture_evidence.py

Exit: 0 build | 1 reprovação (gate ou compilador) | 2 ambiente ausente
"""
import sys, os, json, glob, shutil, subprocess, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

def fail(msg, code):
    print(f"[BUILD {('FAIL_AMBIENTE' if code == 2 else 'FAIL')}] {msg}")
    return code

def find_toolchain():
    """Retorna dict com caminhos ou None com motivo."""
    import shutil as sh
    sdk = os.path.normpath(os.path.join(HERE, "..", "..", "sdk"))
    sdcc = sh.which("sdcc") or os.path.join(sdk, "sdcc-portable", "bin", "sdcc")
    if not os.path.exists(sdcc):
        return None, ("sdcc nao encontrado no PATH nem em " + sdk +
                      "/sdcc-portable/bin | Rode tools/sms_wrapper/ensure_toolchain.sh")
    ver_out = subprocess.run([sdcc, "--version"], capture_output=True, text=True).stdout
    import re
    m = re.search(r"(\d+)\.\d+\.\d+", ver_out)
    major = int(m.group(1)) if m else 0
    if major < 4:
        return None, f"sdcc {major}.x < 4.2 requerido ({ver_out.splitlines()[0][:60]})"
    root = os.environ.get("SMS_DEVKITSMS") or os.path.normpath(os.path.join(
        HERE, "..", "..", "sdk", "devkitSMS"))
    need = {
        "SMSlib.h": os.path.join(root, "SMSlib", "SMSlib.h"),
        "SMSlib.lib": os.path.join(root, "SMSlib", "SMSlib.lib"),
        "PSGlib.h": os.path.join(root, "PSGlib", "PSGlib.h"),
        "PSGlib.lib": os.path.join(root, "PSGlib", "PSGlib.lib"),
        "crt0_sms.rel": os.path.join(root, "crt0", "crt0_sms.rel"),
    }
    missing = [n for n, p in need.items() if not os.path.exists(p)]
    if missing:
        return None, ("devkitSMS incompleto em " + root +
                      "; faltam: " + ", ".join(missing) +
                      ". Siga sdk/README.md")
    makesms = sh.which("makesms")
    if not makesms:
        cand = os.path.join(root, "tools", "makesms")
        if os.path.exists(cand):
            makesms = cand
        else:
            return None, "makesms nao encontrado (rode ensure_toolchain.sh)"
    return {"sdcc": sdcc, "makesms": makesms,
            "inc": [os.path.dirname(need["SMSlib.h"]),
                    os.path.dirname(need["PSGlib.h"])],
            "peep": os.path.join(root, "peep-rules.txt"),
            **need}, None

def pre_gates(project):
    from audit_validate_resources import check_png
    from audit_provenance import audit as provenance_audit
    errors = []
    pngs = sorted(glob.glob(os.path.join(project, "res", "**", "*.png"), recursive=True))
    for p in pngs:
        kind = "sprite" if os.sep + "sprites" + os.sep in p else "bg"
        errors += [f"recursos/{os.path.relpath(p, project)}: {e}"
                   for e in check_png(p, kind)]
    errors += ["procedencia: " + e for e in provenance_audit(project)]
    return errors

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=os.getcwd())
    ap.add_argument("--skip-pre-gates", action="store_true",
                    help="apenas para depurar o compilador; NUNCA em entrega")
    args = ap.parse_args()
    project = os.path.abspath(args.project)

    if not os.path.exists(os.path.join(project, ".mddev", "project.json")):
        return fail(f"{project} nao e um projeto (falta .mddev/project.json)", 1)
    manifest = json.load(open(os.path.join(project, ".mddev", "project.json")))
    name = manifest.get("name") or os.path.basename(project)

    os.makedirs(os.path.join(project, "out", "obj"), exist_ok=True)
    record = {"project": name, "date": "", "steps": {}, "axes": {}}

    if not args.skip_pre_gates:
        errs = pre_gates(project)
        if errs:
            for e in errs:
                print(f"[FAIL] {e}")
            return 1
        record["steps"]["pre_gates"] = "pass"

    tc, why = find_toolchain()
    if tc is None:
        return fail(why + " | Instale seguindo sdk/README.md. "
                    "O gate NAO simula build.", 2)
    record["steps"]["toolchain"] = "ok"

    srcs = sorted(glob.glob(os.path.join(project, "src", "*.c")))
    if not srcs:
        return fail("nenhum .c em src/", 1)
    objs, logs = [], []
    for src_abs in srcs:
        base = os.path.splitext(os.path.basename(src_abs))[0]
        obj_rel = os.path.join("out", "obj", base + ".rel")
        cmd = [tc["sdcc"], "-c", "-mz80", "-o", obj_rel]
        if os.path.exists(tc.get("peep", "")):
            cmd += ["--peep-file", tc["peep"]]
        for inc in tc.get("inc", []):
            cmd += ["-I" + inc]
        proj_inc = os.path.join(project, "inc")
        if os.path.isdir(proj_inc):
            cmd += ["-I" + proj_inc]
        cmd.append(os.path.relpath(src_abs, project))
        r = subprocess.run(cmd, cwd=project, capture_output=True, text=True)
        logs.append(f"$ {' '.join(cmd)}\n{r.stdout}{r.stderr}")
        if r.returncode != 0:
            open(os.path.join(project, "out", "logs_build.txt"), "w").write("\n".join(logs))
            return fail(f"compilacao de {src_abs} falhou (log: out/logs_build.txt)", 1)
        objs.append(obj_rel)
    record["steps"]["compile"] = f"{len(objs)} objeto(s)"

    ihx = os.path.join("out", "obj", name + ".ihx")
    link_cmd = ([tc["sdcc"], "-o", ihx, "-mz80", "--no-std-crt0", "--data-loc", "0xC000",
                 tc["crt0_sms.rel"]] +
                objs +
                [tc["SMSlib.lib"], tc["PSGlib.lib"]])
    r = subprocess.run(link_cmd, cwd=project, capture_output=True, text=True)
    logs.append("$ " + " ".join(link_cmd) + f"\n{r.stdout}{r.stderr}")
    open(os.path.join(project, "out", "logs_build.txt"), "w").write("\n".join(logs))
    if r.returncode != 0 or not os.path.exists(os.path.join(project, ihx)):
        return fail(f"link falhou (log: out/logs_build.txt)", 1)

    rom_dir = os.path.join(project, "out", "rom")
    os.makedirs(rom_dir, exist_ok=True)
    rom = os.path.join(rom_dir, name + ".sms")
    r = subprocess.run([tc["makesms"], ihx, os.path.relpath(rom, project)],
                       cwd=project, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(rom):
        return fail(f"makesms falhou: {r.stderr[:200]}", 1)
    size = os.path.getsize(rom)
    record["steps"]["rom"] = f"{rom} ({size} bytes)"

    # higiene: artefatos de compilacao (asm/lst/sym) vazam para a raiz do projeto;
    # move-os para out/obj para nao poluir o arvore.
    for ext in (".asm", ".lst", ".sym"):
        leak = os.path.join(project, name + ext)
        if os.path.exists(leak):
            shutil.move(leak, os.path.join(project, "out", "obj", name + ext))

    n = 1
    chg = os.path.join(project, "changelog", "roms")
    while os.path.exists(os.path.join(chg, f"build_v{n:03d}")):
        n += 1
    dest = os.path.join(chg, f"build_v{n:03d}", "rom.sms")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copy2(rom, dest)
    record["changelog"] = dest

    record["axes"] = {"build": True, "validation_report": True,
                      "boot_emulador": False, "gameplay": False,
                      "fps_constante": False, "audio": False,
                      "memory_bank_atualizado": False}
    # PRESERVA eixos de runtime ja conquistados (merge, nao reset):
    # um build subsequente nao pode apagar boot/gameplay/fps provados antes.
    prev = os.path.join(project, "out", "build_record.json")
    if os.path.exists(prev):
        try:
            old = json.load(open(prev))
            for k in record["axes"]:
                if old.get("axes", {}).get(k):
                    record["axes"][k] = True
        except (json.JSONDecodeError, OSError):
            pass
    json.dump(record, open(os.path.join(project, "out", "build_record.json"), "w"),
              indent=2)
    print(f"[BUILD OK] {rom} ({size}B) | eixos restantes para entrega: "
          f"{[k for k, v in record['axes'].items() if not v]}")
    if os.environ.get("SMS_EVIDENCE") == "1":
        import capture_evidence as ev
        rc = ev.capture(project, rom)
        if rc != 0:
            return rc
    return 0

if __name__ == "__main__":
    sys.exit(main())
