# workflow: analyze-existing-project

Modo `analyze_existing_project`. Objetivo: dizer o estado REAL de um projeto —
não o que a documentação dele afirma.

**Regra do modo: leia artefato antes de ler prosa.** O doc é a hipótese; o
artefato é o fato. Onde divergirem, o artefato ganha e a divergência é o achado.

1. `doc/10-memory-bank.md` do projeto (autoridade #1) — anote o que ele AFIRMA.
2. Rodar os gates de conciliação ANTES de acreditar em qualquer eixo:
   ```sh
   python3 tools/sms_wrapper/reconcile_claims.py --project SMS_projects/<slug>
   python3 tools/sms_wrapper/audit_doc_sync.py
   ```
3. Frescor da evidência (captura anterior à ROM mostra outro binário):
   ```sh
   python3 tools/sms_wrapper/seal_fresh_evidence_bundle.py \
       --rom <rom.sms> --artifact <cada captura citada>
   ```
4. Semântica das capturas citadas como prova:
   ```sh
   python3 tools/sms_wrapper/screenshot_semantic_gate.py <shot.png> --claim <eixo>
   ```
5. Build honesto: `./build.sh` — falha de toolchain é resultado, não erro do modo.
6. Produzir o veredito nos 7 eixos com o vocabulário de status
   (`documentado ≠ implementado ≠ buildado ≠ testado_em_emulador ≠ validado_budget`).
   Todo eixo precisa citar o artefato que o sustenta.

**Saída obrigatória:** lista de divergências doc↔artefato + o **blocker
dominante** (o item que, resolvido, destrava mais coisa).

**Proibido neste modo:** consertar o que você acabou de auditar na mesma passada.
Auditor que conserta perde a capacidade de reprovar. Reporte, e deixe a correção
para uma sessão com escopo próprio.
