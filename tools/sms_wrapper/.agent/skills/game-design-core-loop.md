# skill: game-design-core-loop

## 5 Leis Fundamentais (checar no GDD)
1. **Agência** — input visivelmente afeta estado.
2. **Feedback** — toda ação tem resposta perceptível (visual+áudio).
3. **Fluxo** — desafio acompanha habilidade; sem paredes de frustração.
4. **Consistência** — mesma regra, mesma resposta, sempre.
5. **Recompensa** — progressão sentida, não só narrada.

## Golden Path
Caminho principal desenhado em 3–5 beats ANTES de conteúdo extra.

## IA de inimigos
Matriz archetype × comportamento no GDD; FSM por inimigo no TDD;
pool estático. Nada de IA "emergente" sem medição.

## Game feel no SMS
hitstop curto (frames), knockback fixo, screen shake = offset de scroll global.
Tudo medido em frames — nunca "um tiquinho".

## Física por condição, não por rótulo
Integração de `y`/gravidade vale enquanto a **altura** pede, em qualquer
estado da FSM. Amarração a `ST_JUMP` deixa o ator pendurado quando um
golpe o tira do estado — e de lá ele anda, agacha e soca no ar (L050).
`airborne()` é altura, não enum.
