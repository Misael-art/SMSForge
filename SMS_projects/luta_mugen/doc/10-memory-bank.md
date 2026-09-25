# 10-memory-bank — luta_mugen

> ESTADO OPERACIONAL REAL. **Autoridade #1** — vence qualquer outra fonte.
> Registre o que FOI OBSERVADO, nunca o que se pretende. Estado de sessão
> não substitui este arquivo.

## Última atualização
2026-09-25 — Plano 1 (S0–S4) executado e commitado no branch
`feat/luta-mugen-motor`; checkpoint S3 aprovado pelo usuário ("prossiga");
decisão de escala do lutador TRAVADA pelo usuário (TALL 8×16, ~32×48 px) e
registrada no GDD. Nada passou de Python-testado: não existe ROM.

## Eixos de entrega (7) — gate final exige os 7 simultâneos
| Eixo | Status | Prova |
|------|--------|-------|
| build | não iniciado | nenhuma ROM compilada; `build_inner.py` ainda não foi invocado neste projeto |
| validation_report | não iniciado | gates de resources/sprite-line só rodam no round local Ken (fora do Git); projeto sem `res/` próprio |
| boot no emulador | não iniciado | — |
| gameplay | não iniciado | — |
| 60/50 fps | não iniciado | — |
| áudio | não iniciado | PCM classificado unsupported; reautoria PSG (6 SFX + 1 BGM) ainda não escrita |
| memory bank atualizado | implementado | este arquivo, nesta data |

> Vocabulário: `documentado ≠ implementado ≠ buildado ≠ testado_em_emulador`.
> O motor (ferramentas) está em `implementado com testes Python` — 63/63 verdes
> (`tools/sms_wrapper/mugen2sms/tests/`, executado 2026-09-25). Isso NÃO é
> eixo de entrega do jogo.

## O que FOI OBSERVADO (Plano 1)
- S0–S4 commitados: `4166868` (S0), `6b181f2` (S1), `f773b05` (S2),
  `db70051` (S3), `2d3a326` (S4). Cópia doada sob contrato de paridade
  (`doc/doacao_md_mugen2sms.json`, 34 arquivos, pino por SHA).
- Ken `ken_masters_adv` parseia inteiro: 463 sprites / 161 animações / 934
  frames / 1.526 clsn / 91 comandos / 126 estados / 33 sons, 0 erros de parse
  (medido por `ken_full_parse.py` contra o acervo local, fora do Git).
- Fidelidade medida (S3): 2.273 direct / 317 approximate / 93 manual / 297
  unsupported. VRAM: 36.401 tiles únicos dedup = 1,16 MB vs 16 KB → streaming
  por pose obrigatório.
- **Gate do harness REPROVA o corte nativo**: pior pose × 2 lutadores =
  pico 32/scanline (teto 8), SAT 256 (teto 64)
  (`out/local_study/generated/s4_generation_report.json`, gitignored).
  Veredito `FAIL` registrado, não contornado.
- Resposta à reprovação é decisão HUMANA, tomada em 2026-09-25: escala
  travada TALL 8×16, lutador ≤4 sprites/linha × ≤3 colunas (≈32×48 px em
  tela), downscale 1:4 fixo no conversor, pose que estourar vira `manual`,
  flicker proibido. Está no GDD §"Escala do lutador" e no TDD §"Corte
  jogável". O conversor AINDA NÃO aplica o contrato — é a primeira tarefa
  do Plano 2, com gate (o mesmo `audit_sprite_line_sim` que deu FAIL deve
  dar PASS com a escala aplicada).

## Decisões registradas
- Motor = ferramentas em `tools/sms_wrapper/mugen2sms/`; runtime interpreta
  tabelas compiladas; CNS-em-runtime recusado (2026-09-25).
- Banking Sega mapper decidido (ROM ≈150 KB/lutador medido no round S4).
- P2/dummy = shift de faixa de índice no MESMO sprite palette (o SMS tem uma única
  paleta de sprite; custo de padrões duplicados medido no Plano 2, não "zero").
- Áudio: zero PCM portado; 6 SFX + 1 BGM reautorizados em PSGlib.
- Licença: arte real do Ken nunca entra no Git; derivativos só em
  `out/local_study/` (gitignored); fixtures sintéticos são os únicos dados
  MUGEN-like no repo.
- Escala do lutador travada (ver acima) — decisão do usuário, não do agente.

## Blocker dominante atual
Aplicar o contrato de escala no conversor/generador e re-medir a pior cena
(FALHA conhecida: 32/linha → alvo ≤8/linha com folga zero-de-flicker).
Tudo depois disso (S5 runtime, cena 02) depende deste número verde.

## Lições abertas
- L-aberta-1: `validate_measurement_tools.py` descobre ferramentas por prefixo
  `audit_`/`measure_` na raiz do wrapper; as ferramentas do mugen2sms não são
  alcançadas. Curadoria pendente (registrar no discovery ou criar wrapper) —
  só com aprovação humana explícita.
- L-aberta-2: downscale 1:4 em arte de 69×83 px mediana produz ~17×21 px —
  silhueta de lutador pode definhar. A prova é visual, no emulador (S5), não
  na planilha. Hipótese: recorte por boneco (remake de pose) pode substituir
  downscale bruto em poses-chave. Ferramenta que fecha: `audit_render_fidelity`
  + evidência capturada na cena 01.

## Handoff
Executar `doc/plan-2-runtime-s5-s6.md` (a ser criado nesta sequência:
T2.0 escala no conversor → cena 01 probe → runtime S5 → golden slice S6).
Primeiro comando do próximo agente: ler o Plano 2, Task 0, e rodar os testes
focados de `mugen2sms` para confirmar baseline verde (63 passed).
