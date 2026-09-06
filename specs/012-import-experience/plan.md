# Plan: Import experience

1. Add `VectorSearchPort.has_frames(asset_id)`; fix skip = size match **and** has frames.
2. Cheap size check via `MediaStoragePort.size_bytes` before materialize; skip download when unchanged+has vectors.
3. `ImportJobRecord.only_keys` + `enqueue(only_keys=…)`; Library upload passes new asset ids; worker/local jobs honor scope.
4. `execute_storage(..., only_keys=)` filters work set.
5. Service `reload_db` after Job SUCCEEDED on poll (download GCS + swap sqlite conn on shared repos).
6. Hermetic bench test: N-file corpus + 1 new → incremental wall ≥3× vs full path.
7. Research note + full reviews.
