# skill: evidence-protocol

## Critério único
"Se não foi visto rodando no emulador, não existe."

## Evidência mínima por entrega
1. Build verde (`out/build_record.json`).
2. Boot no emulador gate (openmsx/Emulicious) com captura INFORMATIVA
   (`capture_evidence.py` reprova tela branca/vazia).
3. Gameplay real (input script quando aplicável).
4. FPS medido (frame counter no código + leitura no emulador).
5. Áudio audível na evidência.
6. Memory bank atualizado com status do vocabulário.

## Proibições
- Simular/maquetar evidência (crime fundador).
- Ler ferramenta sem self-check verde (§19).
- Claim acima do teto (§17).
