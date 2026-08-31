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
Ferramenta de preparo PNG→dados é ROADMAP (matriz Q0x); até lá, assets entram
via assets2banks manual documentado no memory bank do projeto.
