# skill: sms-region-timing

## Regra
NTSC 60Hz / PAL 50Hz. Velocidade de jogo NORMALIZADA por frame counter
(accumulator com passo por região). Delay loops proibidos.

## Consequências
- Orçamento de VBlank difere entre regiões: pior caso manda (PAL tem janela maior,
  mas menos frames/segundo para o mesmo trabalho).
- Claim "60fps"/"50fps" constante exige medição + teto aprovado (`audit_claims.py`).
- Modo estendido de linhas (224/240) é decisão de TDD com fallback declarado.
- Line interrupt: armar o contador com N querendo a linha N+16 (recarga
  no VBlank) desloca todas as bandas. Ponha forma reconhecível na faixa
  — banda vazia não prova a quebra (L046).
