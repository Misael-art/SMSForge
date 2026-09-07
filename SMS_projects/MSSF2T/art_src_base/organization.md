# Regras de organização da biblioteca SSF2T

## Nome de arquivo

```
<o_que>_<plataforma>_<jogo>_v<n>.<ext>
```

- `<o_que>`: lutador (`ryu`, `ken`, `honda`, `chunli`, `blanka`, `zangief`,
  `guile`, `dhalsim`, `balrog`, `vega`, `sagat`, `bison`, `thawk`,
  `feilong`, `deejay`, `cammy`), stage (`stage_<lutador>`),
  `select_character`, `versus_screen`, `continue_portraits`,
  `hud_fonts_healthbars`, `endings`, `effects_projectiles`.
- `<plataforma>`: `arcade` (CPS-2) ou `snes`. Sempre explícita.
- `<jogo>`: `st` (Super Turbo / X), `ce` (Champion Edition), `ww`
  (World Warrior). Marca a versão real da sheet, não a desejada.
  Sheets SNES (port New Challengers) omitem `<jogo>` e usam só `snes`.
- `<ext>`: reflete o formato REAL do arquivo (`png` ou `gif` — as 6
  sheets SNES de lutadores são GIF original; a conversão trata o formato).
- `_v<n>`: versão de sourcing (v1 = coleta 2026-09-06). Nova coleta do
  mesmo asset = v2, nunca sobrescreve v1 sem registrar.

## Onde mora cada categoria

| Categoria | Diretório |
|---|---|
| Lutadores e projéteis | `sprites/` |
| Cenários | `backgrounds/stages/` |
| Telas (select/versus/continue) | `title/screens/` |
| HUD, fontes, textos | `hud/` |
| Endings | `endings/scenes/` |
| Música (só índice, sem binário) | `audio/music/` |
| Movelists e notas | `manuals/docs/` |

## Proibido

- Arquivo de 0 bytes (placeholder sem conteúdo).
- Duas pastas para a mesma categoria (`characters/` removido; vale `sprites/`).
- Binário de áudio (MP3/OGG/WAV) como "asset" — ROM SMS usa PSG.
- Promover qualquer arquivo daqui a `res/` de projeto sem passar pelo
  fluxo canônico (`rascunho/` → contrato → model sheet → gates).
