#!/usr/bin/env python3
"""harness_orchestration.py — planeja até 3 ramos independentes. Não spawna.

Porta o MÉTODO do SGDKForge: o coordenador é o único dono de claim, promoção,
gate humano, git e memória. Trabalho read-heavy independente pode ir em
paralelo (visual / runtime / audio_qa). Sobreposição de escrita volta ao
coordenador.

Uso:
  harness_orchestration.py plan --taskset <json>
  harness_orchestration.py --self-check
Exit: 0 plano válido | 1 contrato violado | 3 uso
"""
from __future__ import annotations

import argparse
import json
import sys

VERSION = "1.0.0"
MAX_PARALLEL = 3

LOCAL_ONLY = {
    "claim_decision", "promotion", "human_gate", "integration",
    "canonical_memory_update", "git_integration",
}
PARALLEL_OK = {
    "visual_production", "runtime_production", "audio_qa",
    "visual_review", "code_review", "inventory", "documentation_audit",
    "test_execution", "budget_analysis", "source_audit",
}
VALID_KINDS = LOCAL_ONLY | PARALLEL_OK | {
    "implementation", "documentation_update", "external_dependency",
}
LANES = ("visual", "runtime", "audio_qa")


class ContractError(ValueError):
    pass


def _writes_overlap(a, b):
    wa = set(a.get("write_paths") or [])
    wb = set(b.get("write_paths") or [])
    return bool(wa & wb)


def plan(taskset):
    if not isinstance(taskset, dict):
        raise ContractError("taskset_not_object")
    tasks = taskset.get("tasks") or []
    if not isinstance(tasks, list):
        raise ContractError("tasks_not_array")

    local, parallel, rejected = [], [], []
    for i, raw in enumerate(tasks):
        task = dict(raw)
        tid = task.get("id") or f"t{i}"
        kind = task.get("kind")
        task["id"] = tid
        if kind not in VALID_KINDS:
            rejected.append({"id": tid, "reason": f"unknown_kind:{kind}"})
            continue
        if kind in LOCAL_ONLY or task.get("owns_claim") or task.get("owns_promotion"):
            task["assignment"] = "coordinator"
            local.append(task)
            continue
        overlap = any(_writes_overlap(task, other) for other in parallel + local)
        if overlap or kind not in PARALLEL_OK:
            task["assignment"] = "coordinator"
            task["serialized_reason"] = (
                "write_overlap" if overlap else f"kind_not_parallel:{kind}"
            )
            local.append(task)
            continue
        task["assignment"] = "worker"
        parallel.append(task)

    # Teto de 3 ramos simultâneos; o resto entra na fila do coordenador.
    if len(parallel) > MAX_PARALLEL:
        overflow = parallel[MAX_PARALLEL:]
        parallel = parallel[:MAX_PARALLEL]
        for task in overflow:
            task["assignment"] = "coordinator"
            task["serialized_reason"] = "max_parallel_exceeded"
            local.append(task)

    lanes_used = []
    for task in parallel:
        lane = task.get("lane")
        if lane not in LANES:
            # Atribui a primeira faixa livre.
            for candidate in LANES:
                if candidate not in lanes_used:
                    lane = candidate
                    break
            else:
                lane = "visual"
        task["lane"] = lane
        if lane not in lanes_used:
            lanes_used.append(lane)

    return {
        "schema": "harness_plan_v1",
        "tool": {"name": "harness_orchestration", "version": VERSION},
        "coordinator_is_single_claim_owner": True,
        "coordinator_is_single_promotion_owner": True,
        "max_parallel": MAX_PARALLEL,
        "lanes": lanes_used,
        "coordinator_tasks": [t["id"] for t in local],
        "worker_tasks": [t["id"] for t in parallel],
        "rejected": rejected,
        "tasks": local + parallel,
        "claim_ceiling": "orchestration_diagnostic_only",
        "ok": not rejected,
    }


def validate_result(envelope):
    problems = []
    if envelope.get("artifact_kind") != "harness_worker_result":
        problems.append("artifact_kind deve ser harness_worker_result")
    if envelope.get("status") not in {"passed", "failed", "blocked", "stale", "needs_review"}:
        problems.append("status fora do vocabulário")
    if envelope.get("claim_ceiling") in {"ready_for_aaa", "aaa", "release"}:
        problems.append("worker não pode elevar claim_ceiling")
    if envelope.get("promoted") is True:
        problems.append("worker não promove")
    return problems


def _self_check() -> int:
    plan_ok = plan({
        "tasks": [
            {"id": "v", "kind": "visual_production", "lane": "visual",
             "write_paths": ["res/sprites/a.png"]},
            {"id": "r", "kind": "runtime_production", "lane": "runtime",
             "write_paths": ["src/fight.c"]},
            {"id": "a", "kind": "audio_qa", "lane": "audio_qa",
             "write_paths": ["res/psg/hit.psg"]},
        ]
    })
    assert plan_ok["worker_tasks"] == ["v", "r", "a"], plan_ok
    assert plan_ok["coordinator_is_single_claim_owner"]

    claim = plan({"tasks": [
        {"id": "c", "kind": "claim_decision", "write_paths": ["doc/10-memory-bank.md"]},
        {"id": "v", "kind": "visual_review", "write_paths": []},
    ]})
    assert "c" in claim["coordinator_tasks"] and "v" in claim["worker_tasks"], claim

    overlap = plan({"tasks": [
        {"id": "v1", "kind": "visual_production", "write_paths": ["res/a.png"]},
        {"id": "v2", "kind": "visual_production", "write_paths": ["res/a.png"]},
    ]})
    assert overlap["worker_tasks"] == ["v1"], overlap
    assert "v2" in overlap["coordinator_tasks"], overlap

    too_many = plan({"tasks": [
        {"id": f"t{i}", "kind": "inventory", "write_paths": [f"out/i{i}.json"]}
        for i in range(5)
    ]})
    assert len(too_many["worker_tasks"]) == 3, too_many
    assert len(too_many["coordinator_tasks"]) == 2, too_many

    bad = validate_result({
        "artifact_kind": "harness_worker_result",
        "status": "passed",
        "claim_ceiling": "ready_for_aaa",
        "promoted": True,
    })
    assert any("claim_ceiling" in x for x in bad) and any("promove" in x for x in bad), bad

    good = validate_result({
        "artifact_kind": "harness_worker_result",
        "status": "passed",
        "claim_ceiling": "orchestration_diagnostic_only",
        "promoted": False,
    })
    assert not good, good

    try:
        plan({"tasks": [{"id": "x", "kind": "telepathy"}]})
    except ContractError:
        raise AssertionError("kind desconhecido deve ir para rejected, não explode")
    unknown = plan({"tasks": [{"id": "x", "kind": "telepathy"}]})
    assert unknown["rejected"] and not unknown["ok"], unknown

    print("[SELF-CHECK OK] harness_orchestration "
          "(3 ramos; claim no coordenador; overlap serializa; teto 3; "
          "worker não promove)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", nargs="?", choices=["plan", "validate-result"])
    ap.add_argument("--taskset")
    ap.add_argument("--result")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.self_check:
        return _self_check()
    if args.command == "plan":
        if not args.taskset:
            print("uso: harness_orchestration.py plan --taskset <json>", file=sys.stderr)
            return 3
        data = json.load(open(args.taskset, encoding="utf-8"))
        out = plan(data)
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0 if out["ok"] else 1
    if args.command == "validate-result":
        if not args.result:
            print("uso: harness_orchestration.py validate-result --result <json>",
                  file=sys.stderr)
            return 3
        data = json.load(open(args.result, encoding="utf-8"))
        problems = validate_result(data)
        if problems:
            for p in problems:
                print(f"[FAIL] {p}")
            return 1
        print("[OK] harness_worker_result")
        return 0
    print("uso: harness_orchestration.py plan|validate-result | --self-check",
          file=sys.stderr)
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
