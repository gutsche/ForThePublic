"""Match all .bib files in the bib/ directory against complete_publication_list.json
and store the matched records as corresponding .json files in the main directory."""

import json
import glob
import os
import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode

BIB_DIR   = "bib"
JSON_FILE = "complete_publication_list.json"


def build_indexes(data):
    doi_index, arxiv_index = {}, {}
    for rec in data["records"]:
        meta = rec["metadata"]
        for d in (meta.get("dois") or []):
            doi_index[d["value"].strip().lower()] = rec
        for a in (meta.get("arxiv_eprints") or []):
            arxiv_index[a["value"].strip().lower()] = rec
    return doi_index, arxiv_index


def process_bib(bib_file, doi_index, arxiv_index, author):
    parser = BibTexParser(common_strings=True)
    parser.customization = convert_to_unicode
    with open(bib_file) as f:
        bib = bibtexparser.load(f, parser=parser)

    matched, unmatched = [], []
    for e in bib.entries:
        doi    = e.get("doi",    "").strip().lower()
        eprint = e.get("eprint", "").strip().lower()
        rec = doi_index.get(doi) or arxiv_index.get(eprint)
        if rec:
            matched.append(rec)
        else:
            unmatched.append(e["ID"])

    output_file = os.path.basename(bib_file).replace(".bib", ".json")
    output = {
        "author":  author,
        "source":  bib_file,
        "total":   len(matched),
        "fetched": len(matched),
        "records": matched,
    }
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)

    status = f"Matched {len(matched)}/{len(bib.entries)}"
    if unmatched:
        status += f"  WARNING unmatched: {unmatched}"
    print(f"  {status} → {output_file}")


def main():
    with open(JSON_FILE) as f:
        data = json.load(f)

    doi_index, arxiv_index = build_indexes(data)

    bib_files = sorted(glob.glob(os.path.join(BIB_DIR, "*.bib")))
    print(f"Processing {len(bib_files)} bib files...")
    for bib_file in bib_files:
        process_bib(bib_file, doi_index, arxiv_index, data["author"])


if __name__ == "__main__":
    main()
