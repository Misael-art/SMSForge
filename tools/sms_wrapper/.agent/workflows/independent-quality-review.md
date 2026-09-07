# workflow: independent-quality-review

Use nos checkpoints `foundation`, `pre_growth`, `vertical_slice` e
`release_candidate`. Não em cada edição pequena.

1. Materialize um `quality_review_request` com artefatos hash-bound, estágio,
   domínios e produtor.
2. Execute `quality_review_router.py plan` — no máximo três reviews.
3. Com dois ou mais ramos longos, passe o taskset a `harness_orchestration.py`.
   Reviewers são read-only e independentes do produtor.
4. Consolide `independent_quality_review` sem expor raciocínio interno.
5. Execute `validate-report`. Descarte parecer stale, autoaprovado ou que
   declare `ready_for_aaa`.
6. Corrija somente as três prioridades, pelos owner skills indicados.
7. Reavalie o delta. Claim, escopo, promoção e git ficam no coordenador.

`defect`/`risk` demonstrado → `revise_before_growth`.
`opportunity`/`taste` não bloqueia. Mudança de escopo abre decisão humana.
