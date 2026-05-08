#!/usr/bin/env python3
"""Generate BibTeX files from InspireHEP JSON publication lists."""

import json
import re
import sys
from datetime import date
from pathlib import Path

TODAY = date.today().strftime("%Y-%m-%d")


def _get_title(metadata):
    titles = metadata.get("titles", [])
    for t in titles:
        if t.get("source", "") != "arXiv":
            return t.get("title", "")
    return titles[0].get("title", "") if titles else ""


def _get_pub_info(metadata):
    for p in metadata.get("publication_info", []):
        if p.get("material") == "publication":
            return p
    infos = metadata.get("publication_info", [])
    return infos[0] if infos else {}


def _get_doi(metadata):
    for d in metadata.get("dois", []):
        if d.get("material") == "publication":
            return d.get("value", "")
    dois = metadata.get("dois", [])
    return dois[0].get("value", "") if dois else ""


def _get_arxiv(metadata):
    eprints = metadata.get("arxiv_eprints", [])
    if eprints:
        ep = eprints[0]
        return ep.get("value", ""), ep.get("categories", [""])[0]
    return "", ""


def _cite_key(record):
    metadata = record.get("metadata", {})
    first_author = metadata.get("first_author", {})
    last = re.sub(r"[^a-zA-Z]", "", first_author.get("last_name", "Unknown"))
    year = (metadata.get("earliest_date", "") or "0000")[:4]
    record_id = record.get("id", "0")
    return f"{last}:{year}_{record_id}"


def _format_author(metadata):
    fa = metadata.get("first_author", {})
    last = fa.get("last_name", "")
    first = fa.get("first_name", "")
    if last and first:
        return f"{last}, {first} and others"
    return f"{last} and others" if last else "others"


def record_to_bibtex(record):
    metadata = record.get("metadata", {})
    key = _cite_key(record)
    title = _get_title(metadata)
    author = _format_author(metadata)
    year = (metadata.get("earliest_date", "") or "")[:4]
    pub = _get_pub_info(metadata)
    doi = _get_doi(metadata)
    eprint, primary_class = _get_arxiv(metadata)

    journal = pub.get("journal_title", "")
    volume = pub.get("journal_volume", "")
    number = pub.get("journal_issue", "")
    artid = pub.get("artid", "")
    page_start = pub.get("page_start", "")
    page_end = pub.get("page_end", "")

    if artid:
        pages = artid
    elif page_start and page_end:
        pages = f"{page_start}--{page_end}"
    elif page_start:
        pages = page_start
    else:
        pages = ""

    entry_type = "article" if (journal or eprint) else "misc"

    fields = [
        f"  author         = {{{author}}}",
        f"  title          = {{{{{title}}}}}",
    ]
    if year:
        fields.append(f"  year           = {{{year}}}")
    if journal:
        fields.append(f"  journal        = {{{journal}}}")
    if volume:
        fields.append(f"  volume         = {{{volume}}}")
    if number:
        fields.append(f"  number         = {{{number}}}")
    if pages:
        fields.append(f"  pages          = {{{pages}}}")
    if doi:
        fields.append(f"  doi            = {{{doi}}}")
    if eprint:
        fields.append(f"  eprint         = {{{eprint}}}")
        fields.append(f"  archivePrefix  = {{arXiv}}")
        if primary_class:
            fields.append(f"  primaryClass   = {{{primary_class}}}")

    body = ",\n".join(fields)
    return f"@{entry_type}{{{key},\n{body}\n}}"


def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <input.json> <output.bib>")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    records = sorted(
        data.get("records", []),
        key=lambda r: r.get("metadata", {}).get("earliest_date", "") or "",
        reverse=True,
    )

    entries = [record_to_bibtex(r) for r in records]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"% Generated from {input_path.name} on {TODAY}\n")
        f.write(f"% Total entries: {len(entries)}\n\n")
        f.write("\n\n".join(entries))
        f.write("\n")

    print(f"Generated {len(entries)} BibTeX entries → {output_path}")


if __name__ == "__main__":
    main()
