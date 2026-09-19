# 11-gdd — HAMOOPIG SMS

> Autoridade #2. Se não está aqui, não entra.

## Pitch (1 frase)
Engine de luta 1v1 HAMOOPIG reimplementada para Sega Master System: abertura, título, seleção, combate com FSM, caixas, rounds e HUD, dentro dos limites reais do VDP/Z80.

## Gênero declarado
fighting

## Loop central
Escolher lutadores → aproximar/afastar → normal ou especial → guarda ou hitstop → barra cai → KO/tempo → round → revanche ou título.

## 5 Leis
- **Agência**: D-pad move, B1 soco, B2 chute, recuar guarda, cima pulo; o sprite controlado desloca na direção comandada.
- **Feedback**: hitstop, barra, banner ROUND/FIGHT/K.O./DRAW/TIME, pose de golpe distinta da idle.
- **Fluxo**: P2 começa DUMMY; CPU e 2P humano existem no contrato de controle.
- **Consistência**: mesmo comando no mesmo estado produz o mesmo startup/active/recovery.
- **Recompensa**: round ganho, melhor de 3, pose de vitória, revanche.

## Cenas
| # | Nome | Escopo | Status |
|---|------|--------|--------|
| 0 | OPENING | Crédito HAMOOPIG/GameDevBoss + porta SMSForge | implementado |
| 1 | TITLE | B1 inicia | implementado |
| 2 | SELECT | P1 troca ID, B1 confirma; P2 opcional | implementado (stub visual) |
| 10 | FIGHT | Arena técnica, dois lutadores, rounds | implementado (arte técnica) |
| 11 | AFTER_MATCH | Resultado, B1 revanche, Pause título | implementado |

## Roster previsto (origem HAMOOPIG)
| ID | Nome | Papel | Arte no SMS |
|----|------|-------|-------------|
| 1 | Ryo | lutador originário da engine | silhueta técnica (placeholder) |
| 2 | Ken | presente na origem; pixels Capcom **não** entram | reservado; sem sprite comercial |
| 3 | Musgo | grappler autoral da origem | silhueta técnica (placeholder) |
| — | Kensaiden | protagonista próprio, **depois** do núcleo estável | não iniciado |

## Adaptação de input (recuo declarado)
Mega Drive: 6 botões. SMS: D-pad + 2 botões + Pause/NMI.
- B1 = soco / confirma / especial (QCF+B1). Especial aceita B1 **hold** enquanto o QCF ainda está nos 8 ticks de direção (não alarga o buffer).
- B2 = chute
- Recuar = guarda
- Pause = sair da luta para o título
Forças L/M/H colapsam em um normal por botão; distância ainda escolhe o move da tabela.

## Fora de escopo (desta fase)
- Copiar pixels/áudio comercial da origem (Ken arcade, MIDI/VGM de terceiros)
- YM2413/FM, 6 botões, SRAM, netplay, AAA
- Personagem Kensaiden antes do ciclo completo da engine

## Teto de claims aprovado
`protótipo jogável de engine de luta 1v1` com época visual **técnica**.
Não é paridade de pixels com Mega Drive. `ready_for_aaa` false.

## Contrato de engine
Núcleo não conhece nomes de golpes no tick: `FighterDef` / `MoveDef` compilados.
Contatos em snapshot; HUD/render só consomem o evento. Reset de round zera timers, hist, projéteis, hitstop e resultado.
