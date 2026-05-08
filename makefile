CONTAINER  = ubuntu-dev
ROOT       = $(PWD)
EXEC       = podman run --rm    -v $(ROOT):$(ROOT)
EXEC_IT    = podman run --rm -it -v $(ROOT):$(ROOT)

# ── Default target ────────────────────────────────────────────────────────────
# Runs all subsystems non-interactively (rebuilds docs from existing data).
# For the full publication_list workflow (fetch + interactive update) use
# make publication_list-all.
.PHONY: all
all: build publication_list talk_list media_list cv profile academic-webpage academic-webpage-static

# ── 0. Build the container image ──────────────────────────────────────────────
.PHONY: build
build:
	@NEEDS_BUILD=0; \
	if ! podman image exists $(CONTAINER); then \
	  NEEDS_BUILD=1; REASON="does not exist"; \
	else \
	  CREATED=$$(podman image inspect $(CONTAINER) --format '{{.Created}}' | cut -c1-19); \
	  CREATED_EPOCH=$$(date -jf '%Y-%m-%d %H:%M:%S' "$$CREATED" +%s 2>/dev/null || echo 0); \
	  TWO_WEEKS_AGO=$$(date -v-14d +%s); \
	  if [ "$$CREATED_EPOCH" -lt "$$TWO_WEEKS_AGO" ]; then \
	    NEEDS_BUILD=1; REASON="older than 2 weeks"; \
	  fi; \
	fi; \
	if [ "$$NEEDS_BUILD" = "1" ]; then \
	  echo "==> Building container image ($$REASON)..."; \
	  podman build -t $(CONTAINER) \
	    -f $(ROOT)/container/Containerfile \
	       $(ROOT)/container; \
	else \
	  echo "==> Container image is up to date, skipping build."; \
	fi

# ── publication_list ──────────────────────────────────────────────────────────
# Default: regenerate PDFs/Markdown from existing JSON (non-interactive).
.PHONY: publication_list
publication_list: build
	@echo "==> Building publication_list..."
	$(EXEC) -w $(ROOT)/publication_list $(CONTAINER) make docs NATIVE=1

.PHONY: publication_list-fetch
publication_list-fetch: build
	@echo "==> Fetching publications from InspireHEP..."
	$(EXEC) -w $(ROOT)/publication_list $(CONTAINER) make fetch NATIVE=1

# update is interactive — needs a TTY.
.PHONY: publication_list-update
publication_list-update: build
	@echo "==> Updating publication sub-lists (interactive)..."
	$(EXEC_IT) -w $(ROOT)/publication_list $(CONTAINER) make update NATIVE=1

# Full workflow: fetch + interactive update + docs.
.PHONY: publication_list-all
publication_list-all: build
	@echo "==> Running full publication_list workflow (interactive)..."
	$(EXEC_IT) -w $(ROOT)/publication_list $(CONTAINER) make all NATIVE=1

# ── talk_list ─────────────────────────────────────────────────────────────────
.PHONY: talk_list
talk_list: build
	@echo "==> Building talk_list..."
	$(EXEC) -w $(ROOT)/talk_list $(CONTAINER) make all

# ── media_list ────────────────────────────────────────────────────────────────
.PHONY: media_list
media_list: build
	@echo "==> Building media_list..."
	$(EXEC) -w $(ROOT)/media_list $(CONTAINER) make all

# ── cv ────────────────────────────────────────────────────────────────────────
.PHONY: cv
cv: build
	@echo "==> Building cv..."
	$(EXEC) -w $(ROOT)/cv $(CONTAINER) make all

# ── profile ───────────────────────────────────────────────────────────────────
.PHONY: profile
profile: build
	@echo "==> Building profile..."
	$(EXEC) -w $(ROOT)/profile $(CONTAINER) make all

# ── academic-webpage ──────────────────────────────────────────────────────────
# Default: process M4 templates to generate website content files.
.PHONY: academic-webpage
academic-webpage: build
	@echo "==> Processing academic-webpage M4 templates..."
	$(EXEC) -w $(ROOT)/academic-webpage $(CONTAINER) make all

# Build the full static Hugo site.
.PHONY: academic-webpage-static
academic-webpage-static: build
	@echo "==> Building academic-webpage static site (Hugo)..."
	@mkdir -p $(HOME)/.cache/hugo-go
	$(EXEC) -v $(HOME)/.cache/hugo-go:/root/go -w $(ROOT)/academic-webpage $(CONTAINER) hugo

# Run a local Hugo dev server on port 1313.
# Hugo modules are cached in ~/.cache/hugo-go between runs.
.PHONY: academic-webpage-server
academic-webpage-server: build
	@echo "==> Starting academic-webpage dev server on port 1313..."
	@mkdir -p $(HOME)/.cache/hugo-go
	podman run --rm -it -p 1313:1313 \
	  -v $(ROOT):$(ROOT) \
	  -v $(HOME)/.cache/hugo-go:/root/go \
	  -w $(ROOT)/academic-webpage $(CONTAINER) \
	  hugo server -D --bind=0.0.0.0 --disableFastRender

# ── clean ─────────────────────────────────────────────────────────────────────
.PHONY: clean
clean:
	@for dir in publication_list talk_list media_list cv profile academic-webpage; do \
	  echo "==> Cleaning $$dir..."; \
	  $(EXEC) -w $(ROOT)/$$dir $(CONTAINER) make clean NATIVE=1; \
	done

# ── help ──────────────────────────────────────────────────────────────────────
.PHONY: help
help:
	@echo "Targets:"
	@echo "  all                        rebuild all subsystems (non-interactive)"
	@echo "  build                      build the container image"
	@echo "  publication_list           regenerate publication list PDFs and Markdown"
	@echo "  publication_list-fetch     fetch latest publications from InspireHEP"
	@echo "  publication_list-update    sync sub-lists (interactive)"
	@echo "  publication_list-all       full workflow: fetch + update + docs (interactive)"
	@echo "  talk_list                  build talk list PDFs and Markdown"
	@echo "  media_list                 build media list PDFs and Markdown"
	@echo "  cv                         build CV and resume PDFs"
	@echo "  profile                    build profile HTML"
	@echo "  academic-webpage           process M4 templates for website content"
	@echo "  academic-webpage-static    build static Hugo site"
	@echo "  academic-webpage-server    run local Hugo dev server (port 1313)"
	@echo "  clean                      remove all generated files in all subsystems"
