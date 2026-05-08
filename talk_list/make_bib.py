#!/usr/bin/env python3
"""Generate BibTeX files from JSON talk lists."""

import json
import sys
from datetime import date
from pathlib import Path

TODAY = date.today().strftime('%Y-%m-%d')


def record_to_bibtex(record):
    key = record['id']
    meta = record['metadata']
    title = meta.get('title', '')
    author = meta.get('author', 'Oliver Gutsche')
    year = meta.get('year', 0)
    month = meta.get('month', 0)
    note = meta.get('note', '')

    fields = [
        f'  title          = {{{{{title}}}}}',
        f'  author         = {{{author}}}',
        f'  year           = {{{year}}}',
    ]
    if month:
        fields.append(f'  month          = {{{month}}}')
    if note:
        fields.append(f'  note           = {{{note}}}')

    body = ',\n'.join(fields)
    return f'@misc{{{key},\n{body}\n}}'


def main():
    if len(sys.argv) < 3:
        print(f'Usage: {sys.argv[0]} <input.json> <output.bib>')
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    with open(input_path, encoding='utf-8') as f:
        data = json.load(f)

    records = data.get('records', [])
    entries = [record_to_bibtex(r) for r in records]

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f'% Generated from {input_path.name} on {TODAY}\n')
        f.write(f'% Total entries: {len(entries)}\n\n')
        f.write('\n\n'.join(entries))
        f.write('\n')

    print(f'Generated {len(entries)} BibTeX entries \u2192 {output_path}')


if __name__ == '__main__':
    main()
