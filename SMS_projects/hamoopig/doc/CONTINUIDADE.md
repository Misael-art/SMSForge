# CONTINUIDADE — HAMOOPIG SMS

- **Data:** 2026-09-19
- **Marco:** guarda chip-2 **observada**. Throw **implementado não observado**. PSG sinal 49%. Worst-frame **derramou** (597/20s).
- **Hash:** `7a8951eef4c886e03631bffcefec55e45ae94fd1aedbb16f566f618679f361bd` (v009, 32768 B)
- **Último item:** L065–L068 registradas; BLOCK dummy; chip 2; B1+B2 throw; PSG; worst-frame
- **Próximo:** mapear B2 ou redesenhar throw com teclas conhecidas; reduzir vovf; BGM no título
- **Provas:** `guard_probe.json` (64→62, p2g=1); `worst_frame.json` derramou; `audio.wav` peak 7470 49%
- **Select:** Down = P2 BLOCK, Up = DUMMY, B2 cicla se o teclado entregar
- **Throw:** B1+B2, dano 10, MF_THROW
- **Não alargar hist[8]**
