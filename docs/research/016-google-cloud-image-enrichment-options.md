# Research: Google Cloud image vectors and Japanese tags

Date: 2026-09-06  
Status: research note only; not an approved feature, architecture, or implementation.  
Method: official documentation and existing repository evidence; no model API calls, infrastructure changes, or benchmark run.

## Findings

Google Cloud provides the components to accept an image, generate tags and a vector, and persist both. Generating annotations/embeddings and saving searchable application records are separate responsibilities. The following is a possible composition, not a selected implementation.

| Need | Official capability | Implication |
|---|---|---|
| Generic labels | Cloud Vision Label Detection returns general entities/categories and scores; labels are English only. | Japanese display requires translation or a different tagging route. [Detect Labels](https://docs.cloud.google.com/vision/docs/labels) |
| Japanese descriptive tags | Gemini accepts images and returns text; Gemini language support includes Japanese. | Ask for Japanese category/color/scene tags. This is a use-case inference from the documented capabilities; tag accuracy on this library is untested. [Image understanding](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/capabilities/image-understanding), [Gemini language support](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/google-models?hl=ja#gemini) |
| Predictable tag record | Gemini structured output supports a response schema, string enums, and JSON. | Use `response_schema` with `response_mime_type="application/json"`; a schema controls shape, not the truth of inferred tags. [Structured output](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/capabilities/control-generated-output) |
| Image vectors | `gemini-embedding-2` accepts multimodal input and outputs up to 3072 dimensions in a shared semantic space; the model card lists GA, released 2026-04-22. | A current candidate exists beyond `multimodalembedding@001`. This embedding model outputs vectors, not human-readable tags. [Gemini Embedding 2](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/embedding-2) |
| Persist/retrieve | Firestore supports vector fields alongside document fields and nearest-neighbor search. | Save image reference, tags, and vector in an application record; create the required vector index. Maximum supported vector dimension is 2048, so the 3072-dimensional default cannot be used unchanged. [Firestore vector search](https://firebase.google.com/docs/firestore/vector-search) |

## Language and model boundaries

- Current multimodal embedding documentation lists both `gemini-embedding-2` and `multimodalembedding@001`. The former supports configurable output dimensionality, allowing an output size compatible with Firestore. [Get multimodal embeddings](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/embeddings/get-multimodal-embeddings)
- Google explicitly describes `gemini-embedding-2` as multilingual in its Memory Bank guidance. That does not establish Japanese image-search quality for this project's corpus. [Memory Bank similarity configuration](https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/memory-bank/setup)
- The current redirected `multimodalembedding@001` pages consulted did not establish a Japanese support commitment. Do not assume Japanese query support from image-input support, or treat the historical English-only claim as newly verified here. [Multimodal embeddings API](https://docs.cloud.google.com/gemini-enterprise-agent-platform/reference/models/multimodal-embeddings-api)
- Japanese tags embedded using a text embedding model are representations of the tag text. They are not automatically comparable to image vectors from a different model; shared-space retrieval needs a compatible model and indexing configuration. This follows from the documented shared-space requirement. [Get multimodal embeddings](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/embeddings/get-multimodal-embeddings)

## Project implications, not implementation decisions

A reasonable option to evaluate is generating Japanese tags and image vectors during import, storing them for subsequent searches. Treat generic labels and visual similarity as descriptive/search signals, not proof of SKU identity. The project's SKU evaluation explicitly reserves exact identity for `product_id` and requires real product-image evidence before a production switch. [008 spec](../../specs/008-sku-product-embedder-eval/spec.md), [008 research](008-sku-product-embedder-eval.md)

The earlier BigQuery no-go concerned interactive retrieval latency: the tested path stored existing OpenCLIP vectors in BigQuery; its BQ/Vertex embedding-generation pass was skipped. It is not evidence that Google embeddings or automatic Japanese tagging are poor. [011 research](011-bigquery-vector-search-eval.md)

Choosing a production model/store still needs sample evaluation of Japanese tag usefulness, retrieval quality, latency, and cost. This note authorizes no provider cutover or new feature implementation.
