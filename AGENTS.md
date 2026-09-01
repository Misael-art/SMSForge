# AGENTS.md — SMSForge

> **Ponto de entrada obrigatório para qualquer agente de IA neste workspace.**
> Diga `[Contexto SMS Carregado]` antes de propor qualquer ação.

---

## REGRA FINAL DE FERRO

**"Se não foi visto rodando no emulador, não existe."**
Intenção não é validação. ROM de Master System rodando a 60fps (NTSC) / 50fps (PAL) constantes, sim.

---

## O QUE É ESTE WORKSPACE

Fábrica metodológica de jogos para **Sega Master System** (e família SG-1000/Game Gear por extensão declarada), portada da filosofia do MegaDrive_DEV (SGDKForge). Dois objetivos:

1. Produzir ROMs reais usando **SDCC + devkitSMS (SMSlib/PSGlib)**, validadas em emulador;
2. Impedir que um agente trate "narrativa bonita" como evidência.

Não é um jogo: é a infraestrutura que produz jogos.

---

## FRAMEWORK CANÔNICO DE AGENTES

O framework `.agent` vive centralizado em `tools/sms_wrapper/.agent/`.
Cada projeto recebe materialização local via bootstrap (`tools/sms_wrapper/new_project.sh`).

```
tools/sms_wrapper/.agent/
  ARCHITECTURE.md          ← leia para entender o framework
  rules/SMS_GLOBAL.md      ← lei canônica sempre ativa
  skills/                  ← conhecimento por domínio
  workflows/               ← runbooks operacionais
  pipelines/               ← pipelines machine-readable
```

**Política de sobrescrita: `.agent` local existente não é sobrescrita.**

---

## MENU DE SESSÃO / MODOS DE OPERAÇÃO

Quando o usuário pedir `menu`, `modo`, `iniciar`, `abrir sessão` ou quando a intenção inicial estiver ambígua:

```
[CRIAR NOVO PROJETO DE JOGO DE MASTER SYSTEM] -> create_new_project
[ANALISAR PROJETO EXISTENTE]                  -> analyze_existing_project
[TREINAR AGENTE]                              -> train_agent
[LABORATÓRIO]                                 -> laboratory
[CURADORIA]                                   -> curation
```

Cada modo tem runbook executável em `tools/sms_wrapper/.agent/workflows/`:

| Modo | Workflow | Onde vive |
|------|----------|-----------|
| `create_new_project` | `new-project.md` | `SMS_projects/<slug>/` |
| `analyze_existing_project` | `analyze-existing-project.md` | projeto existente (não altera) |
| `train_agent` | `train-agent.md` | `SMS_projects/_treino/` |
| `laboratory` | `laboratory-mode.md` | `SMS_projects/_laboratorio/` |
| `curation` | `curation-mode.md` | `tools/sms_wrapper/` ou `doc/` |

Regras:
- pedido direto e claro não deve ser atrasado pelo menu;
- troca de modo exige consentimento humano;
- treino vive em `SMS_projects/_treino/`; laboratório em `SMS_projects/_laboratorio/`;
- curadoria só altera `tools/sms_wrapper/` ou `doc/` com aprovação humana explícita + testes + memória atualizada;
- estado de sessão nunca substitui memory bank, GDD, TDD, manifests ou evidência de emulador.

---

## HIERARQUIA DE VERDADE

| # | Fonte | Autoridade |
|---|-------|------------|
| 1 | `doc/10-memory-bank.md` do projeto | Estado operacional real |
| 2 | `doc/11-gdd.md` | Design e escopo ("se não está no GDD, não entra") |
| 3 | `doc/13-spec-cenas.md` | Budget real por cena |
| 4 | `doc/00-diretrizes-agente.md` | Regras de processo |
| 5 | `.mddev/project.json` | Manifesto estrutural |
| 6 | `doc/12-roteiro.md` | Roteiro e diálogos |
| 7 | `doc/15-tdd.md` | Arquitetura técnica |
| 8 | Headers devkitSMS `sdk/devkitSMS/SMSlib/SMSlib.h` e `PSGlib/PSGlib.h` | API definitiva |
| 9 | `sdk/README.md` | Procedimento de toolchain |
| 10 | Suposição / memória | Última prioridade — nunca especular |

---

## RESTRIÇÕES NÃO NEGOCIÁVEIS

```
❌ float/double em runtime quente   — SDCC Z80 faz float em software; use uint8/int16/Q8.8
❌ malloc / free                    — buffers estáticos; RAM = 8KB
❌ Inventar API SMSlib/PSGlib       — header é autoridade #8; verificar antes de usar
❌ >8 sprites numa scanline         — só depois do simulador aprovar
❌ >64 sprites na SAT               — limite físico do VDP
❌ Cor fora dos códigos 6-bit       — paleta mestra fixa; sem "gradiente suave"
❌ >15 cores úteis por subpaleta    — índice 0 é transparente nas duas
❌ VRAM em massa fora do VBlank     — sem DMA: orçamento worst-frame medido é contrato
❌ Lógica de build no projeto       — apenas em tools/sms_wrapper/
❌ Declarar "pronto" sem ROM rodando no emulador
❌ Pixel nascido de código como personagem, inimigo, boss ou cenário final
❌ Símbolo visual em res/ sem proveniência declarada
❌ Fechar orçamento sem medir o degrau seguinte — folga não medida é timidez
❌ Usar leitura de ferramenta de medição cujo --self-check não passa
```

---

## ORDEM DE TRABALHO DE CENA

Decisão barata antes de arte cara. Cada transição tem gate executável:

```
roteiro → storyboard (planta baixa em pixel) → coreografia → MEDIÇÃO → orçamento
→ contrato de asset → model sheet → assets → runtime → EVIDÊNCIA
```

| Gate | Ferramenta | O que reprova |
|------|-----------|---------------|
| Build | `sms_wrapper/build_inner.py` via SDCC + devkitSMS | erro de compilação/link |
| Recursos | `audit_validate_resources.py` | PNG fora do grid 8×8, cor fora do contrato, >15 úteis |
| Sprites/scanline | `audit_sprite_line_sim.py` | >8 sprites/linha, >64 na SAT, colisão com 0xD0 |
| Geometria de sprite | `audit_sprite_mode.py` | arte mais larga que o modo sem metasprite (L006, §25) |
| Contraste | `audit_luma_floor.py` | contraste < 1 degrau efetivo da paleta mestra |
| Procedência | `audit_provenance.py` | pixel nascido de código como personagem/cenário |
| Evidência | `capture_evidence.py` | captura branca/sem informação, emulador ausente |
| Semântica da captura | `screenshot_semantic_gate.py` | cor fora da paleta mestra (mockup/render), desktop não recortado, reuso da mesma imagem em dois claims, claim que screenshot não prova |
| Frescor da evidência | `seal_fresh_evidence_bundle.py` | artefato **anterior** à ROM (mostra outro binário) ou de outra sessão |
| Conciliação de claims | `reconcile_claims.py` | eixo declarado `true` sem lastro no artefato de evidência |
| Claims | `audit_claims.py` | claim acima do teto aprovado |
| Mudança significativa | `audit_meaningful_change.py` | mudança que não ataca o blocker dominante |
| Boot determinístico | `audit_deterministic_boot.py` | ROM animada sem estado inicial estável |
| Quarentena de placeholder | `audit_placeholder_quarantine.py` | placeholder promovido sem aprovação |
| Fixture canônica | `canonical_fixture_gate.py` | fixture sem escopo ou com claim amplo |
| Áudio (captura) | `capture_audio.py` | grava o áudio **isolado** do emulador (sink dedicado); repete se vier silêncio adiantado |
| Áudio (mix) | `audit_audio.py` | captura de áudio silenciosa/sem sinal |
| FPS | `measure_fps.py` | <5 amostras ou fps fora de 50–60 |
| Matriz de maestria | `audit_mastery_registry.py` | técnica acima de `mapped` sem evidência |
| Especialização | `audit_specialization.py` | gênero declarado sem lastro no GDD |
| **Ferramentas de medição** | `validate_measurement_tools.py` | ferramenta de medição sem `--self-check` passando (§19) |
| **Sincronia doc↔repo** | `audit_doc_sync.py` | doc citando gate inexistente, gate invisível na doutrina, hierarquia de verdade incompleta |

## VOCABULÁRIO DE STATUS

```
documentado ≠ implementado ≠ buildado ≠ testado_em_emulador ≠ validado_budget
```

Gate final de entrega exige os 7 eixos simultâneos: build, validation_report,
boot no emulador, gameplay, 60/50 fps, áudio, memory bank atualizado.

---

## APRENDIZADO INSTITUCIONAL

Quando algo dá errado: lição vira JSON canônico em `doc/curation/` +
seção numerada em `.agent/rules/SMS_GLOBAL.md` + ferramenta que mede.
**Regra vira medição, nunca só prosa.** Ver workflow `curation-learning.md`.
