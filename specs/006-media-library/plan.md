# Plan: Media library

Clarify D1–D11 locked. Profile **full**.

## Architecture

```text
Library UI
  ├ folders CRUD (sqlite)
  ├ asset list by folder_id
  ├ multipart upload → MediaStorage.put → metadata stub? → ImportJob.enqueue
  ├ PATCH display_name / folder_id
  ├ DELETE storage + vectors + frames + metadata
  └ semantic search (existing SearchMediaAssets)
```

Upload keys: `library/{uuid}_{safe_filename}` (stable `asset_id`).

## Schema (sqlite)

- `folders(folder_id TEXT PK, name TEXT, parent_id TEXT NULL)`
- `assets` add `display_name TEXT`, `folder_id TEXT NULL`

## Ports

- Extend `MediaStoragePort`: `put_bytes`, `delete`
- `FolderRepositoryPort`
- Extend metadata: `delete`, `list_by_folder`, display fields on `MediaAsset`

## Tasks

See `tasks.md`.
