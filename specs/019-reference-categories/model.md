# Business model (TM)

People: operator registers visual examples and searches media.
Things: media asset (asset_id), reference category (category_id), immutable example
image snapshot, category catalog, classification result.
Events: category registered/deleted, import comparison succeeded/failed/deferred.
A category has a unique name, visual criteria and 1–3 examples. An image has zero
or one current classification report. A report covers every catalog category,
with model/prompt/catalog provenance and one match/no_match/uncertain decision
and reason each. Multiple categories may match. A report is an AI observation,
not a product identity claim. Generic and manual tags retain their meanings.

Unchanged successful reports are reusable, including uncertain outcomes. A changed
catalog invalidates every report immediately; a subsequent import reassesses.
Provider failure/deferment does not establish a negative observation or destroy
source/vectors. No categories means no classification calls.

Example: reference shows a pump bottle; image containing a pump bottle may match
容器ポンプ despite different background. A matching background without that
object is not a match. An obscured object is uncertain and adds no category tag.
No human category-specific examples have been supplied; these examples illustrate
policy and do not claim measured model accuracy.
