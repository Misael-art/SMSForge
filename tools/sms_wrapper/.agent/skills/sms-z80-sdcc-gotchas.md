# skill: sms-z80-sdcc-gotchas

## Assumir como suspeita até pagar com build
- `int` = 16-bit signed (SDCC z80). Overflow silencioso em contagens grandes.
- Multiplicação/divisão caras: tabelas lookup, Q8.8, deslocamentos.
- float/double: software float — PROIBIDOS em runtime quente.
- RAM 8KB: sem malloc/free; pools estáticos por entidade; stack pequena.
- `__z88dk_fastcall` / `__sdcc_call(1)`: convenções do header mandam, não a intuição.
- Locais recarregam via IX; ponteiros `static` no hot path.
- Espelhar tile em runtime (bitrev) troca ROM por CPU. Curva paga
  (STREAM_BYTES): 32→59.5 fps, 64→58.3, 96→57.5, 128→55.5, 256→40 (L045).

## Build canônico (devkitSMS)
```
sdcc -c -mz80 main.c
sdcc -o game.ihx -mz80 --no-std-crt0 --data-loc 0xC000 crt0_sms.rel main.rel SMSlib.lib PSGlib.lib
makesms game.ihx game.sms
```
crt0 SEMPRE primeiro; libs DEPOIS do código. Só o wrapper monta isso.
