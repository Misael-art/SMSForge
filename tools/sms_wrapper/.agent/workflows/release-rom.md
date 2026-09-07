# workflow: release-rom

Pré-condição: os 7 eixos TRUE simultâneos (schema status_axes_v1).

0. **Build em modo estrito** — prova as ferramentas antes de confiar na leitura delas:
   ```sh
   SMS_STRICT=1 ./build.sh
   ```
   Roda `validate_measurement_tools.py` (§19) + `audit_doc_sync.py` antes de compilar.
   Não roda a cada build por custo (~3s); **na entrega é obrigatório**.
1. `audit_claims.py` verde (teto de "release" aprovado por humano) **e**
   quarentena de placeholder vazia:
   ```sh
   python3 tools/sms_wrapper/audit_placeholder_quarantine.py --project . --check-release
   ```
   Placeholder é legítimo durante o desenvolvimento e **proibido** na entrega.
   Liberar exige `"release_approved": true` + `"approved_by"` no manifest —
   campo estruturado, nunca prosa (nota como "arte final pendente" não aprova).
2. **Evidência recapturada DEPOIS desta ROM** (§26). Relinkou, os eixos de
   runtime caíram — recapture e sele o bundle:
   ```sh
   python3 tools/sms_wrapper/seal_fresh_evidence_bundle.py \
       --rom out/rom/<nome>.sms --artifact <cada captura> -o out/evidence/bundle.json
   python3 tools/sms_wrapper/screenshot_semantic_gate.py <shot.png> --claim <eixo>
   python3 tools/sms_wrapper/reconcile_claims.py --project .
   ```
2b. **Vídeo do eixo que ACONTECE** (§45/L056). Screenshot não sustenta transição,
   animação nem game feel — um PNG não tem eixo do tempo (§36). Grave do
   framebuffer, com o emulador parado antes (instância zumbi reescreve o `.ini`
   e apaga o atalho):
   ```sh
   pkill -f Emulicious.jar
   python3 tools/sms_wrapper/capture_video.py \
       --project . --rom out/rom/<nome>.sms --seconds 8 --out video_release \
       --press '<roteiro do eixo>'
   ```
   O `.mp4` e os frames-chave entram no `seal_fresh_evidence_bundle.py` do passo
   2 como qualquer outro artefato. O gate imprime `[NOTA] sem trilha de audio`
   quando o arquivo sai só com vídeo: **isso não fecha o eixo de áudio** — ele
   continua sendo do `capture_audio.py` (§31).
3. ROM versionada em `changelog/roms/build_vNNN/rom.sms`.
4. Teste em ≥2 emuladores (gate + secundário) e, quando possível, hardware real.
5. NTSC e PAL testados (timing normalizado provado).
6. Memory bank fecha o ciclo com links para evidências.

**Armadilha conhecida:** entregar com captura anterior à ROM final. Aconteceu no
laboratorio_01 (F6): as provas eram 6h mais velhas que o binário entregue.
Hoje `build_inner.py` rebaixa o eixo sozinho — não tente reescrever o registro
à mão para contornar.
