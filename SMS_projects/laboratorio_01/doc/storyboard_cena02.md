# Storyboard — cena 02 "sala do bloco" (planta baixa em pixel)

Grid 32×28 tiles (256×224). Moldura em 4..27 (x) / 4..25 (y). Coordenadas em células (1 cel = 8px).

```
y=4  +----------------------+
y=5  |                      |
y=6  |   P                  |
y=7  |                      |
y=12 |         [##]         |  ## = bloco 2x2 em (13,12)
y=13 |         [##]         |
y=18 |              ..      |  .. = alvo 2x2 em (18,18)
y=19 |              ..      |
y=25 +----------------------+
y=26   F:XXXX |/-\  (status)
```

Coreografia: P(12,12) empurra bloco se célula destino livre e não é parede; bloco só move se P empurra por trás.

Budget validado: pico 0 sprites/linha (BG puro) → simulador `audit_sprite_line_sim.py` com manifest vazio passa.
