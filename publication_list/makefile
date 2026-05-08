CONTAINER  = ubuntu-dev

# Pass NATIVE=1 when tools are already available in PATH (e.g. inside the
# container launched by the root makefile). In that case the podman wrapper
# is skipped and commands run directly.
ifdef NATIVE
  EXEC    =
  EXEC_IT =
else
  EXEC    = podman run --rm    -v $(PWD):$(PWD) -w $(PWD) $(CONTAINER)
  EXEC_IT = podman run --rm -it -v $(PWD):$(PWD) -w $(PWD) $(CONTAINER)
endif

LISTS      = complete experiment physics computing \
             short_physics short_computing \
             shortest_physics shortest_computing

PDFS       = $(addsuffix _publication_list.pdf, $(LISTS))
MARKDOWNS  = $(addsuffix _publication_list.md,  $(LISTS))
BIBS       = $(addsuffix _publication_list.bib, $(LISTS))
JSONS      = $(addsuffix _publication_list.json, $(LISTS))

# ── Default target ────────────────────────────────────────────────────────────
.PHONY: all
ifdef NATIVE
all: fetch update docs
else
all: build fetch update docs
endif

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
	  podman build -t $(CONTAINER) -f ../container/Containerfile ../container; \
	else \
	  echo "==> Container image is up to date, skipping build."; \
	fi

# ── 1. Fetch all publications from InspireHEP ─────────────────────────────────
.PHONY: fetch
fetch:
	@echo "==> Fetching all publications from InspireHEP..."
	$(EXEC) python3 fetch_publications.py

# ── 2. Sync sub-lists (interactive for uncategorized entries) ─────────────────
.PHONY: update
update:
	@echo "==> Syncing sub-lists against complete_publication_list.json..."
	$(EXEC_IT) python3 update_lists.py

# ── 3. Generate all PDFs and Markdown files ───────────────────────────────────
.PHONY: docs .FORCE
docs: $(PDFS) $(BIBS)

# .FORCE ensures PDFs always rebuild so the embedded date stays current.
%_publication_list.pdf: %_publication_list.json make_pdf.py .FORCE
	@echo "==> Generating $@..."
	$(EXEC) python3 make_pdf.py $< $@

%_publication_list.bib: %_publication_list.json make_bib.py .FORCE
	@echo "==> Generating $@..."
	$(EXEC) python3 make_bib.py $< $@

# ── Convenience targets ───────────────────────────────────────────────────────
.PHONY: fetch-update
fetch-update: fetch update

.PHONY: clean
clean:
	@echo "==> Removing generated PDFs and Markdown files..."
	$(EXEC) bash -c 'rm -f $(PDFS) $(MARKDOWNS) $(BIBS)'

.PHONY: status
status:
	@echo "==> Record counts:"
	$(EXEC) python3 -c "\
import json, glob; \
files = sorted(glob.glob('*publication_list.json')); \
[print(f'  {f}: {json.load(open(f))[\"total\"]}') for f in files]"

.PHONY: help
help:
	@echo "Targets:"
	@echo "  all          build + fetch + update + docs (full workflow)"
	@echo "  build        build the container image"
	@echo "  fetch        query InspireHEP, update complete_publication_list.json"
	@echo "  update       sync sub-lists (interactive for new uncategorized entries)"
	@echo "  docs         regenerate all PDFs, Markdown, and BibTeX files"
	@echo "  fetch-update fetch then update (no docs)"
	@echo "  status       show record counts for all JSON files"
	@echo "  clean        remove all generated PDFs, Markdown, and BibTeX files"
