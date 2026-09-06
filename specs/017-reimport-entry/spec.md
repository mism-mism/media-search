---
id: "017"
status: completed
profile: lean
profile_reason: "Local UI entry to existing import endpoint; no API, domain, auth or storage changes"
---

# Spec: Reimport entry in the library

## Goal

The user could not find the reimport action mentioned in 016 guidance because
no button was present. Add the requested visible UI entry for existing media.

## Acceptance Criteria

- AC1. Library shows a clearly labeled 再取り込み button below upload controls,
  including with an empty current folder, on desktop/mobile. Explain that the
  action covers all folders and fills missing AI tags/descriptions under the
  configured per-import cap (default 50), reusing completed results.
- AC2. Click calls existing POST /api/import without a local path override,
  follows the returned job, shows queued/running/terminal status, and refreshes
  library cards at completion. Preserve existing API and single-writer lock.
- AC3. Repeated clicks and upload/reimport overlap in the same page cannot enqueue
  twice. Disable both actions while pending/running, restore after success/error,
  and show enqueue/poll/network failures. Existing upload behavior remains usable.
- AC4. Verify the actual UI event path for success, terminal failure and request
  failure; run regression suite, lean independent reviews, hooks and CI. Deploy
  the reviewed UI and record actual verification limitations.

## Review follow-up acceptance (PR #19)

- AC5. Use the real HTTP409 object detail (`error=import_busy`) in UI tests;
  show a fixed Japanese busy message without exposing the holder identifier.
- AC6. Test synchronous ImportResponse (imported/updated/skipped arrays): refresh
  cards, success banner, no job polling, and restored controls. Unknown response
  shapes must show an error rather than claiming completion.
- AC7. Toolbar guidance explicitly includes failed and deferred image generation
  in the next reimport, while retaining whole-library scope and default cap.

## Constraints / Out of Scope

Keep existing visual style and accessible native buttons/live status. No new API,
folder-scoped import, new annotation behavior, automatic corpus backfill, or
reference-image categorization. No unresolved business decisions.
