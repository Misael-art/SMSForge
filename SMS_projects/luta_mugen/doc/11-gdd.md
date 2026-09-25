# 11-gdd — luta_mugen

> Design e escopo. **Autoridade #2 — "se não está no GDD, não entra."**
> Aprovado por Misael em 2026-09-25 (caminho A: conversor com classes de
> fidelidade + runtime interpretador de tabelas). Briefing de origem:
> `Mugenesis/BRIEFING_AGENTE_LUTA_MUGEN_MEGA_DRIVE.md` — técnica doada para
> MASTER SYSTEM; o alvo aqui NÃO é Mega Drive.

## Pitch (1 frase)
Um MOTOR que consome arquivos MUGEN reais (`.def/.sff/.air/.cns/.cmd/.act/.snd`)
e produz lutadores, palcos e som jogáveis no Master System — provado com
`ken_masters_adv` vs outro lutador por dados, melhor de três rounds, sem tocar
no C do núcleo.

## Gênero declarado
fighting
(eixos congelados: hitboxes, startup_active_recovery, hitstop, rounds, specials, guard)

## Loop central
Aproximar/afastar → escolher normal ou especial → o oponente guarda ou leva
hitstop/knockback → barra de vida cai → KO → próximo round → melhor de 3.
Em cima deste loop: **loop de autoria** — trocar o arquivo de dados de um
lutador muda sprites, paletas, animações, frame data e especiais no build, sem
editar o runtime.

## 5 Leis Fundamentais — como este jogo atende
- **Agência**: d-pad move/pula/agacha, B1 soco, B2 chute, recuar = guard; cada
  input produz transição de estado legível no lutador comandado.
- **Feedback**: hitstop (frames congelados, valor por tabela de dados), faísca
  de impacto em sprite, SFX PSG no mesmo frame do contato, barra de vida caindo.
- **Fluxo**: no MVP, adversário dummy/espelho (IA mínima); a difficulty curve
  completa é pós-MVP declarada. O fluxo de autoria sobe: S2 (1 parse) → S5
  (luta) → S6 (contrato provado).
- **Consistência**: o mesmo arquivo de dados compila tabelas byte-idênticas
  (conversor determinístico com `--self-check`); o mesmo comando no mesmo
  estado produz o mesmo startup_active_recovery, sempre.
- **Recompensa**: round ganho → melhor de 3 → tela de resultado com revanche;
  no plano do motor: ver seu arquivo MUGEN virar lutador jogável.

## O que é o produto (contrato do motor)

```
tools/sms_wrapper/mugen2sms/   ← O MOTOR (lógica de build/transformação só vive aqui)
  inventory → parsers → ir → analysis → converters → generators → validate → reports
SMS_projects/luta_mugen/       ← CONSUMIDOR: runtime Z80 que INTERPRETA tabelas compiladas
```

- **IR não conhece SMS; generators não leem MUGEN.** (regra herdada do
  `mugen2sgdk_forge` do workspace Mega Drive, provada nas etapas E0–E3.)
- Parsers/IR do forge MD são **copiados** no S0 com SHA registrado
  (`doc/provenance_doacao_md.md` + `rascunho/`); a partir daí o fork SMS evolui
  próprio. Nenhum material ativo aponta para o workspace vizinho.
- **Não é VM de CNS.** O conversor destila estados CNS→tabelas por padrão
  reconhecido (estados, physics, command→special). O que não destila é
  classificado `manual` ou `unsupported` no relatório de fidelidade — gap
  visível, nunca silêncio.
- Classes de fidelidade obrigatórias em TODO recurso:
  `direct | approximate | manual | unsupported` (gate novo:
  `audit_mugen_fidelity.py`).
- Núcleo do runtime não conhece nomes: estados, frames (duração, metasprite,
  offset), clsn1/clsn2 → hurtbox/hitbox, janelas startup_active_recovery,
  comandos (buffer QCF+etc → specials), paletas e SFX vêm de tabelas
  compiladas offline dos arquivos MUGEN.
- Física (gravidade, knockback, hitstop) em inteiros/Q8.8; campos análogos do
  MUGEN (`velocity`, `changevelocity`) alimentam os dados; o resto é constante
  declarada no TDD.

## MVP — fatia golden travada

**Pilot:** `chars/street-fighter/ken_masters_adv.zip` (Ken/Chok). Autorizado
pelo usuário para **uso local** na decisão MD 2026-09-22; redistribuição segue
bloqueada.

| # | Cena | Escopo em 1 linha | Status |
|---|------|-------------------|--------|
| 01 | `probe_import` | Ken renderizado de dados convertidos, pose-por-pose em tela estática — prova tileset/paleta/metasprite | documentado |
| 02 | `ken_vs_dummy` | Ken (1P humano) vs dummy: andar, agachar, pular, soco, chute, guard, dano, hitstop — prova FSM interpretador + hitboxes | documentado |
| 03 | `golden_slice` | 2 lutadores por dados (Ken + 2º do acervo, escolha na S6), rounds melhor-de-3, timer, HUD em tiles, 1 especial cada (QCF+B1) — prova do contrato | documentado |

**Prova do contrato (gate automatizado, não narrativa):** trocar o `.def` do
2º lutador no build muda personagem, paleta, frame data e especial sem editar
nenhum `.c` do núcleo.

## Pipeline verificável (E do MD → S do SMS)

| Etapa | Entrega | Critério de aceite |
|---|---|---|
| S0 | baseline + cópia doada MD registrada com SHA | inventário do que veio do forge MD |
| S1 | inventory do acervo (somente leitura) | zips lidos sem erro, determinístico, `--self-check` ok |
| S2 | parsers+IR na cópia; `ken_masters_adv` parseia inteiro; **gate de input do emulador ativo** | testes de contrato com fixtures sintéticos |
| S3 | analysis SMS: Ken medido contra VDP/RAM/VRAM/metasprite/PSG | relatório com contagem por classe; `unsupported` é número, não silêncio |
| S4 | converters+generators: Ken → tileset/metasprites/paletas/tabelas/SFX | `audit_validate_resources`, `audit_sprite_line_sim`, `audit_provenance`, `audit_luma_floor` |
| S5 | runtime: cena 02 (Ken vs dummy) ROM no emulador | boot determinístico, input provado, evidência selada ao SHA da ROM |
| S6 | cena 03 golden slice + prova do contrato | worst-frame medido dentro do orçamento, fps 50–60, claims reconciliados |

## Orçamento e restrições de hardware (medir, não supor)

- **Sprite**: `SMS_addMetaSprite` (SMSlib.h:215) com `SPRITEMODE_TALL`
  (SMSlib.h:57); teto 8/scanline e 64/SAT é bloqueador no `analysis`. A arte
  MUGEN (Ken ~centenas de px por pose) será a primeira vítima real da medição;
  `approximate` (recorte/compactação) só com relatório de deformação.
- **Paleta**: 2 subpaletas × 15 cores úteis + índice 0 transparente;
  quantização 6-bit offline com piso de contraste medido.
- **ROM**: iniciar 32 KB; banking Sega mapper (padrão MSSF2T spec-banking:
  dados em `BANK1+`, `SMS_mapROMBank` só no VBlank) declarado no TDD desde o
  início, não descoberto tarde.
- **RAM 8 KB**: pools estáticos nomeados no TDD (sprite table, estado de luta,
  input buffer, stack). Zero malloc, zero float.
- **Áudio**: `.snd` MUGEN → PSG (SFX via PSGlib, canal conforme manifesto);
  WAV em runtime NÃO existe; 1 stream de música no MVP.
- **Worst-frame**: orçamento de VBlank medido com `measure_worst_frame.py` na
  cena 03 antes de qualquer claim. (Lição aberta do MSSF2T: lá derramou; aqui o
  número é contrato desde o design.)

## Fora de escopo (explícito)

- Screenpacks/lifebars/portraits/intros do MUGEN como sistema de arquivos.
- VM de CNS em runtime (caminho recusado formalmente em 2026-09-25).
- Mega Drive: o alvo é SMS; o forge MD é referência de técnica apenas.
- Team mode, multi-stage, roster além dos 2 do golden slice, select screen,
  continue/credit, SRAM, FM/YM2413, 6 botões, throws, dizzy, Super Combos.
- IA avançada (dummy/espelho bastam no MVP).
- Trilha completa; mais de um palco.
- Licença: arte real convertida nunca entra no Git nem em release — fica em
  `out/local_study/` (gitignored); fixtures de teste sintéticos são os únicos
  dados MUGEN-like no repo.
- Números de Mega Drive afirmados como lei do SMS (gate `audit_hardware_constants`).

## Benchmarks (régua, não fonte)

- `tools/mugen2sgdk_forge` (Mega Drive): arquitetura inventory→IR→converters→
  generators e política de fidelidade/licença. Técnica doada, código cópiada
  com SHA, nada compilado aqui.
- MSSF2T (este workspace): FSM de luta em SMS, contrato de escala 32×64 /
  SPRITEMODE_TALL, banking, pipeline de evidência — e suas dívidas abertas
  (worst-frame derramado, eixo input reprovado com WIP) que este projeto
  ataca cedo por decisão de design, não por acidente.
- HAMOOPIG/SSF2T arcade: frame data, leitura de silhueta, densidade — só como
  régua de qualidade.

## Política de licença e proveniência

- `Base de Estudo/` é somente leitura; nenhum zip original entra no Git.
- Derivados de Ken/2º piloto vivem em `out/local_study/` (gitignored) até
  confirmação humana de redistribuição; `license_status` máximo: `candidate`.
- Cada ativo derivado tem entrada em `doc/asset_provenance_manifest.json` com
  `source_kind` e SHA da fonte MUGEN — proveniência declarada ou não entra.

## Teto de claims aprovado

`protótipo jogável de engine de luta MUGEN→SMS dirigida por dados` — com época
visual no máximo `technical_candidate` até o gate de evidência da S6. Acima
disso só com evidência selada. **Nunca** "MUGEN no Master System" como claim
de paridade; `ready_for_aaa` = false.
