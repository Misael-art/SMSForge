# skill: sms-sprites-metasprite

## Verdades duras
- Máx 64 na SAT; terminador Y=0xD0; máx **8 por scanline** (SMS1 corrompe linha no excesso).
- Tamanho GLOBAL 8×8 ou 16×16 (+ zoom ×2). Entidade grande = metasprite.
- X armazenado = X+32. Early clock e flips são revisão-dependentes → §23 (provar).
- API confirmada: `SMS_initSprites`, `SMS_addMetaSprite_f`, `SMS_copySpritestoSAT` (ver header).

## Fluxo obrigatório
coreografia → `audit_sprite_line_sim.py` (manifest sprite_scene_manifest_v1)
→ só depois runtime. Pico/linha entra no orçamento da cena.

## Truque canônico
Ordenar sprites na SAT para priorizar os importantes quando >8 ameaça uma linha
(flicker controlado > corrupção).
