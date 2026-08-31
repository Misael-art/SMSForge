# workflow: curation-learning

Quando algo dá errado (gate furado, lição paga cara, regressão):
1. Escrever JSON canônico em `doc/curation/<data>_<tema>.json`
   (lesson id, evidence, tool_that_measures, rule_section).
2. APENDAR seção numerada em `.agent/rules/SMS_GLOBAL.md` (nunca renumerar antigas).
3. Se a lição é mensurável e não tem ferramenta → criar/atualizar gate +
   caso no selftest (§20). Regra vira medição, nunca só prosa.
4. Atualizar learning ledger com dedup_key.
5. Curadoria só altera wrapper/doc com aprovação humana explícita.
