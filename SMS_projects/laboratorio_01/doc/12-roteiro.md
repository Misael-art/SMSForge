# 12-roteiro — laboratorio_01

> Roteiro e diálogos. Autoridade #6.
> Criado em 2026-08-31 para fechar deriva detectada por `audit_doc_sync.py`.

## Declaração de escopo narrativo: N/A justificado

Este projeto é um **fixture de validação de pipeline**, não um produto narrativo.
Não há premissa, personagens nem diálogos — e isso é uma decisão registrada, não
uma lacuna a preencher.

Registrar "N/A" aqui é deliberado: a Hierarquia de Verdade exige que o arquivo
exista para que a ausência de roteiro seja uma **escolha auditável** e não um
esquecimento silencioso. Um projeto de jogo real que herdar o modelo encontra
este arquivo preenchido pelo template e não terá essa saída.

## Sequência funcional das cenas (substitui o roteiro)

O que faz as vezes de "beats" aqui é a ordem de capacidades provadas:

| Cena | Capacidade que a cena existe para provar | Estado |
|------|------------------------------------------|--------|
| 01 `boot_interativo` | boot determinístico + input → movimento visível + execução viva (spinner) | testado_em_emulador |
| 02 `sala do bloco` | primeiro gameplay real: colisão AABB, empurrar bloco, condição de vitória | testado_em_emulador (frame de vitória capturado) |
| 04 `game feel` | invulnerabilidade pós-hit, hitstop, screen shake, projétil, dificuldade progressiva | testado_em_emulador (60 fps estável) |

## Custo de texto na tela

O único texto do projeto é funcional (`VITORIA!` / `1:REINICIA` / contador hex).
Regra que vale para qualquer projeto herdeiro: **cada caractere é um tile na
VRAM** — texto é orçamento, e entra em `doc/13-spec-cenas.md` como tal.
