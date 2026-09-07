# Trilhas-alvo — port SSF2T SMS (`audio/music/`)

> Sem binários neste diretório por decisão: ROM de Master System toca
> **PSG (SN76489 via PSGlib)**, não MP3. As composições são trabalho futuro
> com `tools/sms_wrapper/make_psg_assets.py` + skills `sms-psg-audio.md` /
> `sms-psg-composition.md`. Arbitragem música×SFX vai no TDD do projeto.

## Temas necessários (ordem de prioridade do teste)

1. **Guile Stage** — tema do cenário pedido (prioridade máxima: é o palco do teste).
2. **Ken Stage** — tema do segundo cenário.
3. **Character Select** — tela de seleção.
4. **Versus / VS screen jingle** — antes da luta.
5. **Title / attract** — abertura (quando a lacuna de arte da title fechar).
6. **Continue / Game Over / Ranking** — fluxo de telas.
7. **Ending (Ken, Guile)** — cenas de final.
8. **SFX**: hit, block, KO, Hadouken, Sonic Boom, Flash Kick, Shoryuken,
   select cursor, round call ("ROUND 1 / FIGHT!" via texto + jingle).

## Restrições SMS a respeitar na composição

- 3 canais tone + 1 noise; música precisa funcionar sem YM2413 (FM opcional).
- Sem `float`; tabelas de nota em ROM, pools estáticos (RAM 8KB).
- Referência de escuta: gravações do arcade servem de guia auditivo
  (fora do repo); a partitura PSG é autoral.
