# Curated context: 005-template-adoption

## Purpose

Separate template dogfood history from adopting project history.

## Decisions

- `./scripts/adopt` once after “Use this template”
- Fixed list + unknown FAIL + double-adopt NO-OP
- Keep ADR/REFERENCES; reset PRODUCT/DOMAIN/GLOSSARY
- Markdown trailing whitespace preserved

## Known limitations

- Maintainers must extend EXPECTED_TEMPLATE_FEATURES for new dogfood
- adopt on a mistaken repo that only has expected names would delete them — fresh clone only
