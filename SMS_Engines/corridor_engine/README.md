# CorridorEngine — base reutilizável para shoot-em-up de Master System

Encapsula o que a cena04 do laboratório provou, para que novos protótipos
comecem 90% prontos em vez de reescrever.

## O que a engine dá

| Módulo | API |
|--------|-----|
| Setup (VDP/paleta/estrelas/sprites) | `engine_init()` |
| Música PSG (PSGlib) | `engine_set_music(song)` |
| Sprites 8×8 (entidades) | `engine_sprite_add/set/hide`, `engine_sprites_flush()` |
| Jogador (d-pad + tiro + invuln + flash) | `engine_player_update(keys,&hp,&over)` |
| Inimigos (pool, dificuldade progressiva) | `engine_enemies_update(frame)` |
| Projétil + colisão | `engine_bullet_fire/update` |
| Frame (vblank + PSG + input) | `engine_frame_begin()` |
| Render (HUD + scroll/shake + game over) | `engine_render(frame,hp,over)` |
| SFX | `engine_sfx_hit/shot/destroy` |

## Layout de VRAM (fixo)
- tiles 128..131: jogador (hero), inimigos, projétil
- tile 132: estrela (BG)
- paleta mestra SMSForge (16 entradas, índice 0 transparente)

## Como usar um protótipo

```c
#include "engine.h"
#include "music_battle.h"

void main(void){
    unsigned int keys; unsigned char hp=3, over=0;
    engine_init();
    engine_set_music(music_battle);
    engine_sprite_add(40,80,128);
    engine_enemies_reset();
    for(;;){
        keys=SMS_getKeysStatus();
        engine_frame_begin();
        if(!over) engine_update(keys,&hp,&over);
        else if(keys & PORT_A_KEY_1){ hp=3; over=0; engine_player_reset(40,80); engine_enemies_reset(); }
        engine_render(engine_frame_count(), hp, over);
    }
}
```

Veja `example_proto.c` (compila e roda — prova de reutilização).

## Build
```sh
cd SMS_Engines/corridor_engine
./build_proto.sh example_proto.c proto
# -> build/proto.sms
```
Requer toolchain instalada (`tools/sms_wrapper/ensure_toolchain.sh`).

## Prova (observada)
- `proto_engine.sms` roda no Emulicious a 60fps (título 100%).
- Jogador sprite visível + música 97% ativa (protótipo).
- Matriz: originalmente portada da cena04 (`SMS_projects/laboratorio_01`).

## Notas SMS hard (L006)
- Sprites usam `SPRITEMODE_NORMAL` 8×8; para 16×16 use metasprites (4× 8×8).
