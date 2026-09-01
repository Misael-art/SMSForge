# probe: early_clock — quantos pixels o SHIFTSPRITES desloca?

## PERGUNTA (falsificável, escrita ANTES do código)
`VDPFEATURE_SHIFTSPRITES` (registrador 0, bit 3 — SMSlib.h:29) desloca o sprite
**quantos pixels** para a esquerda? E `SMS_addSprite(x, ...)` armazena X+32,
como afirma a matriz de maestria S05?

## PREVISÃO (registrada ANTES de rodar — errar aqui é o achado)
1. O deslocamento é de **8 pixels**, não 32. "32" e "X+32" parecem herança do
   Mega Drive (offset de sprite 128 lá), não do VDP do Master System.
2. `SMS_addSprite(0, y, t)` desenha o sprite **na borda esquerda**, visível —
   ou seja, NÃO existe offset +32 embutido, e X<32 não esconde nada.

Se a previsão 1 falhar, a matriz está certa e eu estou errado.
Se acertar, S05 e S06 são fatos não pagos herdados do console errado (L001).

## MÉTODO
Duas ROMs idênticas exceto pelo feature ligado/desligado. Sprite de referência
em X=100. Mede-se a posição do sprite em cada captura; a diferença É a resposta.
Segunda âncora em X=0 responde a previsão 2.

## VEREDITO (2026-09-01) — **CONFIRMADO** nas duas previsões

Medição nas capturas (`out/evidence/shift_off.png`, `shift_on.png`):

| marcador | SHIFT OFF | SHIFT ON | conclusão |
|----------|-----------|----------|-----------|
| X=100 | x=[114..121] | x=[106..112] | **deslocou 8 px** |
| X=16 | x=[28..36] | x=[21..29] | deslocou 8 px |
| X=0 | x=[13..20] **visível** | **sumiu da tela** | X=0−8 sai pela esquerda |

**Previsão 1 confirmada:** `VDPFEATURE_SHIFTSPRITES` desloca **8 px**, não 32.
**Previsão 2 confirmada:** não existe offset +32. `SMS_addSprite(0, …)` desenha
na borda esquerda, visível; X=16 idem. A afirmação "X<32 esconde o sprite" é falsa.

**Consequência:** S05 e S06 da matriz carregavam números do **Mega Drive**
(offset de sprite 128 lá) — recorrência da L001, agora paga com evidência.
Registry atualizado para `emulador_provado` com as capturas citadas.

**Limite honesto:** medido no Emulicious, não em console real. Variação entre
revisões SMS1/SMS2 **permanece não testada** — se alguém precisar disso em
hardware, é um novo probe.
