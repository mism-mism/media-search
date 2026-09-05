from __future__ import annotations

from pathlib import Path


def download_db_if_remote(*, gcs_uri: str, local_path: Path) -> None:
    """If gcs_uri is gs://bucket/object, download to local_path when remote exists."""
    if not gcs_uri.startswith("gs://"):
        return
    from google.cloud import storage as gcs

    _, _, rest = gcs_uri.partition("gs://")
    bucket_name, _, blob_name = rest.partition("/")
    if not bucket_name or not blob_name:
        raise ValueError(f"invalid gs uri: {gcs_uri}")
    client = gcs.Client()
    blob = client.bucket(bucket_name).blob(blob_name)
    local_path.parent.mkdir(parents=True, exist_ok=True)
    if blob.exists():
        blob.download_to_filename(str(local_path))


def upload_db(*, gcs_uri: str, local_path: Path) -> None:
    if not gcs_uri.startswith("gs://"):
        return
    if not local_path.is_file():
        return
    from google.cloud import storage as gcs

    _, _, rest = gcs_uri.partition("gs://")
    bucket_name, _, blob_name = rest.partition("/")
    client = gcs.Client()
    client.bucket(bucket_name).blob(blob_name).upload_from_filename(str(local_path))
