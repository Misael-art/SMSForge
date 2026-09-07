# skill: sms-pixel-translate

Use quando uma foto, conceito ou arte de outro console precisar **entrar**
no contrato visual do Master System. Porta o MÉTODO da skill Hermes
pixel-art v2.0.0 (MIT: downscale NEAREST → Floyd-Steinberg no grid),
**nunca** a paleta NES/SNES/PICO-8/C64/Game Boy (§32/L001/L055).

Ferramenta: `prepare_sms_pixel_art.py`.

## O que entra

- Foto ou PNG truecolor em `rascunho/` (sha256 no manifesto).
- Pixel art de outro hardware usada como **régua** (escala, silhueta,
  densidade). Pixels só reentram com licença/proveniência.

## O que sai

PNG indexado, grid 8×8, índice 0 transparente, ≤15 úteis, RGB no
contrato canal×85. Ainda **não** é personagem/palco final: é tradução.
Gates: `audit_validate_resources.py`, `audit_luma_floor.py`,
`audit_provenance.py`. Entrega visual: `sms-visual-excellence.md`.

```
prepare_sms_pixel_art.py rascunho/foto.png rascunho/foto_sms.png --block 8 --size 256x192
prepare_sms_pixel_art.py rascunho/sprite.png rascunho/sprite_sms.png --block 1 --size 32x64
```

`--block 1` = já é pixel (só quantiza). `--block 8` = foto chunky no tile.

## Proibido (contaminacao de outro hardware)

- Preset `nes` / `snes` / `pico8` / `gameboy` / `arcade` 32 cores / `neon`.
- Paleta adaptativa de 32 cores (SNES). SMS = 15 úteis + idx0 por subpaleta.
- Dither que invente cor fora de {0,85,170,255}.
- MP4/GIF com chuva, neon, fireflies, snow como evidência de ROM ou como
  asset em `res/`. Cena `night/urban/snow` no máximo informa o GDD
  (atmosfera); o VDP não tem essas partículas de graça.
- Promover a saída desta ferramenta a lutador/boss/palco `delivery`
  sem model sheet e sem `audit_visual_delivery.py`.
- `tool:"code"` no manifesto para personagem — esta ferramenta **traduz**
  um original; o original precisa de proveniência.

## Relação com animação

Ciclos de sprite: `sms-sprite-animation.md` + `audit_animation_semantics.py`.
Não use `pixel_art_video.py` para fabricar walk/punch. Vídeo de mood não
substitui strip no grid 8×8.

## Atribuição

Método (quantizar DEPOIS do downscale para o dither cair no pixel final)
e a ideia de presets de época vêm da skill pixel-art v2 (dodo-reach / MIT,
paletas de Synero/pixel-art-studio). A paleta mestra é só a do SMS.
