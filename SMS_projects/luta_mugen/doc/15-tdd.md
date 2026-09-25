# 15-tdd — luta_mugen

> Arquitetura técnica. Autoridade #7.
> A API definitiva é o header (`sdk/devkitSMS/SMSlib/SMSlib.h`, autoridade #8) —
> este documento NUNCA inventa assinatura. Em dúvida: leia o header.
>
> Rascunho S3 (2026-09-25): toda grandeza de hardware abaixo tem fonte citada;
> todo número de personagem vem de `out/local_study/s3_fidelity_ken.json`
> (medido por `mugen2sms/analysis/`, reproduzível). Cadeia de status:
> `documentado ≠ implementado ≠ buildado ≠ testado_em_emulador ≠ validado_budget`
> — nada daqui passou de **implementado com testes Python**; ROM ainda não existe.

## Restrições assumidas (herdadas, sempre ativas)
```
❌ float/double em runtime quente  — SDCC Z80 faz float em software; use int16/Q8.8
❌ malloc / free                   — buffers estáticos; RAM = 8 KB
❌ VRAM em massa fora do VBlank    — sem DMA
❌ >8 sprites/scanline, >64 na SAT
```

## Grandeza de hardware, com fonte (L001: proibido número de outro console virar lei do SMS)

| Grandeza | Valor | Fonte |
|----------|-------|-------|
| Sprites por scanline | 8 | doutrina AGENTS.md; `audit_sprite_line_sim.py` |
| Capacidade da SAT | 64 entradas | devkitSMS `SMSlib/src/SMSlib_common.c:21` `#define MAXSPRITES 64`; esgota → `SMS_addSprite_f` retorna −1 (`SMSlib.h:199`) |
| Sprite alto 8×16 | `SPRITEMODE_TALL` | `SMSlib.h:57` |
| Metasprite | `SMS_addMetaSprite`, `METASPRITE_END=0x80` | `SMSlib.h:214-216` |
| Tile | 8×8 @ 4bpp = 32 B | `SMSlib.h:130` (`(tilefrom)*32`) |
| Subpaleta | 16 índices, 0 transparente → 15 úteis | `SMSlib.h:131`; AGENTS.md |
| Name table visível | 32×24 = 768 tiles | 256×192 / 8×8 |
| VRAM | 16 KB | VDP |
| RAM | 8 KB | Z80 |

Codificado em `tools/sms_wrapper/mugen2sms/analysis/sms_budget.py::SmsLimits`
(uma linha de comentário-citação por campo; `--self-check` embutido).

## Pipeline de dados (S0–S4 = Plano 1; S5–S6 = Plano 2)

```
pacote MUGEN (zip/pasta, somente-leitura)
  → mugen2sms.source.Source            [S2 ✔]
  → parsers (ini/sff/air/cns/cmd/snd)  [S2 ✔]
  → Character IR + report              [S2 ✔]
  → analysis/sms_budget + fidelity     [S3 ✔ — este documento]
  → converters (tiles/clsn/cmd/sound)  [S4]
  → generators SMS (C + .res)          [S4]
  → runtime interpretador de tabelas   [Plano 2]
```

IR não conhece SMS; generators não leem MUGEN (invariant herdada do doador MD).

## Ken Masters ADV medido contra o VDP (fonte: `s3_fidelity_ken.json`)

Totais por classe: **direct 2273 · approximate 317 · manual 93 · unsupported 297**
(3080 elementos; cada um com `motivo`).

| Categoria | direct | approximate | manual | unsupported | motivo dominante |
|-----------|--------|-------------|--------|-------------|------------------|
| sprite (463) | 447 | — | 16 | — | `paleta>15uteis` (16 sprites com >15 cores) |
| pose/frame (934) | 448 | 243 | — | 243 | `scanline>8` (243); `sat>64` (232 — efeitos 320×240 de intro/victory); `sprite-ausente` (11 — referenciam sprites de sistema ausentes do .sff do personagem) |
| clsn (662 frames com caixas) | 662 | — | — | — | colisão em software Z80, sem custo de VDP |
| comando (91) | 14 | — | 77 | — | `botao>pad` — MUGEN usa b/c/x/y/z; pad SMS tem 1 botão |
| som (33) | — | — | — | 33 | `pcm>psg` — PCM não existe no VDP |
| controlador de estado (796) | 702 | 73 | — | 21 | unsupported: 17 blending/rastro, 2 fightfx, 1 paleta-RAM dinâmica, 1 multiplicador não modelado |

Distribuição de largura de sprite (colunas de 8 px): mediana 69×83 px;
**270/463 sprites (58%) têm >8 colunas** — a arte MUGEN é maior que a tela SMS.

### VRAM (pool de tiles)
- Tiles brutos: 67.501 · **dedup 8×8: 36.401 únicos = 1.164.832 B** vs 16.384 B de VRAM.
- Conclusão medida: **personagem inteiro nunca reside**; streaming por pose é obrigatório
  (padrão MSSF2T: arte em banks, upload só no VBlank).
- Orçamento por pose jogável (pós-corte ≤8 col × ≤8 linhas altas): ≤64 tiles = **≤2 KB
  de tiles ativos por frame**, sobrando ≥8 KB para BG + sprites do cenário.

### ROM e banking
- Estimativa da seleção jogável: ~120 poses finais × ~40 tiles × 32 B ≈ **150 KB só de arte
  de UM lutador** (dedup intrapersonagem já embutido na contagem de tiles únicos).
- 2 lutadores + cenário + código ⇒ **estoura qualquer mapa linear**; banking Sega mapper
  (páginas 16 KB, dados a partir de BANK1, streaming só no VBlank) — mesmo padrão do spec
  de banking do MSSF2T. Status: **bancado** (decisão tomada por medição, não por medo).

## Corte jogável (decisão explícita do que entra no MVP)

| Furo medido | Decisão |
|-------------|---------|
| sons PCM (33, todos unsupported) | **Nada porta direto.** Reautoria PSG: 6 SFX (soco, chute, especial, hit, KO, round) + 1 BGM, declarados em manifest de áudio. Ken audível = zero PCM. |
| comandos com b/c/x/y/z (77) | **Remapeio manual**: tabela de comandos do runtime só aceita {direções, A, start}; combo especial passa para QCB+A etc. na faixa `manual`, reautorado 1 lutador. |
| `scanline>8` (243 poses) | **Escala travada 2026-09-25 (GDD §Escala do lutador)**: TALL 8×16, lutador ≤4 sprites/linha × ≤3 de altura (~32×48 px), downscale 1:4 fixo no conversor; quem ainda estourar vira `manual` (reautoria) e não entra no build. Flicker para mascarar overflow é proibido. |
| `sat>64` (232 frames de efeito) | **Fora do MVP** — intros/victory screens fullscreen não cabem na SAT; ficam no IR como documentação do acervo. |
| `sprite-ausente` (11 frames) | **Fora** — dependem de sprites de sistema (fightfx) que não estão no pacote do personagem. |
| paleta >15 úteis (16 sprites) | Quantização no conversor + revisão visual; `manual` até passar em `audit_validate_resources`. |
| controladores unsupported (21) | 17 blending/rastro → substituídos por sprite-extra ou omitidos; 2 fightfx → omitidos; 1 flash de paleta → CRAM dinâmica no VBlank se sobrar tempo; 1 multiplicador → fora do escopo (sem dano variável no MVP). |
| 12 paletas do .act | P2 (dummy) = **shift de faixa de índice** no MESMO sprite palette (o SMS tem UMA paleta de sprite; sem escolha por sprite — SMSlib.h:249-250). Paletas ACT de P1/P2 devem caber em 15 úteis conjuntas; custo = cópia dos padrões com índices deslocados (medido no Plano 2 Task 2), não zero. |

## Mapa de memória (RAM) — candidatos, a fechar no Plano 2 com o runtime escrito
| Faixa | Tamanho | Conteúdo |
|-------|---------|----------|
| — | — | (fechado em S5; nenhum byte acima de 8 KB será declarado sem pool nomeado) |

## Entidades e pools (estáticos) — orçamento inicial em jogo
| Pool | Máx | Bytes/entidade | Total |
|------|-----|----------------|-------|
| lutador+helper (Q8.8 pos/vel, estado, anim, timer, vida, flags) | 4 slots | 32 B | 128 B |
| stack da VM de condições (IR `vm.py`) | 2 × 32 | 1 B/entry | 64 B |
| staging de tiles p/ upload no VBlank | — | 512 B | 512 B |
| buffers do SMSlib (SAT, name table espelho) | — | (SMSlib aloc; ~2 KB) | — |

**Regra:** nenhum pool entra no build sem linha medida no worst-frame
(`measure_worst_frame.py`), padrão MSSF2T.

## Máquina de estados
_(runtime — Plano 2; o IR por estado já é interpretável: 126 estados de Ken medidos,
origem 99 personagem + 27 common_forge)_

## Banking
- Alvo inicial: **48 KB linear sem mapper** (B01) → **reprovado por medição S3**
  (só a arte do corte de 1 lutador ≈ 150 KB).
- Adotado: **mapper Sega** (páginas 16 KB, regs 0xFFFE/0xFFFF), código ≤32 KB,
  dados a partir do bank 1, streaming apenas no callback de VBlank.
- Status atual: **decidido (bancado), não implementado**.

## Áudio
- Driver: PSGlib (`sdk/devkitSMS/PSGlib/PSGlib.h` é a autoridade).
- Arbitração de canais SFX vs música (só 4 canais) — declarar explicitamente:
  _(canal que cede: SFX em A+B, música cede A/B no hit; fechar no Plano 2)_
- YM2413/FM é **opcional**: o jogo tem que funcionar sem ele.
- Medido: 33/33 sons PCM → **zero bytes portados**; só reautoria PSG entra.

## Orçamento de frame
_(quem escreve na VRAM, quanto, e dentro de qual janela — fechar em S5/S6 com
`measure_worst_frame.py`; entrada: pose ativa ≤2 KB de tiles, BG 768 tiles)_
