# Everyday operator targets for media-search.
# Defaults match the current GCP project; override on the CLI as needed.
#
#   make test
#   make deploy

PROJECT  ?= laperm-507708
REGION   ?= asia-northeast1
SERVICE  ?= media-search
JOB      ?= media-search-import
IMAGE_TAG ?= latest
IMAGE_ANNOTATION_BACKEND ?= gemini
IMAGE_ANNOTATION_MODEL ?= gemini-3.1-flash-lite
IMAGE_ANNOTATION_LOCATION ?= global
IMAGE_ANNOTATION_MAX_PER_IMPORT ?= 50
ANNOTATION_ENV := IMAGE_ANNOTATION_BACKEND=$(IMAGE_ANNOTATION_BACKEND),IMAGE_ANNOTATION_MODEL=$(IMAGE_ANNOTATION_MODEL),IMAGE_ANNOTATION_LOCATION=$(IMAGE_ANNOTATION_LOCATION),IMAGE_ANNOTATION_MAX_PER_IMPORT=$(IMAGE_ANNOTATION_MAX_PER_IMPORT)
REPO     := $(REGION)-docker.pkg.dev/$(PROJECT)/media-search-repo
IMAGE    := $(REPO)/media-search:$(IMAGE_TAG)
BUCKET   := media-search-$(PROJECT)-media

.PHONY: help test deploy docker-prune

help:
	@echo "make test          # pytest (uses .venv if present)"
	@echo "make deploy        # amd64 build → push → Cloud Run service + import Job"
	@echo "make docker-prune  # free Docker disk (fixes 'No space left on device')"
	@echo "                   # optional: make deploy IMAGE_TAG=005-006"

test:
	@if [ -x .venv/bin/python ]; then \
	  .venv/bin/python -m pytest -q; \
	else \
	  python3 -m pytest -q; \
	fi

docker-prune:
	docker builder prune -af
	docker image prune -af
	@docker system df

deploy:
	@set -euo pipefail; \
	gcloud auth configure-docker "$(REGION)-docker.pkg.dev" --quiet; \
	DOCKER_BUILDKIT=1 docker build --platform linux/amd64 \
	  --build-arg INSTALL_SEMANTIC=1 \
	  --build-arg INSTALL_GCP=1 \
	  --build-arg PREWARM_OPENCLIP=1 \
	  -t "$(IMAGE)" .; \
	docker push "$(IMAGE)"; \
	SA=$$(gcloud run services describe "$(SERVICE)" \
	  --project="$(PROJECT)" --region="$(REGION)" \
	  --format='value(spec.template.spec.serviceAccountName)'); \
	gcloud run deploy "$(SERVICE)" \
	  --project="$(PROJECT)" \
	  --region="$(REGION)" \
	  --image="$(IMAGE)" \
	  --no-allow-unauthenticated \
	  --cpu=2 \
	  --memory=8Gi \
	  --port=8080 \
	  --timeout=300 \
	  --min-instances=1 \
	  --no-cpu-throttling \
	  --update-env-vars="$(ANNOTATION_ENV),EMBEDDER=local,MEDIA_BACKEND=gcs,GCS_PREFIX=incoming,MEDIA_SEARCH_DATA=/tmp/media-search,MEDIA_SEARCH_DB=/tmp/media-search/media-local-cos.db,MEDIA_SEARCH_WORK=/tmp/media-search/work,FRAME_BACKEND=gcs,GCS_FRAMES_PREFIX=frames,IMPORT_LOCK_BACKEND=gcs,IMPORT_JOB_BACKEND=cloudrun,CLOUD_RUN_IMPORT_JOB=$(JOB),GOOGLE_CLOUD_PROJECT=$(PROJECT),CLOUD_RUN_REGION=$(REGION),GCS_BUCKET=$(BUCKET),MEDIA_SEARCH_DB_GCS=gs://$(BUCKET)/state/media-local-cos.db"; \
	if gcloud run jobs describe "$(JOB)" --project="$(PROJECT)" --region="$(REGION)" >/dev/null 2>&1; then \
	  JOB_CMD=update; \
	else \
	  JOB_CMD=create; \
	fi; \
	gcloud run jobs "$$JOB_CMD" "$(JOB)" \
	  --project="$(PROJECT)" \
	  --region="$(REGION)" \
	  --image="$(IMAGE)" \
	  --service-account="$$SA" \
	  --cpu=4 \
	  --memory=16Gi \
	  --task-timeout=3600 \
	  --max-retries=0 \
	  --command=python \
	  --args=-m,media_search.worker_import \
	  --set-env-vars="$(ANNOTATION_ENV),IMPORT_MODE=worker,EMBEDDER=local,MEDIA_BACKEND=gcs,GCS_BUCKET=$(BUCKET),GCS_PREFIX=incoming,FRAME_BACKEND=gcs,GCS_FRAMES_PREFIX=frames,IMPORT_LOCK_BACKEND=gcs,MEDIA_SEARCH_DATA=/tmp/media-search,MEDIA_SEARCH_DB=/tmp/media-search/media-local-cos.db,MEDIA_SEARCH_DB_GCS=gs://$(BUCKET)/state/media-local-cos.db,MEDIA_SEARCH_WORK=/tmp/media-search/work,GOOGLE_CLOUD_PROJECT=$(PROJECT),CLOUD_RUN_REGION=$(REGION),IMPORT_EMBED_WORKERS=4"; \
	gcloud run jobs add-iam-policy-binding "$(JOB)" \
	  --project="$(PROJECT)" --region="$(REGION)" \
	  --member="serviceAccount:$$SA" \
	  --role="roles/run.developer" >/dev/null; \
	echo "Deployed $(IMAGE)"; \
	gcloud run services describe "$(SERVICE)" \
	  --project="$(PROJECT)" --region="$(REGION)" \
	  --format='value(status.url)'
