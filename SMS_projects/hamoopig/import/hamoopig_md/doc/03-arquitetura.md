# 03 - Arquitetura

Arquitetura inicial:

- `src/main.c`: loop principal.
- `src/title.c` / `inc/title.h`: cena formal de título, menu principal e OPTION.
- `src/core/app.c`: inicializacao e roteamento de cenas.
- `src/system/input.c`: leitura de controles.
- `src/scenes/`: comportamento de cada tela.
- `src/game_vars.c`: estado global enxuto.

Principios:
- separar infraestrutura de gameplay;
- preferir funcoes pequenas e previsiveis;
- evitar logica escondida em variaveis globais sem contexto;
- manter o primeiro build simples e observavel.

Nota:
- menu e title screen devem ser tratados como cenas formais, com identidade visual coerente, ownership claro de display state e contrato de reset equivalente ao de gameplay.
