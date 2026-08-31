# skill: sms-banking-header

## Regras
- ≤48KB linear sem mapper (primeiro alvo de todo projeto).
- Mapper Sega: páginas de 16KB; slot 0x4000 via 0xFFFE, slot 0x8000 via 0xFFFF;
  slot 0x0000 fixo na página 0. Troca: macro `SMS_mapROMBank(n)` (header).
- Código não-bancado ≤32KB. Dados bancados: `--constseg BANKn` +
  `-Wl-b_BANKn=0x{n}4000`; assets2banks gera os fontes.
- Header SEGA @0x7FF0 ("TMR SEGA" + checksum + região); `makesms` cuida do checksum.

## Gate mental
Antes de adicionar mapper: o orçamento atual foi MEDIDO ou é chute? Mapper sem
medição é feature creep técnico.
