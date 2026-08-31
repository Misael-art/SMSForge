# SMS_Engines — engines reutilizáveis para jogos de Master System

Engines extraídas do laboratório e prontas para protótipos novos.

| Engine | Foco | Status |
|--------|------|--------|
| `corridor_engine/` | shoot-em-up/corredor: sprites, música PSG, scroll, jogador com tiro/invuln/flash, inimigos, HUD, game over | ✅ compilando e rodando (60fps) |

## Como usar
1. Escolha a engine (ex.: `corridor_engine`).
2. Escreva o `main.c` do protótipo incluindo o `engine.h` da engine.
3. Rode o `build_proto.sh` da engine.

Veja o README de cada engine. Todas seguem a lei do workspace
(`AGENTS.md` raiz): gates antes de runtime, evidência de emulador,
paleta mestra fixa, sprites 8×8 / metasprites (L006).
