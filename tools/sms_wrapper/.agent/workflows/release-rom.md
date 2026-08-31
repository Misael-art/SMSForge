# workflow: release-rom

Pré-condição: os 7 eixos TRUE simultâneos (schema status_axes_v1).
1. `audit_claims.py` verde (teto de "release" aprovado por humano).
2. ROM versionada em `changelog/roms/build_vNNN/rom.sms`.
3. Teste em ≥2 emuladores (gate + secundário) e, quando possível, hardware real.
4. NTSC e PAL testados (timing normalizado provado).
5. Memory bank fecha o ciclo com links para evidências.
