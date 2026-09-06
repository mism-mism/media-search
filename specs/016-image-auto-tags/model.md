# Business model: Image search enrichment

## Purpose and vocabulary

People: operator who imports and searches media. Things: media asset (asset_id),
product (product_id), operator-supplied metadata, generated image description.
Events: import, successful image description, failed description attempt, search.

A media asset has zero or one current generated description; that description
contains multiple tags, one short text and generation provenance. Generated
observations are search aids; they do not establish product identity or replace
facts supplied by the operator. No new actor identity is inferred from a photo.

## Rules and lifecycle

- Asset identity remains its existing asset_id. Product association is unchanged.
- Before generation, an image is pending. Valid output makes it ready. A failed
  attempt records a safe failure code; a later import may retry. A run's request
  cap can defer an image without claiming it failed at the provider.
- A completed description is reused when existing import logic says unchanged.
- Changed image content (as detected by existing import) replaces old generated
  observations; stale generated text must not be shown after generation fails.
- Failure to describe an image does not remove its source, metadata or vectors.
- Searchable tags are the union of manual and generated tags; provenance remains
  distinguishable in returned/displayed data.

## Examples and counterexamples

An image named IMG_01.jpg with no manual tags can gain tags such as 白いボトル and
手持ち. A search for 手持ち can retrieve it. Its operator-assigned product_id does
not become a guessed SKU. A subsequent import does not repeat completed work.
If generation fails, existing manual tag 広告 and its frame vector remain usable;
reimport retries only the missing generated description for unchanged content.

## Evidence, assumptions and architecture implications

Human intent is the accepted recommendation; lifecycle/reuse/failure semantics
are conservative implementation choices preserving existing behavior. The size
comparison used for unchanged media is inherited, not a checksum guarantee.
Generation needs an inward-owned image-description boundary and a separately
stored value. No middleware selection is required by this business model.
