# workflow: production-loop

Pipeline de uma iteração SMS: design → arte → runtime → QA → evidência.
A jornada de cena vive em `pipelines/aaa_scene_v1.json`.

Nenhum passo abaixo autoriza encerrar a execução após diagnóstico, correção
de ferramenta, relatório, build isolado, captura ou um único milestone.

## 0. Continuidade

- Pedido de produção contínua → `causal-persistence-loop.md`.
- Dois ramos independentes → `harness_orchestration.py` (máx. 3:
  visual / runtime / audio_qa). Claim permanece no coordenador.
- Checkpoints foundation / vertical_slice / RC → `independent-quality-review.md`.

## 1. Escopo

GDD (`doc/11-gdd.md`) trava o que entra. Feature fora do GDD não entra.
Divergência GDD↔fork: registrar decisão e harmonizar GDD/TDD/spec/memory bank
**antes** de crescer.

## 2. Arte (visual-first)

Skill: `sms-visual-excellence.md`. Workflow: `new-visual-asset.md`.
PNG indexado válido ≠ qualidade. Epoch `probe`/`technical_d1` não promove.
Gate: `audit_visual_delivery.py --delivery` + `audit_rom_asset_binding.py --require`.

## 3. Runtime

Skill: hardware/budget + input. Build pelo wrapper. Pre-gates do `build_inner.py`.
Não tratar planejamento offline como `validado_budget`.

## 4. Evidência

`evidence-protocol.md`. Captura de boot classifica no máximo
`runtime_probe_passed_visual_epoch_failed` até o gate visual passar.
SHA da ROM no bundle tem de ser o da ROM que rodou.
Gameplay: direção + identidade + escala nativa (§29). Scale da janela
é entrada do gate, não detalhe de UI (L040).

## 5. Áudio

`new-audio.md` + `audit_audio.py` / `capture_audio.py`. PSG, não XGM2.

## 6. Fechamento de iteração

Memory bank atualizado com: claim ativo, blocker folha, última rota, delta,
rotas encerradas, próxima ação causal, gate humano pendente.
Não declare `ready_for_aaa=true` enquanto visual delivery, binding, gameplay,
áudio, budget medido e regressão não estiverem pagos.
