# DISPOSITION — schemas do wrapper (§32 aplicado a governança)

> "Portar metodologia de outro console é portar **método**, nunca número."
> Schema sem produtor nem consumidor é forma sem método. Registro da
> disposição feita em 2026-09-04, no pacote da L035
> (`doc/curation/2026-09-04_l035_canal_runtime.json`).

| Schema | Disposição | Motivo |
|--------|-----------|--------|
| `runtime_metrics_v1` | **ATIVO** — produtor no ar, e a instância é validada contra o schema antes de selar | `measure_runtime_probe.py` produz (canal DAP, L035) e, desde a ressalva de curadoria de 2026-09-04, abre o schema via `schema_guard.py` e recusa selar instância fora do contrato — `"schema": "runtime_metrics_v1"` deixou de ser string literal. Validador fail-closed: keyword JSON Schema fora do subconjunto implementado reprova em vez de ser ignorada. Schema evoluído no mesmo dia: `audio_active_pct` opcional (produtor próprio em `capture_audio.py`), campos de probe/axes/input_route adicionados. Não havia produtor nem consumidor na evolução — mudança sem quebra. |
| `scene_budget_frame_v1` | **REMOVIDO** | Órfão absoluto: a única ocorrência no repo era o próprio arquivo. Sem ferramenta que meça budget de frame por cena em runtime. Se a medição nascer, o schema se RE-DERIVA com o método (§32) — não se desenterra. |
| `production_visual_quality_v1` | **REMOVIDO** | Órfão absoluto: idem — zero referências, zero produtores. |
| `scene_budget_v1` | **MANTIDO COM DÍVIDA** | Referenciado por `.agent/pipelines/aaa_scene_v1.json`, `new-scene.md` e `13-spec-cenas.md` do laboratorio_01, mas NENHUMA ferramenta produz ou valida instâncias. Dívida registrada: produtor é o degrau seguinte do pipeline de cena. |
| `asset_contract_v1` | **MANTIDO COM DÍVIDA** | Referenciado por workflows/skills do asset pipeline e com uma instância escrita à mão (`laboratorio_01/doc/asset_contract_cena02.json`) — sem ferramenta que produza ou valide. Dívida registrada: validador é o degrau seguinte do pipeline de asset. |

Regra de manutenção: este arquivo é o registro; um schema novo entra aqui
com produtor declarado, e schema que perder o último consumidor volta para
disposição. Validador de instância vive em `schema_guard.py` — produtor que
cita schema sem validar contra ele é a ponta escrita sem travessia (a
ressalva que gerou o validador). Forma sem método não fica no repositório
sem dívida assinada.
