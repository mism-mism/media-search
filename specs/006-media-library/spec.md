---
id: "006"
status: active
profile: full
profile_reason: "Library UX + virtual folders + upload/delete/move + search colocation"
---

# Spec: Media library (upload + folders + search)

## Problem

Operators manage media via `gsutil` and Import, then search elsewhere. There is
no clear **directory-like** place to upload, organize, delete/move/rename, and
search in one experience.

## Goal

A **library UI** with virtual folders, upload, management (delete / move /
rename), and **colocated semantic search**, auto-indexing new uploads via the
005 Import path.

## User

Team operators (IAP) managing a shared image/video corpus.

## Requirements

- R1. Browse assets in **virtual folders** (create / navigate).
- R2. **Upload** image and video into a chosen folder (GCS/local store; stable key).
- R3. **Delete**, **move** (folder_id), **rename** (display_name) — metadata move/rename; hard delete.
- R4. **Semantic search** on the same library screen.
- R5. Upload **auto-enqueues Import**.
- R6. Folders in sqlite; Domain free of GCP SDKs.

## Acceptance Criteria

- AC1. Create folder → upload media into it → after Import, asset listed in that folder.
- AC2. Move/rename update library view without changing `asset_id`.
- AC3. Delete removes asset from search, metadata, vectors, frames, and storage.
- AC4. Library UI runs semantic search and shows thumbnails/preview links.
- AC5. Upload enqueues Import without a separate Import click.
- AC6. Out of Scope upheld.

## Out of Scope

- GCS prefix-as-folder UX
- Vertex embedder cutover
- Fine video timeline index
- Soft-delete / trash
- Public (non-IAP) access

## Constraints

- Clarify D1–D11 locked.
- Prefer extending 005 ImportJobPort / MediaStoragePort.

## Open Questions

- None
