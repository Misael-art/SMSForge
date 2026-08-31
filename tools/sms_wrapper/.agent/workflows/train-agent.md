# workflow: train-agent

Modo `train_agent`. Vive em `SMS_projects/_treino/`. Objetivo: elevar a
proficiência real do agente numa trilha da matriz de maestria — e **provar** que
subiu, em vez de afirmar.

Escada: `mapped → incorporada → reproduzível → emulador_provado → default_senior`.

1. Escolher UMA trilha e ler o nível atual em
   `doc/05_technical/01_registry_maestria_sms.json`. Sem alvo declarado não há treino.
2. Ler a skill do domínio em `.agent/skills/` antes de escrever qualquer linha.
3. Exercício com critério de aprovação declarado ANTES da execução — o que
   contaria como falha precisa estar escrito, senão qualquer resultado "passa".
4. Executar sem consultar a solução; erro é o material didático.
5. Comparar com a lei (`SMS_GLOBAL.md`) e com o header (autoridade #8).
   Todo erro cometido aqui é candidato a lição de curadoria — especialmente
   se a doutrina permitiu o erro.
6. Subir nível SÓ com evidência de emulador (§23). Treino não promove por esforço;
   promove por prova. `audit_mastery_registry.py` reprova nível sem `evidence`.

**Critério de pronto:** técnica exercitada com evidência citada, OU registro
honesto de que o nível NÃO subiu e qual foi o obstáculo.

**Anti-padrão:** treinar escrevendo documentação sobre a técnica. Documentar não
é saber fazer — o vocabulário de status separa `documentado` de
`testado_em_emulador` exatamente por isso.
