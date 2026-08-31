<div align="center">

# 🕹️ SMSForge

### Fábrica metodológica de jogos para **Sega Master System**

*Transformamos as restrições físicas de 1985 em gates medidos — e os erros de modelos anteriores em ferramentas que reprovam.*

> **"Se não foi visto rodando no emulador, não existe."**
> Intenção não é validação. ROM a 60/50 fps no emulador, sim.

[![SDK](https://img.shields.io/badge/toolchain-SDCC_%2B_devkitSMS-blue?style=flat-square)](https://github.com/sverx/devkitSMS)
[![Target](https://img.shields.io/badge/hardware-Sega_Master_System-red?style=flat-square)](#)
[![Gates](https://img.shields.io/badge/gates-14%20execut%C3%A1veis-brightgreen?style=flat-square)](#)
[![Selftest](https://img.shields.io/badge/selftest-25%2F25-green?style=flat-square)](#)
[![Eixos](https://img.shields.io/badge/entrega-7%2F7%20TRUE-blueviolet?style=flat-square)](#)
[![License](https://img.shields.io/badge/licen%C3%A7a-MIT-red?style=flat-square)](#)

</div>

---

## 🎮 Propósito

O SMSForge é um **compilador de disciplina**. Ele pega os limites irredutíveis do
Master System — Z80 a 3.58MHz, VDP **sem DMA**, paleta mestra de 64 códigos,
**8 sprites por scanline**, 8KB de RAM — e os transforma em **gates executáveis**
que um agente de IA (ou humano) precisa passar antes de declarar qualquer coisa.

O elo fraco nunca foi o hardware. Era o **agente prometendo o que não tinha provado.**

> Não é um jogo. É a **infraestrutura que produz jogos** — com 7 eixos de entrega
> verificados, 14 gates anti-autoengano, um framework de agentes e uma engine
> reutilizável já rodando a 60fps.

---

## 🚀 Capacidades

### 14 Gates Executáveis (cada um com `--self-check`)

| Categoria | Gate | Reprova |
|-----------|------|---------|
| 🧱 Build | `build_inner.py` | erro de compilação/link |
| 🎨 Recursos | `audit_validate_resources.py` | PNG fora do grid 8×8, cor fora do contrato, >15 úteis |
| 👾 Sprites/scanline | `audit_sprite_line_sim.py` | >8 sprites/linha, >64 na SAT, colisão com 0xD0 |
| 🌗 Contraste | `audit_luma_floor.py` | contraste < 1 degrau efetivo da paleta |
| 🔍 Procedência | `audit_provenance.py` | pixel nascido de código como personagem |
| 📸 Evidência | `capture_evidence.py` | captura branca/vazia, emulador ausente |
| 🗣️ Claims | `audit_claims.py` | claim acima do teto aprovado |
| 🎯 Mudança real | `audit_meaningful_change.py` | mudança que não ataca o blocker |
| ⏱️ Boot determinístico | `audit_deterministic_boot.py` | ROM sem estado inicial estável |
| 📦 Placeholder | `audit_placeholder_quarantine.py` | placeholder promovido sem aprovação |
| 🧩 Fixture canônica | `canonical_fixture_gate.py` | fixture sem escopo ou claim amplo |
| 📊 Maestria | `audit_mastery_registry.py` | técnica "provada" sem evidência (overclaim) |
| 🎭 Gênero | `audit_specialization.py` | eixos congelados do gênero ausentes |
| 🎵 Áudio | `audit_audio.py` | mix fraco / ownership de canal ausente |

### Framework de Agentes (`.agent/`)
- **Lei canônica** `rules/SMS_GLOBAL.md` (hierarquia de verdade, vocabulário de status)
- **5 personas**: `sms-pixel-engineer`, `sms-hardware-budget-guardian`, `sms-game-director`, `sms-qa-emulator-tester`, `sms-audio-engineer`
- **17 skills** por domínio · **3 pipelines** machine-readable · **13 schemas** JSON
- **7 eixos de entrega**: build, validation, boot, gameplay, fps, áudio, memory bank

### Engine Reutilizável (`SMS_Engines/corridor_engine/`)
Shoot-em-up base: sprites 8×8 (L006), música PSG (PSGlib), scroll, jogador com
tiro/invuln/flash, inimigos com dificuldade progressiva, HUD, game over.

---

## 🖥️ Especificações do Master System (as "regras do jogo")

| Eixo | Limite físico | Como o SMSForge lida |
|------|---------------|----------------------|
| CPU | Z80 @3.58MHz, int 16-bit, sem mul/div | SDCC; Q8.8; proibido float em runtime |
| RAM | **8KB** | buffers estáticos, pools; sem malloc |
| VRAM | 16KB, **sem DMA** | transferências SÓ no VBlank, orçamento medido |
| Sprites | **8/scanline**, 64 na SAT | simulador por scanline |
| Paleta | 64 códigos fixos (6-bit) | contrato de cor, sem "gradiente" |
| Tiles BG | name table de **1 byte/tile** | sem flip/paleta por tile |
| ROM | 48KB linear; mapper 16KB | header SEGA + makesms |
| Áudio | PSG SN76489 (4 canais); YM2413 opcional | PSGlib; jogo roda sem FM |

---

## 📂 Estrutura

```
SMSForge/
├── AGENTS.md              ← contrato de entrada para qualquer IA
├── doc/
│   ├── 05_technical/      ← matriz de maestria, arquitetura de áudio
│   ├── 06_AI_MEMORY_BANK.md
│   ├── curation/          ← lições canônicas (vira medição)
│   └── game-design/       ← matriz de gênero
├── sdk/                   ← toolchain (headers = autoridade de API)
├── tools/
│   ├── sms_wrapper/       ← FONTE ÚNICA de build + gates + .agent
│   └── emuladores/        ← Emulicious (gate), MEKA, openMSX
├── SMS_Engines/           ← engines reutilizáveis
│   └── corridor_engine/
└── SMS_projects/          ← os jogos (cada um autocontido)
    └── laboratorio_01/    ← cena04 "corredor estelar" (60fps)
```

---

## ⚙️ Como usar

### 1. Instalar a toolchain (rootless, ~2 min)

```sh
tools/sms_wrapper/ensure_toolchain.sh
# instala SDCC portátil + devkitSMS + makesms e PROVA com smoke-test
```

### 2. Verificar que os gates estão sãos

```sh
python3 tools/sms_wrapper/selftest.py
# → SELFTEST: 25/25 verdes
```

### 3. Criar um novo projeto

```sh
tools/sms_wrapper/new_project.sh meu_jogo
cd SMS_projects/meu_jogo
./build.sh          # delega ao wrapper; nunca lógica local
```

### 4. Rodar no emulador

```sh
java -jar tools/emuladores/emulicious/Emulicious.jar \
     SMS_projects/meu_jogo/out/rom/meu_jogo.sms
```

### 5. Fechar uma cena (ciclo oficial)

```
roteiro → storyboard (pixel) → coreografia → MEDIÇÃO → orçamento
→ contrato de asset → model sheet → assets → runtime → EVIDÊNCIA
```

Cada transição passa por um **gate executável** — nunca por confiança verbal.

---

## 🏗️ Estado honesto

O workspace está **operacional e verificado**:
- ✅ Selftest **25/25** (gates provam o válido e reprovam o inválido)
- ✅ Cena04 **"corredor estelar"** rodando a **60fps** (sprites + música PSG + scroll + game feel)
- ✅ **7 eixos de entrega TRUE** com evidência de emulador
- ✅ Engine reutilizável + framework de agentes prontos
- ✅ Reproduzível: clone → `ensure_toolchain.sh` → `build.sh`

---

## 🔬 Filosofia

Decisão barata antes de arte cara. Medição entre elas. Gate executável em toda
transição. **Regra vira medição, nunca só prosa** — quando algo dá errado, a lição
vira um JSON canônico, uma seção numerada na lei e uma ferramenta que mede.

A espinha metodológica (hierarquia de verdade, vocabulário de status, learning loop)
é a mesma do workspace-mãe **MegaDrive_DEV (SGDK Forge)** — porque ela é geral de
engenharia, não de console. O que foi **re-derivado** aqui é todo o lado hardware
(Z80/VDP/PSG), porque Master System ≠ Mega Drive.

---

<div align="center">

**Feito com ❤️ e um Z80 saudável** — *prove, não prometa.* 🕹️

</div>
