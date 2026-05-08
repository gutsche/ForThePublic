CONTAINER = ubuntu-dev

# Pass NATIVE=1 when tools are already available in PATH (e.g. inside the
# container launched by the root makefile). In that case the podman wrapper
# is skipped and commands run directly.
ifdef NATIVE
  EXEC =
else
  EXEC = podman run --rm -v $(PWD):$(PWD) -w $(PWD) $(CONTAINER)
endif

LISTS     = talk_list short_talk_list
PDFS      = $(addsuffix .pdf, $(LISTS))
MARKDOWNS = $(addsuffix .md,  $(LISTS))
BIBS      = $(addsuffix .bib, $(LISTS))
JSONS     = $(addsuffix .json, $(LISTS))

# ── Default target ────────────────────────────────────────────────────────────
.PHONY: all
all: docs

# ── Generate all PDFs, Markdown, and BibTeX files ────────────────────────────
.PHONY: docs .FORCE
docs: $(PDFS) $(BIBS)

# .FORCE ensures outputs always rebuild so the embedded date stays current.
%.pdf: %.json make_pdf.py .FORCE
	@echo "==> Generating $@..."
	$(EXEC) python3 make_pdf.py $< $@

%.bib: %.json make_bib.py .FORCE
	@echo "==> Generating $@..."
	$(EXEC) python3 make_bib.py $< $@

# ── Utilities ─────────────────────────────────────────────────────────────────
.PHONY: status
status:
	@echo "==> Record counts:"
	@python3 -c "\
import json, glob; \
files = sorted(glob.glob('*.json')); \
[print(f'  {f}: {json.load(open(f))[\"total\"]}') for f in files]"

.PHONY: clean
clean:
	@echo "==> Removing generated PDFs, Markdown, and BibTeX files..."
	rm -f $(PDFS) $(MARKDOWNS) $(BIBS)

.PHONY: help
help:
	@echo "Targets:"
	@echo "  all      regenerate all PDFs, Markdown, and BibTeX files (default)"
	@echo "  docs     same as all"
	@echo "  status   show record counts for all JSON files"
	@echo "  clean    remove all generated PDFs, Markdown, and BibTeX files"
