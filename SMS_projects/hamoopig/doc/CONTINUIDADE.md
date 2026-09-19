# CONTINUIDADE — HAMOOPIG SMS

- **Data:** 2026-09-19
- **Marco atual:** Etapa 1–2 observadas. Etapa 3 **especial+projétil observados** (ainda sem captura visual da bola no ar).
- **Último item concluído:** v006 QCF com `refocus=False` + B1 hold na janela de 8 ticks; dummy KO por projétil
- **Próximo item executável:** guarda (chip 2) e throw; PSG; worst-frame. Não alargar o hist.
- **Hash:** `4d6bfa4005b27412551fa3f8a041db813c69e163ce3dd2e7c8cf422cdb707964` (32768 B, build_v006)
- **Comandos:** `cd SMS_projects/hamoopig && ./build.sh`
- **Testes:** probe 59.42/59.42. special PASS (SP 32→4, fire=2, HP 8→0, hist 2-2-6-6).
- **Evidências:** `out/evidence/special_probe.json`, `runtime_probe.json`, `title.png`, `fight.png`
- **Adaptação:** especial aceita B1 hold enquanto QCF vive nos 8 ticks (não é hist maior).
- **Dívida:** áudio, arte, HUD completo, palco, guarda/throw, Kensaiden, git até commit humano se o add não for desejado
