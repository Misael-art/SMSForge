# skill: sms-harness-orchestration

Use quando houver dois ou mais ramos realmente independentes. Não spawna:
`harness_orchestration.py` só planeja.

## Política

- Máximo **três** ramos simultâneos: `visual`, `runtime`, `audio_qa`.
- Coordenador é o único dono de claim, promoção, gate humano, git e memória.
- Worker read-only por default; write_paths sobrepostos voltam ao coordenador.
- Worker não declara `ready_for_aaa` nem promove.
- Resultado compacto: status, evidência hash-bound, blockers, teto de claim.

## Quando NÃO delegar

Tarefa curta, claim, promoção, decisão humana, blocker de capacidade
compartilhada, writes no mesmo PNG/fonte, integração.

## Continuidade

Um blocker de arte não paralisa gameplay, áudio, palco, documentação ou QA.
Um blocker de captura não paralisa produção visual.
Siga `causal-persistence-loop.md`.
