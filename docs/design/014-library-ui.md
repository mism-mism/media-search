# Design brief: media-search Library UI (014)

## Problem

Current `/` UI reads as an **internal verification console**: raw embedder IDs,
stacked forms, English/Japanese mix, card-less but still “admin CRUD dump”.
Operators need a **product-feeling media library + search** surface.

## Users & jobs

1. **Find** — type meaning / name → see ranked media fast  
2. **Browse** — folders → grid of assets  
3. **Ingest** — upload (+ optional product) → wait for Import  
4. **Organize** — rename / move / delete; manage product master (secondary)

## Information architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Brand: media-search                    [subtle status chip] │
│  ═══════════════════════════════════════════════════════════ │
│  SEARCH HERO (primary)                                       │
│  [ 意味・名前で探す…                    ] [種類▾] [検索]     │
└─────────────────────────────────────────────────────────────┘
┌──────────────┬──────────────────────────────────────────────┐
│ LIBRARY NAV  │  MAIN                                         │
│ Folders      │  Mode tabs:  ライブラリ  |  検索結果           │
│ + new folder │  Toolbar: Upload · Product select · crumb     │
│              │  Asset GRID (thumb dominant, not admin rows)  │
│ ──────────── │                                               │
│ Products     │  (Search mode shows result grid here)         │
│ (collapsed)  │                                               │
└──────────────┴──────────────────────────────────────────────┘
footer: embedder mode (muted, not hero)
```

### Hierarchy rules

- **Search is the hero** — first viewport is brand + one search field + one CTA.  
- **Library is the workspace** — folders + visual grid.  
- **Products are secondary** — collapsible section, not competing with upload.  
- **Hide debug** — `mode=` / model id only in footer.  
- **Status** — slim toast/banner under hero (Import progress), not a big dump box.  
- **Japanese UI chrome** — labels JA; keep API/asset ids in muted mono.

## Visual direction (“暗室アーカイブ”)

Not a purple SaaS dashboard. Not cream+terracotta magazine. Not newspaper grid.

| Token | Value |
|-------|--------|
| Mood | Quiet darkroom / film archive |
| BG | deep charcoal `#141618` with subtle grain |
| Surface | `#1e2124` |
| Text | `#ece8e1` |
| Muted | `#9a958c` |
| Accent | warm amber `#e2a15a` (search / focus only) |
| Danger | soft coral `#d9786a` |
| Fonts | Display: **Zen Old Mincho**; UI: **IBM Plex Sans JP** (Google Fonts) |
| Radius | 2–6px (slightly sharp, archival) |
| Motion | 2–3 only: hero fade-in, result stagger, status pulse while Import busy |

### Composition

- Full-bleed dark field; soft radial highlight behind search (not purple glow).  
- Asset **grid** (2–4 cols): large thumb, name, type/SKU caption — actions on hover.  
- No dashboard stat strips; no badge piles; no floating chips on thumbs.

## Technical constraints

- Keep **single-file HTML** in `src/media_search/api/app.py` `_ui_html()` (no React).  
- Preserve **all existing API calls** and behaviors (upload→pollJob, folders, products, search).  
- Accessibility: focus rings, contrast, button labels.  
- Mobile: stack sidebar above main; search stays sticky-ish near top.

## Out of scope

- New APIs, AI caption dual-index, auth UI, dark/light toggle.

## Acceptance (feel)

Opening `/` should feel like a **product**, not a pytest harness. Someone should
remember: dark archive + amber search bar + image grid.
