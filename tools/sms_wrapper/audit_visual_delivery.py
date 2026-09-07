#!/usr/bin/env python3
"""audit_visual_delivery.py — boot técnico não é qualidade visual.

Porta o MÉTODO do visual_delivery_gate do SGDKForge para Master System:
uma captura que prova boot/rota Linux pode (e deve) reprovar entrega se a
cena for D1, probe, branding de referência ou escala abaixo do contrato.

Blockers permanentes (vocabulário estável):
  wrong_visual_epoch
  placeholder_or_probe_in_delivery_scene
  duplicate_character_asset
  entity_scale_below_contract
  entity_scale_uncontracted
  stage_contains_branding_or_reference_screen
  hud_overlap_or_clipping
  rom_asset_binding_unproven
  canvas_not_sms

Uso:
  audit_visual_delivery.py --project <dir> [--contract <json>] [--delivery]
  audit_visual_delivery.py --self-check
Exit: 0 entrega visual honesta | 1 blocker | 3 uso
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from audit_rom_asset_binding import audit as binding_audit, sha256_file  # noqa: E402
from png_io import read_indexed_png, write_indexed_png  # noqa: E402

SMS_CANVAS = {(256, 192), (256, 224)}  # 224 só com VDPFEATURE_224LINES declarado
DELIVERY_EPOCHS = {"delivery"}
INELIGIBLE_EPOCHS = {
    "probe", "technical_d1", "lab", "visual_lab_control",
    "technical_candidate", "reference_only", "negative_case_evidence",
}
BANNED_ROLES = {
    "probe", "reference_only", "negative_case_evidence",
    "technical_candidate", "visual_lab_control", "placeholder",
    "procedural_debug", "debug_lab_control",
}
BRANDING_MARKERS = (
    "hamoopig", "sgdk splash", "sega logo stage", "devkitsms splash",
    "copyright screen as stage", "reference_screen", "engine_title",
)
NON_DELIVERY_CLASSIFICATIONS = {
    "runtime_probe_passed_visual_epoch_failed",
    "technical_artifact_only",
    "lab_evidence_not_delivery",
    "smoke_only",
}


def _rel(project, path):
    if not path:
        return None
    return path if os.path.isabs(path) else os.path.join(project, path)


def opaque_bbox_height(path):
    img = read_indexed_png(path)
    trns = img["trns"] or {0}
    top = bot = None
    for y, row in enumerate(img["pixels"]):
        if any(px not in trns for px in row):
            if top is None:
                top = y
            bot = y
    if top is None:
        return 0
    return bot - top + 1


def _boxes_overlap(a, b):
    return not (a["x"] + a["w"] <= b["x"] or b["x"] + b["w"] <= a["x"]
                or a["y"] + a["h"] <= b["y"] or b["y"] + b["h"] <= a["y"])


def _text_blob(*parts):
    return " ".join(str(p or "") for p in parts).lower()


def load_contract(project, explicit=None):
    candidates = []
    if explicit:
        candidates.append(explicit)
    candidates.extend([
        os.path.join(project, "doc", "visual_delivery_contract.json"),
        os.path.join(project, "out", "logs", "visual_delivery_contract.json"),
    ])
    for path in candidates:
        if path and os.path.isfile(path):
            try:
                return json.load(open(path, encoding="utf-8")), path, []
            except (OSError, json.JSONDecodeError) as exc:
                return None, path, [f"contrato ilegível ({exc})"]
    return None, None, []


def audit(project, contract_path=None, delivery=False):
    problems = []
    codes = []
    data, used, load_errs = load_contract(project, contract_path)
    problems += load_errs
    if data is None:
        if delivery:
            problems.append("wrong_visual_epoch: contrato de entrega visual ausente")
            codes.append("wrong_visual_epoch")
        return problems, codes, {"present": False}

    epoch = data.get("visual_epoch") or data.get("epoch") or ""
    classification = data.get("classification") or ""
    claim = data.get("claim") or ""
    wants_delivery = delivery or data.get("delivery_intent") is True \
        or claim in {"delivery", "ready_for_aaa", "aaa", "release"}

    canvas = data.get("canvas") or {}
    cw, ch = int(canvas.get("w") or 0), int(canvas.get("h") or 0)
    if (cw, ch) not in SMS_CANVAS:
        problems.append(
            f"canvas_not_sms: contrato declara {cw}×{ch}; "
            "Master System é 256×192 (224 só com VDPFEATURE_224LINES)"
        )
        codes.append("canvas_not_sms")
    if canvas.get("console") in {"megadrive", "genesis", "md"}:
        problems.append("canvas_not_sms: console do contrato não é Master System")
        codes.append("canvas_not_sms")

    if wants_delivery and epoch not in DELIVERY_EPOCHS:
        problems.append(
            f"wrong_visual_epoch: epoch='{epoch or 'ausente'}' não é delivery "
            f"(captura técnica ≠ qualidade visual)"
        )
        codes.append("wrong_visual_epoch")
    if wants_delivery and classification in NON_DELIVERY_CLASSIFICATIONS:
        problems.append(
            f"wrong_visual_epoch: classification='{classification}' prova boot, "
            "não cena final"
        )
        codes.append("wrong_visual_epoch")
    if epoch in INELIGIBLE_EPOCHS and wants_delivery:
        if "wrong_visual_epoch" not in codes:
            codes.append("wrong_visual_epoch")

    shas = {}
    for ch_spec in data.get("characters") or []:
        cid = ch_spec.get("id") or ch_spec.get("name") or "?"
        role = (ch_spec.get("role") or ch_spec.get("disposition") or "").lower()
        png_rel = ch_spec.get("png") or ch_spec.get("res_path")
        png = _rel(project, png_rel)
        note = _text_blob(ch_spec.get("note"), ch_spec.get("tags"), role, png_rel)
        if role in BANNED_ROLES or any(b in note for b in BANNED_ROLES):
            problems.append(
                f"placeholder_or_probe_in_delivery_scene: {cid} role/tag='{role or note}'"
            )
            codes.append("placeholder_or_probe_in_delivery_scene")
        if not png or not os.path.isfile(png):
            problems.append(f"placeholder_or_probe_in_delivery_scene: {cid} PNG ausente")
            codes.append("placeholder_or_probe_in_delivery_scene")
            continue
        digest = sha256_file(png)
        if digest in shas:
            problems.append(
                f"duplicate_character_asset: {cid} e {shas[digest]} compartilham o mesmo PNG"
            )
            codes.append("duplicate_character_asset")
        else:
            shas[digest] = cid

        min_h = ch_spec.get("min_visible_height_px")
        if wants_delivery and min_h is None:
            problems.append(f"entity_scale_uncontracted: {cid} sem min_visible_height_px")
            codes.append("entity_scale_uncontracted")
        else:
            try:
                measured = opaque_bbox_height(png)
            except Exception as exc:  # noqa: BLE001 — gate deve falar, não explodir
                problems.append(f"entity_scale_below_contract: {cid} PNG ilegível ({exc})")
                codes.append("entity_scale_below_contract")
                measured = None
            declared = ch_spec.get("visible_height_px")
            height = declared if declared is not None else measured
            if min_h is not None and height is not None and int(height) < int(min_h):
                problems.append(
                    f"entity_scale_below_contract: {cid} visível={height}px "
                    f"< contrato {min_h}px (canvas SMS 256×192; não copie 320×224)"
                )
                codes.append("entity_scale_below_contract")
            if (declared is not None and measured is not None
                    and abs(int(declared) - int(measured)) > 2 and wants_delivery):
                problems.append(
                    f"entity_scale_below_contract: {cid} visible_height_px={declared} "
                    f"≠ bbox opaco {measured}px"
                )
                codes.append("entity_scale_below_contract")

    stage = data.get("stage") or {}
    stage_blob = _text_blob(
        stage.get("bga"), stage.get("bgb"), stage.get("note"),
        stage.get("source"), *(stage.get("branding_keywords") or []),
    )
    if any(m in stage_blob for m in BRANDING_MARKERS) or stage.get("contains_branding") is True:
        problems.append(
            "stage_contains_branding_or_reference_screen: palco declara branding/"
            "tela de referência (HAMOOPIG, splash de engine, logo como BG)"
        )
        codes.append("stage_contains_branding_or_reference_screen")
    for key in ("bga", "bgb"):
        rel = stage.get(key)
        if not rel:
            continue
        name = os.path.basename(rel).lower()
        if any(m.replace(" ", "") in name.replace("_", "") for m in ("hamoopig", "splash", "engine_title")):
            problems.append(
                f"stage_contains_branding_or_reference_screen: {key}={rel}"
            )
            codes.append("stage_contains_branding_or_reference_screen")

    hud = data.get("hud") or {}
    boxes = list(hud.get("boxes") or [])
    for i, a in enumerate(boxes):
        ax, ay, aw, ah = (int(a.get(k, 0)) for k in ("x", "y", "w", "h"))
        if aw <= 0 or ah <= 0:
            problems.append(f"hud_overlap_or_clipping: caixa '{a.get('name', i)}' degenerada")
            codes.append("hud_overlap_or_clipping")
            continue
        if ax < 0 or ay < 0 or ax + aw > (cw or 256) or ay + ah > (ch or 192):
            problems.append(
                f"hud_overlap_or_clipping: '{a.get('name', i)}' sai da canvas "
                f"{cw or 256}×{ch or 192}"
            )
            codes.append("hud_overlap_or_clipping")
        for b in boxes[i + 1:]:
            if _boxes_overlap(
                {"x": ax, "y": ay, "w": aw, "h": ah},
                {"x": int(b.get("x", 0)), "y": int(b.get("y", 0)),
                 "w": int(b.get("w", 0)), "h": int(b.get("h", 0))},
            ):
                problems.append(
                    f"hud_overlap_or_clipping: '{a.get('name', i)}' ∩ '{b.get('name', '?')}'"
                )
                codes.append("hud_overlap_or_clipping")

    bind_probs, bind_report = binding_audit(
        project,
        rom_path=_rel(project, data.get("rom_path")),
        map_path=_rel(project, data.get("binding_map")),
        require=wants_delivery,
    )
    if bind_probs:
        for p in bind_probs:
            problems.append(p if p.startswith("rom_asset_binding") else
                            f"rom_asset_binding_unproven: {p}")
        codes.append("rom_asset_binding_unproven")

    report = {
        "present": True,
        "contract_path": used,
        "visual_epoch": epoch,
        "classification": classification,
        "wants_delivery": wants_delivery,
        "ready_for_aaa": wants_delivery and not problems,
        "binding": bind_report,
        "blocker_codes": sorted(set(codes)),
    }
    return problems, sorted(set(codes)), report


def _sprite(path, w, h, fill=1, opaque_h=None):
    pal = [(0, 0, 0), (255, 255, 255), (0, 0, 255)] + [(0, 0, 0)] * 13
    oh = opaque_h if opaque_h is not None else h
    rows = []
    for y in range(h):
        rows.append(bytes([(fill if y < oh else 0)] * w))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_indexed_png(path, w, h, pal, rows)


def _self_check() -> int:
    d = tempfile.mkdtemp(prefix="smsvisdel_")
    try:
        a = os.path.join(d, "res", "sprites", "hero.png")
        b = os.path.join(d, "res", "sprites", "rival.png")
        bg = os.path.join(d, "res", "bg", "stage_bga.png")
        rom = os.path.join(d, "out", "rom", "game.sms")
        os.makedirs(os.path.join(d, "doc"), exist_ok=True)
        os.makedirs(os.path.dirname(rom), exist_ok=True)
        _sprite(a, 16, 48, opaque_h=48)
        _sprite(b, 16, 48, fill=2, opaque_h=48)
        _sprite(bg, 256, 192, fill=1)
        open(rom, "wb").write(b"SMS" + b"\x00" * 128)
        bind = {
            "schema": "rom_asset_binding_v1",
            "rom_path": "out/rom/game.sms",
            "rom_sha256": sha256_file(rom),
            "rom_size_bytes": os.path.getsize(rom),
            "entries": [
                {"res_path": "res/sprites/hero.png", "symbol": "hero_tiles",
                 "sha256": sha256_file(a)},
                {"res_path": "res/sprites/rival.png", "symbol": "rival_tiles",
                 "sha256": sha256_file(b)},
            ],
        }
        json.dump(bind, open(os.path.join(d, "doc", "rom_asset_binding.json"), "w"))

        good = {
            "schema": "visual_delivery_contract_v1",
            "visual_epoch": "delivery",
            "classification": "delivery_candidate",
            "delivery_intent": True,
            "canvas": {"w": 256, "h": 192, "console": "sms"},
            "characters": [
                {"id": "hero", "png": "res/sprites/hero.png",
                 "min_visible_height_px": 40, "role": "personagem"},
                {"id": "rival", "png": "res/sprites/rival.png",
                 "min_visible_height_px": 40, "role": "personagem"},
            ],
            "stage": {"bga": "res/bg/stage_bga.png", "contains_branding": False},
            "hud": {"boxes": [
                {"name": "hp", "x": 8, "y": 8, "w": 64, "h": 8},
                {"name": "timer", "x": 112, "y": 8, "w": 32, "h": 8},
            ]},
            "binding_map": "doc/rom_asset_binding.json",
            "rom_path": "out/rom/game.sms",
        }
        json.dump(good, open(os.path.join(d, "doc", "visual_delivery_contract.json"), "w"))
        p, codes, _ = audit(d, delivery=True)
        assert not p, f"entrega válida reprovou: {p}"

        # Época D1 + probes idênticos + HAMOOPIG + escala baixa + HUD overlap
        probe = os.path.join(d, "res", "sprites", "spr_kairo_vant_probe.png")
        _sprite(probe, 32, 40, opaque_h=16)
        shutil.copy(probe, os.path.join(d, "res", "sprites", "spr_c1_probe.png"))
        ham = os.path.join(d, "res", "bg", "room_0_bgb.png")
        _sprite(ham, 256, 192)
        bind_path = os.path.join(d, "doc", "rom_asset_binding.json")
        if os.path.isfile(bind_path):
            os.remove(bind_path)
        d1 = {
            "schema": "visual_delivery_contract_v1",
            "visual_epoch": "technical_d1",
            "classification": "runtime_probe_passed_visual_epoch_failed",
            "delivery_intent": True,
            "canvas": {"w": 256, "h": 192, "console": "sms"},
            "characters": [
                {"id": "kairo", "png": "res/sprites/spr_kairo_vant_probe.png",
                 "role": "probe", "min_visible_height_px": 48},
                {"id": "c1", "png": "res/sprites/spr_c1_probe.png",
                 "role": "probe", "min_visible_height_px": 48},
            ],
            "stage": {
                "bga": "res/bg/room_0_bga.png",
                "bgb": "res/bg/room_0_bgb.png",
                "note": "tela HAMOOPIG reusada como palco",
                "contains_branding": True,
            },
            "hud": {"boxes": [
                {"name": "hp", "x": 0, "y": 0, "w": 80, "h": 16},
                {"name": "meter", "x": 40, "y": 8, "w": 80, "h": 16},
            ]},
        }
        json.dump(d1, open(os.path.join(d, "doc", "visual_delivery_contract.json"), "w"))
        p, codes, _ = audit(d, delivery=True)
        needed = {
            "wrong_visual_epoch",
            "placeholder_or_probe_in_delivery_scene",
            "duplicate_character_asset",
            "entity_scale_below_contract",
            "stage_contains_branding_or_reference_screen",
            "hud_overlap_or_clipping",
            "rom_asset_binding_unproven",
        }
        missing = needed - set(codes)
        assert not missing, f"D1 deveria disparar {missing}; codes={codes}; p={p}"

        # Canvas Mega Drive copiada
        md = dict(good)
        md["canvas"] = {"w": 320, "h": 224, "console": "megadrive"}
        json.dump(md, open(os.path.join(d, "doc", "visual_delivery_contract.json"), "w"))
        p, codes, _ = audit(d, delivery=True)
        assert "canvas_not_sms" in codes, f"faltou recusar 320×224: {codes} {p}"

        # Sem contrato + --delivery reprova; sem --delivery passa (lab)
        os.remove(os.path.join(d, "doc", "visual_delivery_contract.json"))
        p, codes, _ = audit(d, delivery=False)
        assert not p, f"lab sem contrato não pode reprovar: {p}"
        p, codes, _ = audit(d, delivery=True)
        assert "wrong_visual_epoch" in codes, f"entrega sem contrato deveria reprovar: {codes}"
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print("[SELF-CHECK OK] visual_delivery "
          "(entrega válida passa; D1/probe/HAMOOPIG/duplicata/escala/HUD/binding "
          "reprovam; 320×224 recusado)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    ap.add_argument("--contract")
    ap.add_argument("--delivery", action="store_true",
                    help="intenção de entrega: contrato ausente e epoch≠delivery REPROVAM")
    ap.add_argument("--json")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.self_check:
        return _self_check()
    problems, codes, report = audit(args.project, args.contract, args.delivery)
    if args.json:
        json.dump({"problems": problems, "blocker_codes": codes, "report": report},
                  open(args.json, "w"), indent=2, ensure_ascii=False)
    if problems:
        for p in problems:
            print(f"[FAIL] {p}")
        print("blockers: " + ",".join(codes))
        return 1
    print("[OK] visual_delivery")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
