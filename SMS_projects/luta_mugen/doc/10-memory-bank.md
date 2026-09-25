# 10-memory-bank — luta_mugen

> ESTADO OPERACIONAL REAL. **Autoridade #1** — vence qualquer outra fonte.
> Registre o que FOI OBSERVADO, nunca o que se pretende. Estado de sessão
> não substitui este arquivo.

## Última atualização
2026-09-25 (tarde) — Plano 2 Tasks 1–3 executadas: escala 1:4 aplicada no
conversor (S4.5a), formato de runtime SMS com metasprite TALL+espelhos (S4.5b,
commit `4313dd1`), e **cena 01 `probe_import` testada em emulador** com a
primeira ROM deste projeto (fixture sintético `mini`; Ken continua fora do Git).

## Eixos de entrega (7) — gate final exige os 7 simultâneos
| Eixo | Status | Prova |
|------|--------|-------|
| build | testado_em_emulador (cena 01) | `build.sh` → `out/rom/luta_mugen.sms` 16 KB, SHA `274d3109…d7b8` |
| validation_report | parcial | capture PASS, `audit_deterministic_boot` PASS (2 runs idênticos), `audit_render_fidelity` PASS 100%, `audit_sprite_line_sim` pico 4/linha SAT 8/64 sem violação, `measure_fps` 6×60 |
| boot no emulador | testado_em_emulador | `out/evidence/cena01_probe.png` — viewport variancia 818.2 |
| gameplay | não iniciado | input zero nesta cena (Task 5) |
| 60/50 fps | testado_em_emulador (cena 01) | `out/evidence/cena01_fps.json` (título do emulador; laço de frame ainda sem contador — probe SMRT vem na Task 4) |
| áudio | não iniciado | PCM classificado unsupported; reautoria PSG (6 SFX + 1 BGM) ainda não escrita |
| memory bank atualizado | implementado | esta seção, nesta data |

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

## O que FOI OBSERVADO (Plano 2 até Task 3)
- Leis de hardware MEDIDAS na cena 01 (não assumidas): par TALL
  `(pattern, pattern+1)` = (topo, base) — probe branco/preto mostrou branco em
  cima; origem de `SMS_addMetaSprite` = 1ª linha visível do topo da pose;
  espelho-h renderiza como OUTRO padrão (METAL no oponente); fixture com
  trailer de paleta PCX + `same=0` no subheader produz PAL visível (0x25).
- O harness `capture_evidence.py` reprova cena cujo conteúdo fica FORA da
  metade central da imagem (viewport box = canvas x64..191, y29..137) — a cena
  01 foi recentrada (chão na linha 16, lutadores x=96/152) em vez de maquiar o
  gate.
- `-set Update=0` do Emulicious só pinta depois do primeiro redraw (~2 s de
  Java): burst de capturas precisa aguardar a janela existir E o floor aparecer.
- Ken redondo S4.5b: 3.921 artefatos / 376.226 B (+199.396 B de espelhos — o
  custo real da ausência de flip), gate worst-scene PASS peak 8 / SAT 32.

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
O contrato de escala FOI aplicado e medido (S4.5a/S4.5b: gate worst-scene do
Ken PASS, pico 8/linha, SAT 32 — `out/local_study/generated/s4_generation_report.json`,
gitignored). Blocker novo, da cena 01: um bug de C no runtime (`meta_rebase`
comparando `unsigned char` com `(signed char)METASPRITE_END` = −128 → loop
infinito comendo a RAM) travou a ROM no frame 180 e foi diagnosticado LENDO
MEMÓRIA VIA DAP (PC preso em `_meta_rebase`, `g_frame` corrompido), não por
pixels. Corrigido e reverificado. Próximo gate real: interpretador FSM +
contador de frame com probe SMRT (Task 4) e input vivo (Task 5).

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
