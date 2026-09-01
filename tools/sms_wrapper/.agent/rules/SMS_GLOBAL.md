# SMS_GLOBAL — Lei canônica do SMSForge (sempre ativa)

> Porte da SGDK_GLOBAL (MegaDrive_DEV) para Master System. Seções numeradas;
> lições novas APENDAM seção; regra vira medição, nunca só prosa.

## 1. Fonte de verdade
Hierarquia em `AGENTS.md` da raiz. Estado operacional (`10-memory-bank.md`) >
design (GDD) > processo > headers devkitSMS (API definitiva) > suposição.
Suposição nunca vira resposta; vira pergunta.

## 2. Restrições não negociáveis
Lista ❌ completa vive no AGENTS.md e é espelho desta seção. Violar qualquer
item invalida a entrega inteira — não "com exceção".

## 3. Governança e vocabulário de status
```
documentado ≠ implementado ≠ buildado ≠ testado_em_emulador ≠ validado_budget
```
Um agente que diz "pronto" sem ROM rodando no emulador comete autoengano —
o crime fundador deste workspace. Claims têm teto aprovado (§17).

## 4. Operação do wrapper
Toda lógica de build/validação vive em `tools/sms_wrapper/`. Projetos têm shims
que delegam. Duplicar lógica = regressão estrutural.

## 5. Handoff
Fim de sessão: memory bank atualizado + handoff curto (o que mudou, próximo passo,
bloqueios). Handoff nunca substitui memory bank nem evidência.

## 6. Lei do VDP (tiles BG)
- Grid 8×8; pattern table 32 bytes/tile; **máx 256 tiles BG**.
- Name table = **1 byte por tile** (índice 0–255). Não existe flip nem paleta
  por tile no BG — variação vem de tiles distintos ou metatiles.
- Scroll global X/Y + trava opcional da 1ª coluna. Split de scroll exige
  line interrupt e é técnica medida, não gratuita.

## 7. Lei de sprites
- SAT: máx **64 sprites**; terminador Y=0xD0 corta o processamento.
- Máx **8 sprites por scanline**. Excesso é descartado; no VDP SMS1 corrompe a
  linha. O simulador (`audit_sprite_line_sim.py`) aprova antes do runtime.
- Tamanho global 8×8 OU 16×16 (+ zoom ×2 global). Metasprites compõem entidades.
- X físico armazenado = X+32; X<32 esconde à esquerda.
- Comportamento dependente de revisão (early clock, flips) não vira lei sem
  evidência de emulador/console (§23).

## 8. Lei de paleta
- CRAM 2 subpaletas ×16; índice 0 transparente nas duas → máx 30 úteis simultâneas.
- Cor = código 6-bit. Contrato de assets: canal×85. Sem gradiente suave;
  fade = recarga de paleta sincronizada ao VBlank.
- Contraste medido em degraus de luma derivada (`audit_luma_floor.py`).
  Adjetivo visual sem piso numérico não entra em spec.

## 9. Orçamento VRAM/VBlank (não existe DMA)
- Transferência em massa SÓ dentro do VBlank (janela ≈4.5ms NTSC).
- Orçamento worst-frame POR CENA é contrato em `13-spec-cenas.md`, medido
  ("estimado" é proibido no schema). Folga não medida é timidez (§18).

## 10. Armadilhas Z80/SDCC (assumir como suspeita até provado)
- `int` = 16-bit signed; multiplicação/divisão caras; float proibido em runtime quente.
- RAM 8KB total (`--data-loc 0xC000`): sem malloc, pools estáticos.
- ISR/NMI curtos; pause = NMI.

## 11. Banking e header
- ≤48KB linear sem mapper. Mapper Sega: páginas 16KB nos slots 0x4000/0x8000;
  código não-bancado restrito aos primeiros 32KB.
- Header SEGA em 0x7FF0 exigido pela BIOS regional; `makesms` gera/checksum.

## 12. Áudio
- PSG SN76489: 3 tone + noise. PSGlib é o driver padrão. Arbitração música×SFX
  declarada no TDD. YM2413 é opcional — o jogo precisa funcionar sem FM.

## 13. Timing NTSC/PAL
60 vs 50 Hz: velocidade normalizada via frame counter. Nada de delay loops.
Claim de fps constante exige medição (§17).

## 14. Anti-alucinação devkitSMS
Headers = autoridade #8. Antes de usar API: abrir `SMSlib.h`/`PSGlib.h`.
Mapa conceitual SGDK→SMSlib (NÃO é 1:1):
| Conceito MD | Equivalente SMS |
|---|---|
| DMA queue | transferências manuais dentro do VBlank |
| PAL_setPalette | SMS_loadBGPalette / SMS_loadSpritePalette |
| VDP_setTileMapXY | SMS_setTileatXY (name table 1 byte) |
| sprite flip por atributo | NÃO EXISTE no BG; sprites: revisão-dependente (§7) |
| XGM2 | PSGlib (+ PSG samples) |
Função que não estiver no header não existe.

## 15. Estética doutrinária
Dark Deco adaptado: contraste alto, luz escassa, silhueta legível a 256×192.
Pixel art autoral obrigatória. Proveniência por asset (`audit_provenance.py`);
pixel nascido de código como personagem/inimigo/boss/cenário final é bloqueado.

## 16. Ciclo de produção de cena
roteiro → storyboard (planta baixa em pixel) → coreografia → MEDIÇÃO → orçamento
→ contrato de asset → model sheet → assets → runtime → EVIDÊNCIA.
Medir depois de arte cara foi a lição mais cara da história da metodologia-mãe
(curadoria 2026-08-17): aqui isso é gate, não conselho.

## 17. Claim ceiling executável
Tokens AAA / 60fps / 50fps / pixel-perfect / release só existem com teto aprovado
(`doc/promotion_claims/<token>.json`). `audit_claims.py` reprova o resto.

## 18. Doutrina de audácia
Fechar orçamento sem medir o degrau seguinte é timidity disfarçada de prudência.
Sempre medir o próximo degrau antes de declarar folga.

## 19. Self-check obrigatório
Ferramenta de medição cujo `--self-check` falha não é fonte. Ler saída de
ferramenta sem self-check verde é violação.

## 20. Gate calibrado contra falso positivo
Todo gate precisa reprovar um caso inválido conhecido E aprovar um válido
(`selftest.py`). Gate que nunca reprovou não está calibrado.

## 21. Learning capture obrigatório
Erro → JSON canônico em `doc/curation/` + seção numerada AQUI + ferramenta que mede.
Dedup por chave canônica no ledger.

## 22. Capacidade declarada com prova antes de promessa
Só declare capacidade que já pagou com build/evidência. "Devo conseguir" não
entra em doc de projeto; entra como risco.

## 23. Fatos pagos com evidência
Fato hardware/software só vira lei quando pago com build + emulador. Enquanto
isso: hipótese marcada, teste agendado. Ex.: comportamento early-clock entre
revisões de VDP — pendente de primeira evidência real.

## 24. Deterministic boot
Boot determinístico obrigatório: mesmo estado inicial toda execução; RNG semeado
por input/frame counter documentado. Evidência comparável exige boot estável.

## 25. Geometria de sprite: nenhum modo é mais largo que 8px
`SPRITEMODE_TALL` é **8×16**, não 16×16. `ZOOMED` dobra o PIXEL, não a arte.
Entidade com arte mais larga que 8px exige **metasprite**, em qualquer modo.
Lição L006 (laboratorio_01): a matriz de maestria S03 afirmava "8×8 ou 16×16" e
custou dias de sprite invisível — doutrina errada gera bug, não só confusão.
Corolário: fato de hardware citado na matriz é lei operante; errá-lo é defeito
de gate, não detalhe de redação.
Gate: `audit_sprite_mode.py` (cruza modo declarado no fonte com largura do asset).

## 26. Binário novo invalida evidência velha
Relinkou a ROM? Toda prova de runtime (boot/gameplay/fps/áudio) volta a `false`
até ser recapturada contra o binário novo. `build_inner.py` rebaixa sozinho:
eixo só sobrevive se a evidência for POSTERIOR à ROM.
Corolário: `--skip-pre-gates` nunca produz `validation_report: true`.
Herança de eixo entre builds vale só para eixos de runtime; `build` e
`validation_report` descrevem a execução atual e não se herdam.
Gate: `build_inner.demote_stale_axes` + `reconcile_claims.py` como pós-gate.

## 27. Base de tiles de sprite: o VDP lê na metade que VOCÊ escolher
Sprite não lê o tile que você cita, e sim o tile que a **base do reg 6** manda.
Sem `SMS_useFirstHalfTilesforSprites(1)`, `SMS_addSprite(...,128)` lê o tile
**384** — VRAM nunca escrita = ruído colorido. BG sai limpo porque usa outra base:
**"BG certo + sprite corrompido" é assinatura deste erro.**
Corolário do L006: a causa-raiz REAL era esta, provada em emulador em 2026-08-31.
As duas leis anteriores estavam certas mas eram camadas de cima:
§25 (geometria/metasprite) e o conversor 4bpp. Três defeitos empilhados sobre o
mesmo sintoma — por isso "corrigir a causa" não resolvia.
Gate: `audit_sprite_mode.py` (sprite citando tile < 256 exige a base declarada).

## 28. Tela de emulador com informação não é tela CORRETA
Variância de luma alta e conformidade de paleta **não distinguem arte de ruído**:
lixo de VRAM usa as mesmas cores da CRAM e tem variância altíssima.
`capture_evidence.py` e `screenshot_semantic_gate.py` provam **origem e
não-vacuidade**, nunca correção. Toda captura que sustente claim visual exige
inspeção do conteúdo — humana ou por comparação com referência esperada.
Fato pago: a evidência da F6 (`cena04_sprites.png`) era uma tela de ruído
aprovada por dois gates e aceita como entrega de "7 eixos true".
