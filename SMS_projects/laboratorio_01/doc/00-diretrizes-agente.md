# 00-diretrizes-agente — laboratorio_01

> Regras de processo deste projeto. Autoridade #4.
> Criado em 2026-08-31 para fechar deriva detectada por `audit_doc_sync.py`
> (o arquivo era citado pela Hierarquia de Verdade do AGENTS.md mas não existia).

## Natureza deste projeto
`laboratorio_01` **não é um jogo**: é o fixture de validação do próprio SMSForge.
Existe para provar o pipeline inteiro (gates → build → runtime → evidência) numa
ROM real. Consequência prática: claims sobre ele são sobre a FÁBRICA, nunca
sobre qualidade de jogo.

## Ordem de leitura obrigatória
1. `AGENTS.md` da raiz do workspace
2. `.agent/rules/SMS_GLOBAL.md`
3. `doc/10-memory-bank.md` (estado operacional real — autoridade #1)
4. este arquivo

## Desvios locais aprovados
| Data | Desvio | Justificativa | Registro |
|------|--------|---------------|----------|
| 2026-08-26 | Cena 01 usa BG para o cursor em vez de sprite | L006 (sprite invisível) estava aberto; rota BG destravou a cena sem esperar a causa-raiz | `doc/10-memory-bank.md` §Cena 01 |
| 2026-08-30 | Sprites 8×8 (`SPRITEMODE_NORMAL`) em vez de 16×16 | causa-raiz do L006: `SPRITEMODE_TALL` não alinha com a base de sprite; 16×16 exige metasprite | `PLANO_CONTINUACAO.md` F1 |

## Teto de claims aprovado
**"protótipo de validação de pipeline"**. Proibido chamar de jogo, de demo
técnica AAA ou de qualquer superlativo — `audit_claims.py` reprova.

## Vocabulário obrigatório
`documentado ≠ implementado ≠ buildado ≠ testado_em_emulador ≠ validado_budget`.
O eixo áudio deste projeto está em **implementado** (blip PSG capturado em
`audio_psg.wav`); confirmação audível humana continua sendo o degrau seguinte.

## Ao encerrar sessão
Atualizar `doc/10-memory-bank.md` com o estado observado e o blocker dominante.
