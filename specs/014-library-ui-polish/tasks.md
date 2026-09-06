# Tasks: Library UI polish

- [x] T000 Lock brief + activate
- [x] T010 Codex implements `_ui_html` per design brief
- [x] T020 Lean reviews

## v2 — Studio light DAM (human-requested revision)

- [x] T030 Rewrite the UI to the v2 brief while preserving API flows
- [x] T040 Verify API regressions and DOM interactions; independent Inner reviews (browser rendering unavailable: sandbox MachPort denial)
- [x] T050 Independent Outer product review and lifecycle gates
- [x] T060 Inner review follow-up: synchronize product captions on existing library/search cards after product rename
- [x] T070 Clarify folder navigation: here-card, clickable breadcrumbs, child-folder list labels (remove root/parent buttons)

## Handoff (next session)

Done on this branch / PR #16:
- Light DAM UI (`docs/design/014-library-ui.md` v2)
- Upload button right-aligned in toolbar
- Folder location chrome (ここまででユーザー確認済みの見た目改善)

Still open / not claimed done:
- [ ] Human visual pass on folder nav + any remaining polish feedback
- [ ] Deploy + browser check under IAP (prod)
- [ ] Re-run pre-review / Outer if more UI changes land after this commit
- [ ] Merge only after AC + gates

Local preview used: `EMBEDDER=fake` uvicorn on `http://127.0.0.1:8000/`
Do not commit `.playwright-mcp/` or ad-hoc screenshots.
