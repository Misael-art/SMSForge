# skill: sms-score-banking

## Para quê
Múltiplos bancos de ROM (>48KB) no Master System via mapper Sega.

## Regras
- ≤48KB linear sem mapper (primeiro alvo). Mapper Sega: páginas de 16KB;
  slots 0x4000 (0xFFFE) e 0x8000 (0xFFFF); slot 0x0000 fixo na página 0.
- Código não-bancado restrito a 32KB (as últimas 16KB são paged-out).
- Dados: `--constseg BANKn` + `-Wl-b_BANKn=0x{n}4000`, montados via assets2banks.
- Header SEGA @0x7FF0; makesms calcula checksum.

## Decisão
Só usar mapper quando o orçamento foi medido (nunca "por precaução").
