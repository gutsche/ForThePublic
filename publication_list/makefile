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
	@podman image exists $(CONTAINER) \
	  && echo "==> Container image already exists, skipping build." \
	  || (echo "==> Building container image..." && podman build -t $(CONTAINER) -f Containerfile .)

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
docs: $(PDFS)

# .FORCE ensures PDFs always rebuild so the embedded date stays current.
%_publication_list.pdf: %_publication_list.json make_pdf.py .FORCE
	@echo "==> Generating $@..."
	$(EXEC) python3 make_pdf.py $< $@

# ── Convenience targets ───────────────────────────────────────────────────────
.PHONY: fetch-update
fetch-update: fetch update

.PHONY: clean
clean:
	@echo "==> Removing generated PDFs and Markdown files..."
	$(EXEC) bash -c 'rm -f $(PDFS) $(MARKDOWNS)'

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
	@echo "  docs         regenerate all PDFs and Markdown files"
	@echo "  fetch-update fetch then update (no docs)"
	@echo "  status       show record counts for all JSON files"
	@echo "  clean        remove all generated PDFs and Markdown files"
