# Roadmap de maestria — Master System (waves)

Eleva o agente de "mapped" (só documentado) até `default_senior` (procedimento
base seguro) por trilha. Cada wave fecha com evidência de emulador.

Escada de proficiência:
`mapped → incorporada → reproduzível → emulador_provado → default_senior`

## Wave 0 — Fundação (já conquistada)
Trilhas: VDP tiles, sprites 8×8, paleta, vblank, z80/sdcc, banking header,
audio psg, input/timing.
- Status: `emulador_provado`/`default_senior` (ver registry JSON).

## Wave 1 — Física e tempo (próxima)
- `V04` line interrupt → split de scroll estável (medir jitter no emulador).
- `I03` normalização NTSC/PAL → movimento com frame-counter escalado.
- `M04` streaming de tiles com cota fixa → rodar no worst-frame.

## Wave 2 — Profundidade visual
- `P04` half-brightness / color add-sub → fade estético sem alpha.
- `S05` x-offset 32 (provar posicionamento real de sprite no VDP).
- `M03` layout VRAM declarado por cena no TDD (impor).

## Wave 3 — Áudio avançado
- `A03` samples PSG (mini-samples com custo de ROM medido).
- `A04` YM2413 (FM opcional) — só se o projeto pedir; nunca obrigatório.
- `A05` áudio com budget próprio (medido junto do VRAM).

## Wave 4 — Banco e escala
- `B02` mapper Sega (páginas 16KB) → cena > 48KB.
- `B04` código restrito a 32KB + dados bancados.
- `Z06` banked code (`__banked`) → código > 32KB.

## Wave 5 — Raster / efeitos
- `R01` split de scroll por line interrupt (rasterbar).
- `R02` palette cycling por linha (com varredura vblank).
- `R03` scroll-y por coluna (efeito de parallax vertical).

## Wave 6 — Sênior absoluto
- Todas as trilhas em `default_senior` com evidência de emulador por técnica.
- Habilidade de prototipar qualquer gênero usando as técnicas da matriz.

## Nota
Nenhuma técnica sobe de nível em `mapped` sem build + evidência de emulador
(regra SMS_GLOBAL §23 — fato pago). Report falsos = overclaim.
