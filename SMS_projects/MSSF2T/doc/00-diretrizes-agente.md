# 00-diretrizes-agente — MSSF2T

> Regras locais. Autoridade #4. Lei global permanece em
> `tools/sms_wrapper/.agent/rules/SMS_GLOBAL.md`.

## Ordem de leitura
1. `AGENTS.md` da raiz
2. `SMS_GLOBAL.md`
3. `doc/10-memory-bank.md`
4. este arquivo

## Regra de ferro
**"Se não foi visto rodando no emulador, não existe."**

## Desvios locais
| Data | Desvio | Justificativa | Aprovado por |
|------|--------|---------------|--------------|
| 2026-09-06 | Fan demake de SSF2T (IP Capcom) | Projeto local de teste; proveniência `reference_only` nas sheets; ROM de entrega usa pixel SMS-nativo derivado, nunca o rip | pedido humano explícito |
| 2026-09-06 | 2 botões no lugar de 6 | Hardware SMS. B1=soco, B2=chute, QCF+B1=especial | GDD |

## IP / proveniência
`art_src_base/` é **régua e referência**. Role `reference_only`.
Não entra em `res/` sem tradução nativa (SMS_GLOBAL §15/§39).
Capcom permanece dona de Street Fighter. Este projeto não declara originalidade de IP.
