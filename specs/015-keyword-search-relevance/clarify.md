# Clarify: Reliable keyword search

## Basis

- Human request (2026-09-06): search relevance is poor; improve keyword search.
- Existing human decision 007 D2: combine semantic and display-name/tag matching.
- Agent implementation scope: repair reproduced Japanese tag omissions and
  favor literal metadata matches within the existing combined search.
- A preference/example question was sent for follow-on prioritization. Its
  answer is not treated as approval of additional search modes or AI tagging.
- Human follow-up (2026-09-06): after implementation completion and the explicit
  report that production was not updated, requested proceeding. Release work
  now includes committing, PR/CI, merging and deploying this reviewed correction
  through the existing deployment procedure, preserving IAP.

## Unresolved items

None affecting this bounded correction. Broader search expansion requires its
own acceptance criteria once the operator provides direction.
