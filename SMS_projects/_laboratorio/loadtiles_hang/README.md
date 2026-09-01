# probe: loadtiles_hang — SMS_loadTiles trava mesmo?

## PERGUNTA (falsificável)
L009 item (3) afirma: "a cena trava DENTRO de `SMS_loadTiles` (marcador B1
alcançado, B2 nunca)". Isso é verdade? E depende da tela estar LIGADA durante o
load (a condição histórica: os loads vinham depois de
`SMS_autoSetUpTextRenderer`, que liga o display)?

## PREVISÃO (antes de rodar)
`SMS_loadTiles` **não trava** em nenhum dos dois casos. A ROM atual do
laboratorio_01 chama a função 4× e roda a 60fps. A hipótese de travamento era
consequência das duas armadilhas de depuração dos itens (1) e (2) da própria
L009 — marcador eliminado pelo SDCC e leitura DAP quebrada pelo prefixo `$` —
ou seja, **o instrumento estava mentindo, não a função**.

## MÉTODO (sem DAP — evita a armadilha do `$`)
Marcadores `volatile __at()` antes e depois do load, impressos NA TELA como
hexadecimal. Se o load travar, a tela não chega a mostrar M2.
Duas variantes: display LIGADO durante o load (condição histórica) e DESLIGADO.

## VEREDITO (2026-09-01) — **REFUTADO**

Marcadores lidos NA TELA nas duas variantes:

| variante | M1 (antes) | M2 (depois) | M3 (4 loads) | texto final |
|----------|-----------|-------------|--------------|-------------|
| display LIGADO no load | `A1` | `B2` | `C3` | `LOADTILES OK` |
| display DESLIGADO | `A1` | `B2` | `C3` | `LOADTILES OK` |

`SMS_loadTiles` **não trava** — nem com a tela ligada (a condição histórica),
nem com ela desligada, nem em quatro chamadas seguidas.

**Por que parecia travar:** pelas duas outras armadilhas da própria L009. O
marcador sem `volatile` era eliminado pelo SDCC (item 2) e a leitura DAP
quebrava no prefixo `$` (item 1). **O instrumento mentia, não a função.**
A previsão registrada antes de rodar se confirmou.

O ruído na tela é esperado: este probe não limpa a name table de propósito
(§30 — VRAM não nasce zerada), e isso não afeta o veredito, que se lê no texto.
