# Índice de assets — biblioteca SSF2T (`reference_only`)

Coleta: 2026-09-06. Fonte: The Spriters Resource. Verificação de conteúdo:
`visual` = inspecionado nesta sessão; `metadados` = nome/tamanho/dimensões
conferidos com a página-fonte (inspeção visual pendente na conversão).

## sprites/ — lutadores e projéteis (arcade CPS-2)

| Arquivo | Sheet fonte | Dimensões | Bytes | Verif. | Notas SMS |
|---|---|---|---|---|---|
| `ken_arcade_st_v1.png` | Ken (Fighters) | 1549×11279 | 1008844 | metadados | Pedido central. Idle ~90–100px → redução ~2× + metasprite; 8 sprites/scanline manda selecionar frames (idle, walk, socos, chutes, Hadouken, Shoryuken, Tatsumaki, hit, KO). |
| `guile_arcade_st_v1.png` | Guile (Fighters) | 847×8630 | 916335 | metadados | Pedido central. Mesmo tratamento do Ken; Sonic Boom e Flash Kick incluídos na strip. |
| `sagat_arcade_st_v1.png` | Sagat (Fighters) | 922×7201 | 624380 | metadados | BÔNUS (mesmo custo). Referência de boss futuro; Tiger Shot/Uppercut na strip. |
| `effects_projectiles_arcade_v1.png` | Effects (Misc) | 296×256 | 9708 | metadados | BÔNUS. Hadouken / Sonic Boom / faíscas — base dos projéteis de Ken e Guile. |
| `ryu_arcade_st_v1.png` | Ryu (Fighters) | 1549×12116 | 1123708 | metadados | Roster completo. Mesmo demake dos demais: redução + metasprite + frames selecionados. |
| `blanka_arcade_st_v1.png` | Blanka (Fighters) | 1875×5021 | 1577659 | metadados | Roster completo. Electric Thunder = efeito de área (tiles animados, não sprite). |
| `zangief_arcade_st_v1.png` | Zangief (Fighters) | 850×9167 | 1180572 | metadados | Roster completo. Grappler alto; piledrivers exigem pares de poses sincronizadas. |
| `dhalsim_arcade_st_v1.png` | Dhalsim (Fighters) | 850×8475 | 1119205 | metadados | Roster completo. Membros extensíveis estouram qualquer orçamento de scanline — candidato a redesenho pesado. |
| `deejay_arcade_st_v1.png` | Dee Jay (Fighters) | 844×8349 | 997529 | metadados | Roster completo. |
| `cammy_arcade_st_v1.png` | Cammy (Fighters) | 2891×4381 | 1106058 | metadados | Roster completo. |
| `bison_arcade_st_v1.png` | M. Bison (Fighters) | 2056×1322 | 502626 | metadados | Roster completo. Sheet compacta (checar cobertura de golpes na conversão). |

## sprites/ — lutadores SNES (sem sheet arcade; GIF original)

| Arquivo | Sheet fonte | Dimensões | Bytes | Verif. | Notas SMS |
|---|---|---|---|---|---|
| `honda_snes_v1.gif` | E. Honda (SNES New Challengers) | 1457×1260 | 204510 | metadados | Sem arcade. GIF preservado; conversão trata o formato. Hundred Hand Slap = ciclo rápido de 2–3 frames. |
| `chunli_snes_v1.gif` | Chun-Li (SNES New Challengers) | 1453×1222 | 216543 | metadados | Sem arcade. Lightning Kick = ciclo rápido; filereference p/ Kikoken. |
| `balrog_snes_v1.gif` | Balrog (SNES New Challengers) | 1046×1204 | 169002 | metadados | Sem arcade. Dash punches = deslocamento + pose estendida. |
| `vega_snes_v1.gif` | Vega (SNES New Challengers) | 1623×1273 | 204781 | metadados | Sem arcade. Wall dive exige palco com parede — amarrar ao stage. |
| `thawk_snes_v1.gif` | T. Hawk (SNES New Challengers) | 1786×1328 | 316680 | metadados | Sem arcade. Maior sprite do set; 360/720 exigem par sincronizado. |
| `feilong_snes_v1.gif` | Fei Long (SNES New Challengers) | 1558×1079 | 206946 | metadados | Sem arcade. Rekka = sequência de 3 avanços encadeados. |

## backgrounds/stages/ — cenários

| Arquivo | Sheet fonte | Dimensões | Bytes | Verif. | Notas SMS |
|---|---|---|---|---|---|
| `stage_guile_arcade_v1.png` | Guile Stage | 1040×624 | 64167 | visual | Pedido central. Base aérea (F-16, hangares, crowd). 1040px → scroll + metatiles; teto 256 tiles BG. |
| `stage_sagat_snes_v1.png` | Sagat Stage (SNES) | 512×464 | 41315 | metadados | Pedido central com ressalva: **não existe stage arcade do Sagat** (boss sem palco no ST); referência SNES. |
| `stage_ken_arcade_v1.png` | Ken's Stage | 912×576 | 109568 | metadados | BÔNUS. Porto/USA; mesmo orçamento de scroll do Guile. |
| `stage_balrog_arcade_v1.png` | "Title" (Misc — é o stage do Balrog + intros) | 1080×528 | 79302 | visual | BÔNUS. Nome da sheet engana: contém Las Vegas (céu, crowd, torre) e retratos de intro do Balrog. |
| `stage_honda_arcade_v1.png` | E. Honda's Stage | 888×472 | 68674 | metadados | Roster completo. Palco estreito (888px) — scroll curto, bom candidato a primeiro stage jogável. |
| `stage_blanka_arcade_v1.png` | Blanka's Stage | 1024×480 | 98454 | metadados | Roster completo. Selva; parallax em camadas exige line interrupt (técnica medida, não gratuita — §6). |
| `stage_chunli_arcade_v1.png` | Chun-Li's Stage | 1056×1008 | 140214 | metadados | Roster completo. Mercado com vendedores e ciclista; elementos animados viram tiles animados ou sprites caros. |
| `stage_ryu_snes_v1.png` | Ryu Stage (SNES) | 512×769 | 28290 | metadados | Sem arcade. Japão/noturno; SNES 512px = referência de composição. |
| `stage_feilong_snes_v1.png` | Fei Long Stage (SNES) | 512×1048 | 75444 | metadados | Sem arcade. Hong Kong; amarrar wall dive do Vega? Não — é do Fei Long; Vega usa grade própria (lacuna). |
| `stage_bison_snes_v1.png` | M. Bison Stage (SNES) | 512×582 | 53725 | metadados | Sem arcade. Templo; palco de boss — prioridade baixa no teste. |
| `stage_cammy_snes_v1.png` | Cammy Stage (SNES) | 512×1192 | 75980 | metadados | Sem arcade. Inglaterra/castelo. |
| `stage_deejay_snes_v1.png` | Dee Jay Stage (SNES) | 512×1312 | 105937 | metadados | Sem arcade. Jamaica/praia. |
| `stage_thawk_snes_v1.png` | T. Hawk Stage (SNES) | 512×1320 | 71561 | metadados | Sem arcade. México/deserto. |

## title/screens/ — telas

| Arquivo | Sheet fonte | Dimensões | Bytes | Verif. | Notas SMS |
|---|---|---|---|---|---|
| `select_character_st_v1.png` | Character Select (X/ST) | 443×1146 | 154758 | visual | Pedido central. Grid 4×4 + mapa-múndi; cursor 1P/2P vira sprite, fundo vira BG estático. |
| `versus_screen_ce_v1.png` | Versus Screen (Champion Edition) | 1160×654 | 222803 | metadados | Pedido central com ressalva: **só existe versus da CE**; layout reaproveitável, arte ST a derivar. |
| `continue_portraits_st_v1.png` | Continue Portraits (ST) | 1368×2364 | 563159 | metadados | Pedido central. Retratos grandes → reduzir para 256×192 ou recortar busto. |

## hud/ — HUD e fontes

| Arquivo | Sheet fonte | Dimensões | Bytes | Verif. | Notas SMS |
|---|---|---|---|---|---|
| `hud_fonts_healthbars_v1.png` | Game Text, Fonts, & Health Bars | 496×224 | 20369 | visual | Pedido central. Barras, KO, timer, alfabeto completo 2 cores, FIGHT!/ROUND, nomes dos 16. Base direta da fonte 8×8 do projeto. Nota: HUD é CPS-1; separar do ST na conversão. |

## endings/scenes/ — finais

| Arquivo | Sheet fonte | Dimensões | Bytes | Verif. | Notas SMS |
|---|---|---|---|---|---|
| `endings_ww_v1.png` | Character Endings (World Warrior) | 1000×3082 | 342605 | metadados | Pedido central com ressalva: **ST reaproveita endings WW**; quadros de Ken/Guile a localizar na strip durante a conversão. Cenas finais da ROM serão arte autoral. |

## audio/music/ — sem binários por decisão

Só `tracks.md` (temas-alvo + estratégia PSG). MP3 não entra em ROM SMS.

## manuals/docs/ — referência de design

`movelist_ken.md`, `movelist_guile.md` (golpes para o GDD futuro; frame data
se valida contra as strips na conversão).

## Lacunas declaradas

1. **Title screen / opening attract**: nenhuma sheet no arcade. Captura
   própria futura ou arte autoral — nunca mockup.
2. **Versus do ST**: só CE disponível.
3. **Stage arcade do Sagat**: inexistente; SNES como referência.
4. **Endings próprios do ST**: não encontrados; WW documentado.
5. **Stages sem sheet em nenhuma plataforma**: Zangief, Dhalsim e Vega.
   Candidatos futuros: spritedatabase.net ou captura própria — nunca mockup.
6. **Roster de lutadores: COMPLETO 16/16** (10 arcade + 6 SNES).
   Stages: 13/16 cobertos (5 arcade + 1 parcial Balrog + 7 SNES).
