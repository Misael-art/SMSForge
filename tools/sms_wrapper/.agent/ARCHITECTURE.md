# ARCHITECTURE.md — framework .agent do SMSForge

```
.agent/
├── rules/SMS_GLOBAL.md     ← lei canônica sempre ativa (seções numeradas)
├── skills/                 ← conhecimento por domínio (leia o que a tarefa exige)
├── workflows/              ← runbooks passo-a-passo
└── pipelines/              ← sequências machine-readable com gates
```

## Como usar
1. AGENTS.md da raiz é o contrato de entrada; SMS_GLOBAL.md é a lei.
2. Antes de trabalhar num domínio, leia a skill correspondente.
3. Siga o workflow do tipo de tarefa; pipelines definem gates obrigatórios.
4. Erro vira lição via workflow `curation-learning.md`.

## Princípios (herdados do SGDKForge)
- Decisão barata antes de arte cara; medição entre elas.
- Gate executável > confiança verbal.
- `.agent` local de projeto NÃO é sobrescrito pelo central (política de sobrescrita).
- Estado de sessão nunca substitui memory bank/GDD/TDD/evidência.
- Relatório não é entrega: `workflows/causal-persistence-loop.md`.
- Boot ≠ qualidade visual: `skills/sms-visual-excellence.md`.
- Até 3 ramos independentes: `skills/sms-harness-orchestration.md`.
- Review independente nos checkpoints: `workflows/independent-quality-review.md`.
- Produção contínua: `workflows/production-loop.md`.
- Lição só no ledger é prosa: `audit_learning_capture.py` (§43).
- Input neste host: `emulator_input.py` (kdotool+ydotool). XTEST não
  atravessa o KWin (L039).
- Tamanho de símbolo e redundância PSG: `audit_symbol_size_sync.py`,
  `audit_psg_redundancy.py`. Não torcer a demo (L053).
- Tradução pixel: `prepare_sms_pixel_art.py` / `sms-pixel-translate.md`.
  Paleta de outro console é régua (L055).

Números de Mega Drive não entram. Método sim (§32).

Engines MUGEN→SMS: `workflows/mugen-engine-quality.md`, pipeline
`pipelines/mugen_fighting_v1.json` e SMS_GLOBAL §68.
