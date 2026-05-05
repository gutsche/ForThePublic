"""Convert a BibTeX file to the InspireHEP JSON format used by complete_publication_list.json."""

import json
import re
import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode

INPUT_FILE = "bib/additional_publication_list.bib"
OUTPUT_FILE = "additional_publication_list.json"


def parse_author(raw):
    """Parse 'Last, First' or 'First Last' into a first_author dict."""
    raw = raw.strip()
    if "," in raw:
        last, first = [p.strip() for p in raw.split(",", 1)]
    else:
        parts = raw.split()
        last, first = parts[-1], " ".join(parts[:-1])
    return {
        "full_name": f"{last}, {first}" if first else last,
        "last_name": last,
        "first_name": first,
    }


def bib_entry_to_record(entry):
    """Convert a bibtexparser entry dict to an InspireHEP-style record dict."""
    etype = entry.get("ENTRYTYPE", "article").lower()
    key   = entry.get("ID", "")

    # --- first_author ---
    raw_author = entry.get("author", "")
    # take only the first author (before " and ")
    first_raw = re.split(r"\s+and\s+", raw_author, flags=re.IGNORECASE)[0]
    first_author = parse_author(first_raw)

    # --- title ---
    title = entry.get("title", "").strip("{}")

    # --- date ---
    year = entry.get("year", "").strip()
    month = entry.get("month", "").strip()
    earliest_date = f"{year}-{month.zfill(2)}" if month.isdigit() else year

    # --- DOI ---
    doi_val = entry.get("doi", "").strip()
    dois = [{"value": doi_val}] if doi_val else None

    # --- arXiv ---
    eprint = entry.get("eprint", "").strip()
    arxiv_eprints = [{"value": eprint}] if eprint else None

    # --- publication_info ---
    pub_info = None
    if etype == "article":
        p = {}
        if entry.get("journal"):  p["journal_title"]  = entry["journal"].strip("{}")
        if entry.get("volume"):   p["journal_volume"]  = entry["volume"].strip()
        if entry.get("pages"):    p["page_start"]       = entry["pages"].split("--")[0].strip()
        if year:                  p["year"]             = int(year)
        if entry.get("number"):   p["journal_issue"]    = entry["number"].strip()
        pub_info = [p] if p else None
    elif etype in ("phdthesis", "mastersthesis"):
        label = "PhD Thesis" if etype == "phdthesis" else "Master's Thesis"
        school = entry.get("school", "").strip("{}")
        freetext = f"{school}, {label}" if school else label
        pub_info = [{"pubinfo_freetext": freetext}]
    elif etype == "inproceedings":
        p = {}
        if entry.get("booktitle"): p["pubinfo_freetext"] = entry["booktitle"].strip("{}")
        if year:                   p["year"] = int(year)
        pub_info = [p] if p else None

    # --- report numbers ---
    rep = entry.get("reportnumber", entry.get("reportNumber", "")).strip()
    report_numbers = [{"value": rep}] if rep else None

    # --- document_type ---
    type_map = {
        "article": ["article"],
        "phdthesis": ["thesis"],
        "mastersthesis": ["thesis"],
        "inproceedings": ["conference paper"],
        "proceedings": ["proceedings"],
        "book": ["book"],
        "techreport": ["report"],
    }
    document_type = type_map.get(etype, ["other"])

    metadata = {
        "first_author": first_author,
        "titles": [{"title": title}],
        "earliest_date": earliest_date,
        "document_type": document_type,
    }
    if dois:            metadata["dois"] = dois
    if arxiv_eprints:   metadata["arxiv_eprints"] = arxiv_eprints
    if pub_info:        metadata["publication_info"] = pub_info
    if report_numbers:  metadata["report_numbers"] = report_numbers

    return {
        "id": key,
        "links": {},
        "created": f"{year}-01-01T00:00:00",
        "updated": f"{year}-01-01T00:00:00",
        "metadata": metadata,
    }


def main():
    parser = BibTexParser(common_strings=True)
    parser.customization = convert_to_unicode

    with open(INPUT_FILE) as f:
        bib = bibtexparser.load(f, parser=parser)

    records = [bib_entry_to_record(e) for e in bib.entries]

    output = {
        "author": "O.Gutsche.1",
        "source": INPUT_FILE,
        "total": len(records),
        "fetched": len(records),
        "records": records,
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Converted {len(records)} entries → {OUTPUT_FILE}")
    for r in records:
        print(f"  [{r['metadata']['document_type'][0]}] {r['metadata']['earliest_date']}  {r['metadata']['titles'][0]['title'][:70]}")


if __name__ == "__main__":
    main()
