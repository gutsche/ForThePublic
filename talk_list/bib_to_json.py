#!/usr/bin/env python3
"""Convert talk_list BibTeX files to JSON (one-time migration tool)."""

import json
import sys
from pathlib import Path

import bibtexparser
from bibtexparser.bparser import BibTexParser

MONTH_MAP = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
}


def strip_braces(s):
    s = s.strip()
    while s.startswith('{') and s.endswith('}'):
        s = s[1:-1].strip()
    return s


def parse_month(s):
    s = strip_braces(s).lower().strip()
    try:
        return int(s)
    except ValueError:
        return MONTH_MAP.get(s[:3], 0)


def entry_to_record(entry):
    title = strip_braces(entry.get('title', ''))
    author = strip_braces(entry.get('author', 'Oliver Gutsche'))
    try:
        year = int(strip_braces(entry.get('year', '0')))
    except ValueError:
        year = 0
    month = parse_month(entry.get('month', '0'))
    note = entry.get('note', '')

    return {
        'id': entry['ID'],
        'metadata': {
            'title': title,
            'author': author,
            'year': year,
            'month': month,
            'note': note,
        },
    }


def main():
    if len(sys.argv) < 3:
        print(f'Usage: {sys.argv[0]} <input.bib> <output.json>')
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    parser = BibTexParser(common_strings=True)
    parser.customization = None  # keep raw LaTeX in note field

    with open(input_path, encoding='utf-8') as f:
        bib_db = bibtexparser.load(f, parser=parser)

    records = [entry_to_record(e) for e in bib_db.entries]
    records.sort(
        key=lambda r: (r['metadata']['year'], r['metadata']['month']),
        reverse=True,
    )

    data = {
        'source': str(input_path),
        'total': len(records),
        'records': records,
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f'Converted {len(records)} entries → {output_path}')


if __name__ == '__main__':
    main()
