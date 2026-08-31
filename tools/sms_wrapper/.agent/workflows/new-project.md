# workflow: new-project

```sh
tools/sms_wrapper/new_project.sh <slug>
```
1. Instancia `SMS_projects/<slug>/` do modelo (`.agent` local não sobrescrito).
2. Preencher `doc/11-gdd.md` (escopo travado) — humano aprova.
3. Preencher `doc/15-tdd.md` (VRAM layout, pools, FSM).
4. Primeiro ciclo: `./build.sh` (deve falhar honesto se toolchain ausente).
5. Registrar no memory bank do projeto o status REAL dos 7 eixos.
