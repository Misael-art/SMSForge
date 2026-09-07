# workflow: new-visual-asset

1. Original entra em `rascunho/` (externo) ou é criado lá; registrar sha256.
   Foto/truecolor: `prepare_sms_pixel_art.py` (skill `sms-pixel-translate.md`).
   Paleta de outro console é régua, não fonte (L055).
2. Contrato `asset_contract_v1`: grid, kind, códigos de paleta.
3. Model sheet quando for personagem/inimigo/cenário final.
4. Exportar PNG indexado 8-bit p/ `res/` (índice 0 transparente, ≤15 úteis).
5. Rodar gates:
   - `audit_validate_resources.py`
   - `audit_luma_floor.py`
   - `audit_provenance.py`
6. Atualizar `doc/asset_provenance_manifest.json`.
7. Se for personagem/palco/HUD de entrega: skill `sms-visual-excellence.md`,
   contrato de escala no GDD, `audit_visual_delivery.py` e entrada no
   `doc/rom_asset_binding.json`. Sintaxe P/4bpp não fecha este passo.
8. Headroom de ROM menor que o custo do asset novo: **compor** com paleta,
   pose e fonte já carregadas antes de gerar (L049). Não inventar logo
   de 2 KB quando cabem 518 B de composição.
9. Falhou? Lição → workflow curation-learning. Persistência:
   `causal-persistence-loop.md` — não encerrar no diagnóstico.
