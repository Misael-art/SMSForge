# skill: sms-asset-pipeline

## Fluxo canônico
```
rascunho/<original> (com sha256 registrado)
  → contrato de asset (asset_contract_v1)
  → model sheet (personagem/inimigo/cenário)
  → res/*.png indexado 8-bit, grid 8×8, índice 0 transparente, ≤15 úteis
  → gates: validate_resources + luma_floor + provenance
  → conversão a dados C/assets2banks (quando o primeiro asset real chegar)
```

## Proveniência (gate audit_provenance.py)
- Todo PNG de res/ tem entrada em `doc/asset_provenance_manifest.json`.
- origin aponta arquivo real em rascunho/; sha256 bate.
- `tool:"code"` é proibido para personagem/inimigo/boss/cenário_final.

## Conversão
Foto/truecolor → `prepare_sms_pixel_art.py` (paleta mestra SMS, grid 8×8)
antes de `res/`. Skill: `sms-pixel-translate.md`. Não use preset NES/SNES.
PNG indexado no contrato → `png_to_sms_tiles.py` (4bpp / 32 B por tile).

## Uma fonte para o tamanho
`#define FOO_SIZE` e `foo[N]` (e o mesmo define em dois headers) coincidem.
Header-índice escrito à mão diverge da folha e o streamer lê além do array
(L052). Gere o header; rode `--check`. Gate: `audit_symbol_size_sync.py`.
