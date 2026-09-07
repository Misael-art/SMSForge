# Biblioteca de referência — Super Street Fighter 2 Turbo (SMS)

> **Status: `reference_only`.** Nada aqui é arte de entrega.
> Esta biblioteca alimenta o estudo de viabilidade do port de teste para
> Master System. A conversão futura vive em `SMS_projects/ssf2t_sms/`
> (a criar via `tools/sms_wrapper/new_project.sh`) e, por lei do workspace
> (§15/§39 do `SMS_GLOBAL.md`), a arte final da ROM será pixel art autoral
> SMS-nativa derivada destas referências — nunca os rips diretos.

## Origem

Sheets públicas de The Spriters Resource (comunidade), ripadas do arcade
CPS-2 (e uma do SNES, marcada) — **Capcom ©, uso pessoal de teste**.
Proveniência máquina-legível: `provenance_manifest.json`.
Índice humano: `asset_list.md`. Regras de nome: `organization.md`.

## Estrutura

```
sprites/               lutadores (Ken, Guile + bônus Sagat) e projéteis
backgrounds/stages/    cenários (Guile, Ken, Sagat-SNES + bônus Balrog)
title/screens/         select ST, versus, continue portraits
hud/                   health bars, timer, fonte completa, textos
endings/scenes/        endings (World Warrior — ST reaproveita)
audio/music/           tracks.md (sem binários: ROM SMS usa PSG, não MP3)
manuals/docs/          movelists de referência (Ken, Guile)
```

## Lacunas declaradas (não preencher com mockup)

- Arte da title screen / attract-mode opening: nenhuma sheet no arcade.
- Versus específico do ST: só existe o da Champion Edition.
- Stage arcade do Sagat: não existe (boss); usado SNES como referência.
- Endings próprios do ST: não encontrados; WW documentado.
- Áudio: composições PSG são trabalho futuro (`make_psg_assets.py`).

## Escopo desta etapa: localizar + depositar + indexar. Sem conversão, sem ROM.
