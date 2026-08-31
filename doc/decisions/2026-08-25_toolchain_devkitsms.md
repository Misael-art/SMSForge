# Decisão de fundação: toolchain SDCC + devkitSMS

- **Data:** 2026-08-25
- **Status:** aceita
- **Contexto:** porte do SGDKForge para Master System exige equivalente ao papel
  que SGDK 2.11 ocupa no Mega Drive: SDK C oficial da comunidade, com headers
  como autoridade de API e pipeline de build reprodutível.
- **Alternativas consideradas:**
  - Assembly puro (WLA-DX): controle total, mas abandona o paralelo "SGDK : MD :: X : SMS"
    e o modelo de projeto em C. Perdeu.
  - SGlib-only (SG-1000): subconjunto; alvo primário é SMS. Fica como extensão declarada.
- **Decisão:** SDCC ≥4.2 + devkitSMS (SMSlib/PSGlib/crt0/makesms/assets2banks).
  Headers `SMSlib.h` / `PSGlib.h` = autoridade #8 da hierarquia de verdade.
  Build canônico documentado em `sdk/README.md`, orquestrado apenas por
  `tools/sms_wrapper/build_inner.py`.
- **Consequências:** projetos não tocam toolchain; gates rodam antes/depois do sdcc;
  ausência de toolchain = falha honesta FAIL_AMBIENTE, nunca simulação.
