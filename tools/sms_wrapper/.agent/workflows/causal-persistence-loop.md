# workflow: causal-persistence-loop

Use quando o pedido for continuidade até a entrega, quando um blocker se
repetir, ou quando uma ferramenta falhar e o agente estiver prestes a parar.

Oráculo executável: `tools/sms_wrapper/audit_causal_persistence.py`.
Relatório não é entrega. Depois de registrar o resultado, escolha a próxima
lacuna causal e continue.

## Ciclo

0. Inspecione o asset/VRAM **já carregado** antes de teorizar o VDP
   (L044). Alfabeto embutido no tileset não é estouro de VBlank.
   Classe: `asset_content_mismatch`.
1. Selecione o blocker folha que mais limita o claim ativo.
2. Registre `rota`, `hipótese`, `evidencia_antes` e resultado esperado.
3. Execute uma ação reversível.
4. Meça com a ferramenta dona do gate. Intenção não conta como delta.
5. Se passou: sincronize memory bank e avance.
6. Se falhou: classifique a causa e mude ferramenta, representação ou hipótese.

Classes: `implementation_failure`, `tool_capability_failure`,
`interaction_channel_mismatch`, `representation_mismatch`,
`scale_density_mismatch`, `environment_failure`, `contract_or_spec_conflict`,
`human_decision_required`, `asset_content_mismatch`,
`evidence_script_tuned_to_pass`.

## Limites

- Duas tentativas equivalentes sem evidência nova encerram a **rota**, não o projeto.
- Documento/build com `blockers_removed=0` não é progresso causal.
- Nunca reduza teste, budget, schema, gate visual ou claim para fabricar verde.
- Nunca afine o roteiro da atração/demo para o próprio teste passar (L053).
  Reporte o caminho como não observado.
- Representação errada (dimensão, indexação, grid) **não** é gate humano.
- Escala `locked`: reautor no grid. Probe maior é evidência, nunca substituto.
- Escala `provisional`: medir no máximo três caixas antes de pedir decisão.
- GUI por ponteiro / seletor de arquivos é `interaction_channel_mismatch`.
  Ordem SMS: Pillow/png_io → ImageMagick → GIMP **batch** registrado. Sem GIMP GUI.

## Gate humano sem paralisar

Registre a pergunta, as opções e o artefato. Continue só ramos cuja validade
não dependa da resposta. Não simule aprovação humana.

## Parada legítima

Pare somente se: ação destrutiva/externa/cara sem autorização; licença ausente;
contradição de autoridades que muda o produto; decisão humana irredutível sem
ramo independente; hardware impossível medido; rotas seguras esgotadas.

Relatório de parada nomeia blocker, tentativas distintas, evidências, teto de
claim e a menor próxima ação que desbloqueia.
