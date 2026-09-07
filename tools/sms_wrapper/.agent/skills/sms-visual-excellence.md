# skill: sms-visual-excellence

Use quando a tarefa pedir julgamento estético, época visual, escala, palco,
HUD ou promoção para `res/` / ROM. Complementa `sms-pixel-strict-rules`
(sintaxe) — esta skill trata **semântica**. PNG 4bpp válido não é qualidade.

Canvas: **256×192** (224 só com `VDPFEATURE_224LINES` medido). Não copie
320×224, 4 subpaletas, DMA ou Shadow/Highlight do Mega Drive.

## Teto honesto

```
runtime_probe_passed ≠ visual_epoch_passed ≠ ready_for_aaa
```

Captura que prova boot/rota Linux classifica no máximo
`runtime_probe_passed_visual_epoch_failed` até `audit_visual_delivery.py`
passar em modo `--delivery`.

## Época visual

Somente `visual_epoch=delivery` promove personagem, inimigo, boss, palco ou HUD.
Reprovar promoção de: `probe`, `technical_d1`, `technical_candidate`,
`visual_lab_control`, `reference_only`, `negative_case_evidence`, `placeholder`.

Benchmark (engine de referência, outro console, outro jogo) é **régua**:
escala, densidade, timing, silhueta, ocupação de tela. Pixels só reentram
com licença/proveniência explícita.

## Personagem

1. Model sheet limpo: sem sombra no chão, poeira, glow, FX ou checkerboard assado.
2. Must-preserve: rosto, cabelo, traje, proporção, mãos/pés, arma, identidade.
3. Até três rotas de tradução; nenhuma rota mecânica vira final sozinha.
4. Triagem em 1×, 2×/3×, NEAREST 8×, silhueta, fundos claro/escuro, composição 256×192.
5. Limpeza nativa: olhar legível, contorno consistente, ≤15 úteis + idx0,
   RGB no grid 6-bit, sem halo.
6. Escala vem do GDD. Reduzir personagem para economizar tiles é proibido.
   `scale_density_mismatch` com escala `locked` → reautor no grid, não probe maior.

## Palco e HUD

- BG_A/B coerentes; sem splash de engine, logo de toolkit ou tela de referência.
- Lutador/jogador é o pico de leitura; BG_B respira; BG_A estrutura.
  BG/HUD não podem ser o objeto mais saturado com forma de sprite —
  sequestram o detector de gameplay (L042).
- HUD autoral sem overlap/clipping; nomes, barras, timer quando o GDD pedir.
- ROM cheia: composição (paleta, pose, fonte já carregada) **antes** de
  gerar asset novo (L049).
- Contraste medido (`audit_luma_floor.py`); CRT-aware: se só funciona ampliado, não existe.

## Gates

- `audit_visual_delivery.py --delivery`
- `audit_rom_asset_binding.py --require`
- `audit_placeholder_quarantine.py --check-release`
- `audit_render_fidelity.py` + `screenshot_semantic_gate.py`

## Nunca faça

- Confundir conformidade P/4bpp com qualidade artística.
- Reusar o mesmo PNG para dois personagens.
- Promover probe 8×8/16×16/32×40 como lutador final.
- Usar tela de branding como stage.
- Declarar `ready_for_aaa` com epoch ≠ delivery.
