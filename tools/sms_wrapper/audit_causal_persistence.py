#!/usr/bin/env python3
"""audit_causal_persistence.py — oráculo da persistência causal (porte do SGDKForge).

Porta o MÉTODO, não o número: duas falhas equivalentes encerram a ROTA, nunca
o projeto; mismatch de representação não é gate humano; blocker irrelevante
não paralisa o claim ativo.

Uso:
  audit_causal_persistence.py <state.json>
  audit_causal_persistence.py --self-check
Exit: 0 decisão computada / self-check ok | 1 estado inválido | 3 uso
"""
from __future__ import annotations

import json
import sys
from typing import Any, Dict, List, Optional

DESTRUCTIVE_ACTIONS = {
    "force_reset", "delete_project", "overwrite_asset", "rm_rf",
    "git_push_force", "modify_header", "external_network_call",
    "release_publish",
}
REPETITION_LIMIT = 2
CAUSAL_CLASSES = {
    "implementation_failure",
    "tool_capability_failure",
    "interaction_channel_mismatch",
    "representation_mismatch",
    "scale_density_mismatch",
    "environment_failure",
    "contract_or_spec_conflict",
    "human_decision_required",
    "asset_content_mismatch",
    "evidence_script_tuned_to_pass",
}
DELTA_VOCAB = {"pending", "advanced", "no_change", "regressed", "stale_anchor"}


def _equivalent_attempts(state: Dict[str, Any]) -> bool:
    return (state.get("used_equivalent_attempts", 0) or 0) >= REPETITION_LIMIT


def _delta_measured(state: Dict[str, Any]) -> bool:
    after, before = state.get("evidence_after"), state.get("evidence_before")
    if not after or not before:
        return False
    return after != before


def decide(state: Dict[str, Any]) -> Dict[str, Any]:
    """Vereditos: advance, retry_changed_representation, retry_scale_measurement,
    close_route, blocked_human, stop_unauthorized, stop_exhausted,
    invalid_causal, invalid_state."""
    delta_status = state.get("delta_status")
    cause = state.get("cause")

    if delta_status not in DELTA_VOCAB:
        return {
            "verdict": "invalid_causal",
            "reason": "delta_status_not_in_vocabulary",
            "message": f"delta_status '{delta_status}' fora do vocabulário causal.",
        }
    if cause is not None and cause not in CAUSAL_CLASSES:
        return {
            "verdict": "invalid_causal",
            "reason": "cause_not_in_vocabulary",
            "message": f"cause '{cause}' não é classe causal.",
        }

    proposed = state.get("proposed_action")
    if proposed in DESTRUCTIVE_ACTIONS:
        return {
            "verdict": "stop_unauthorized",
            "reason": "destructive_action_without_authorization",
            "message": (
                f"Ação {proposed!r} é destrutiva/cara/externa e exige "
                "autorização humana explícita."
            ),
        }

    routes = state.get("available_routes") or []

    # Representação errada NÃO é gate humano — mesmo se alguém escreveu um.
    if cause == "representation_mismatch" and routes:
        return {
            "verdict": "retry_changed_representation",
            "reason": "representation_mismatch_change_representation_not_human",
            "message": (
                "A rota produziu a representação errada (dimensão, indexação "
                "ou grid). Mude a representação ou o produtor e tente de novo. "
                "Não peça o artefato a um humano."
            ),
        }

    if cause == "scale_density_mismatch" and routes:
        scale_status = state.get("scale_lock_status")
        if scale_status == "locked":
            return {
                "verdict": "retry_changed_representation",
                "reason": "locked_scale_requires_native_reauthoring",
                "message": (
                    "A escala travada é restrição de produto. Reautor clusters "
                    "no grid; probe maior é evidência, nunca substituto."
                ),
            }
        if scale_status == "provisional" and not state.get("scale_tradeoff_measured", False):
            return {
                "verdict": "retry_scale_measurement",
                "reason": "provisional_scale_tradeoff_unmeasured",
                "message": (
                    "Compare no máximo três caixas na pose e meça câmera, "
                    "hitbox, metasprite, tiles e pior scanline antes de pedir "
                    "decisão de produto."
                ),
            }
        if (
            scale_status == "provisional"
            and state.get("scale_tradeoff_measured", False)
            and state.get("scale_product_change_required", False)
            and state.get("human_gate_pending") is None
        ):
            return {
                "verdict": "invalid_state",
                "reason": "scale_change_requires_human_gate",
                "message": (
                    "A alternativa medida muda o contrato de produto; registre "
                    "a decisão humana em vez de avançar em silêncio."
                ),
            }

    if state.get("human_gate_pending") is not None:
        return {
            "verdict": "blocked_human",
            "reason": "human_decision_required",
            "message": (
                "Decisão humana obrigatória. Registre a pergunta e as opções; "
                "continue só os ramos independentes."
            ),
        }

    if not routes:
        return {
            "verdict": "stop_exhausted",
            "reason": "all_safe_routes_exhausted",
            "message": "Todas as rotas seguras e autorizadas foram esgotadas com evidência.",
        }

    if _equivalent_attempts(state) and not _delta_measured(state):
        return {
            "verdict": "close_route",
            "reason": "equivalent_repetition_no_new_evidence",
            "message": (
                f"{REPETITION_LIMIT} tentativas equivalentes sem evidência nova; "
                "feche a rota, não o projeto."
            ),
        }

    if state.get("artifact_kind") == "document" and state.get("blockers_removed", 0) == 0:
        return {
            "verdict": "close_route",
            "reason": "documentary_progress_not_causal",
            "message": "Documento/build com blockers_removed=0 não é progresso causal.",
        }

    if state.get("blocker_relevant") is False:
        return {
            "verdict": "advance",
            "reason": "blocker_irrelevant_to_active_claim",
            "message": "O blocker não limita o claim ativo; avance o claim.",
        }

    if _delta_measured(state) and delta_status in {"advanced", "no_change", "regressed"}:
        return {
            "verdict": "advance",
            "reason": "delta_registered",
            "message": "Delta medido; registre evidência e avance ou recategorize a causa.",
        }

    return {
        "verdict": "advance",
        "reason": "valid_state_retry_changed_route",
        "message": "Estado válido; tente uma hipótese causal e meça.",
    }


def _self_check() -> int:
    cases = [
        ("F1_tool_failure_safe_alternative", {
            "delta_status": "no_change",
            "cause": "tool_capability_failure",
            "evidence_before": "stage:rgba_raw",
            "evidence_after": None,
            "available_routes": ["pillow", "gimp_batch"],
            "used_equivalent_attempts": 0,
            "artifact_kind": "asset",
            "blockers_removed": 0,
            "blocker_relevant": True,
            "human_gate_pending": None,
        }, "advance"),
        ("F2_unproductive_repetition", {
            "delta_status": "no_change",
            "cause": "environment_failure",
            "evidence_before": "same",
            "evidence_after": "same",
            "available_routes": ["pillow", "gimp_batch"],
            "used_equivalent_attempts": 2,
            "artifact_kind": "asset",
            "blockers_removed": 0,
            "blocker_relevant": True,
        }, "close_route"),
        ("F3_human_gate_independent_branch", {
            "delta_status": "pending",
            "cause": None,
            "available_routes": ["fixture_tool"],
            "used_equivalent_attempts": 0,
            "artifact_kind": "asset",
            "blockers_removed": 0,
            "blocker_relevant": True,
            "human_gate_pending": {
                "decision_question": "aprovar silhueta?",
                "options": ["yes", "no"],
            },
            "independent_branches": ["fixture_tool"],
        }, "blocked_human"),
        ("F4_irrelevant_blocker", {
            "delta_status": "pending",
            "cause": None,
            "available_routes": ["pillow"],
            "used_equivalent_attempts": 0,
            "artifact_kind": "asset",
            "blockers_removed": 0,
            "blocker_relevant": False,
            "human_gate_pending": None,
        }, "advance"),
        ("F5_destructive_action", {
            "delta_status": "pending",
            "cause": None,
            "available_routes": ["pillow"],
            "used_equivalent_attempts": 0,
            "artifact_kind": "asset",
            "blockers_removed": 0,
            "blocker_relevant": True,
            "proposed_action": "overwrite_asset",
        }, "stop_unauthorized"),
        ("F6_exhaustion", {
            "delta_status": "no_change",
            "cause": "representation_mismatch",
            "evidence_before": "asset_v1",
            "evidence_after": "asset_v1_no_change",
            "available_routes": [],
            "used_equivalent_attempts": 0,
            "artifact_kind": "asset",
            "blockers_removed": 0,
            "blocker_relevant": True,
        }, "stop_exhausted"),
        ("F7_representation_not_human", {
            "delta_status": "no_change",
            "cause": "representation_mismatch",
            "evidence_before": "model_sheet",
            "evidence_after": "rgb_not_native",
            "available_routes": ["native_grid_stamp", "change_producer"],
            "used_equivalent_attempts": 0,
            "artifact_kind": "asset",
            "blockers_removed": 0,
            "blocker_relevant": True,
            "human_gate_pending": {
                "decision_question": "quem fornece a lineart nativa?",
                "options": [],
            },
        }, "retry_changed_representation"),
        ("F8_locked_scale", {
            "delta_status": "regressed",
            "cause": "scale_density_mismatch",
            "evidence_before": "identity_source",
            "evidence_after": "native_visual_fail",
            "available_routes": ["direct_native_cluster_redraw"],
            "used_equivalent_attempts": 0,
            "artifact_kind": "asset",
            "blockers_removed": 0,
            "blocker_relevant": True,
            "scale_lock_status": "locked",
        }, "retry_changed_representation"),
        ("F9_provisional_unmeasured", {
            "delta_status": "no_change",
            "cause": "scale_density_mismatch",
            "evidence_before": "native_fail",
            "evidence_after": "probe_pass",
            "available_routes": ["bounded_scale_probe"],
            "used_equivalent_attempts": 0,
            "artifact_kind": "asset",
            "blockers_removed": 0,
            "blocker_relevant": True,
            "scale_lock_status": "provisional",
            "scale_tradeoff_measured": False,
        }, "retry_scale_measurement"),
        ("F10_measured_product_scale", {
            "delta_status": "advanced",
            "cause": "scale_density_mismatch",
            "evidence_before": "unmeasured",
            "evidence_after": "bounded_comparison",
            "available_routes": ["keep", "adopt"],
            "used_equivalent_attempts": 0,
            "artifact_kind": "asset",
            "blockers_removed": 1,
            "blocker_relevant": True,
            "scale_lock_status": "provisional",
            "scale_tradeoff_measured": True,
            "scale_product_change_required": True,
            "human_gate_pending": {
                "decision_question": "adotar escala que muda câmera?",
                "options": ["keep", "adopt"],
            },
        }, "blocked_human"),
        ("doc_without_delta", {
            "delta_status": "no_change",
            "cause": "implementation_failure",
            "evidence_before": "a",
            "evidence_after": "a",
            "available_routes": ["rewrite_report"],
            "used_equivalent_attempts": 0,
            "artifact_kind": "document",
            "blockers_removed": 0,
            "blocker_relevant": True,
        }, "close_route"),
    ]
    failed = []
    for name, state, expected in cases:
        got = decide(state)["verdict"]
        if got != expected:
            failed.append(f"{name}: esperado {expected}, obtido {got}")
    if failed:
        print("[SELF-CHECK FAIL] " + "; ".join(failed))
        return 1
    print("[SELF-CHECK OK] causal_persistence "
          "(F1–F10 + documento sem delta: fecha rota, não projeto)")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args or args[0] in {"-h", "--help"}:
        print("uso: audit_causal_persistence.py <state.json> | --self-check",
              file=sys.stderr)
        return 3
    if args[0] == "--self-check":
        return _self_check()
    try:
        with open(args[0], encoding="utf-8") as fh:
            state = json.load(fh)
        decision = decide(state)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    print(json.dumps(decision, indent=2, ensure_ascii=False))
    # 0 = decisão computada (incluindo stop_*); 1 só para estado ilegível.
    return 0


if __name__ == "__main__":
    sys.exit(main())
