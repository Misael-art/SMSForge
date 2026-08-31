# skill: sms-input-pause

## Input
- Joypad: portas 0xDC/0xDD (2 pads), d-pad + 2 botões.
- Ler uma vez por frame no loop principal; debouncing por frame counter.
- Libs opcionais (raphnet inlib) para light phaser/paddle — só com necessidade real.

## Pause
- Botão pause do console dispara NMI (`SMS_nmi_isr` do crt0).
- Tratamento: flag + retorno rápido; lógica pesada no loop principal.
- Estado PAUSE declarado na FSM global do TDD.
