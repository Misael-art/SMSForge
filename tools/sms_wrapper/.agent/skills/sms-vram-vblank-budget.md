# skill: sms-vram-vblank-budget

## Não existe DMA
Toda transferência em massa passa pela CPU dentro do VBlank (~4.5ms NTSC).

## Orçamento = contrato
1. Listar transferências por frame (tiles, name table, SAT, paleta).
2. Medir worst-frame real (contador de ciclos/instrução + evidência de emulador).
3. Registrar em `13-spec-cenas.md` com campo `method` ≠ "estimado".
4. Fechar orçamento SEM medir o degrau seguinte é proibido (§18).

## Técnicas
- Streaming de tiles entre frames com cota fixa.
- Compressão ZX7/aPLib: descompressão custa CPU do frame — medir junto.
- `SMS_VRAMmemcpy*` / `SMS_loadTileMapAreaatAddr` — assinaturas SEMPRE no header.
- Transição de tela: **display off**, reescrever o mapa inteiro, display on.
  Escritas fora do VBlank deixam resto na tela; limpar linha a linha não
  fecha a classe (L047).
