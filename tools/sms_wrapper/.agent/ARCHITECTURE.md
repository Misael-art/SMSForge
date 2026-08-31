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
