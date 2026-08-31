# workflow: new-visual-asset

1. Original entra em `rascunho/` (externo) ou é criado lá; registrar sha256.
2. Contrato `asset_contract_v1`: grid, kind, códigos de paleta.
3. Model sheet quando for personagem/inimigo/cenário final.
4. Exportar PNG indexado 8-bit p/ `res/` (índice 0 transparente, ≤15 úteis).
5. Rodar gates:
   - `audit_validate_resources.py`
   - `audit_luma_floor.py`
   - `audit_provenance.py`
6. Atualizar `doc/asset_provenance_manifest.json`.
7. Falhou? Lição → workflow curation-learning.
