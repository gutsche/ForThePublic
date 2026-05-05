#!/usr/bin/env python3
"""Sync experiment/physics/computing JSON lists against the updated complete list.

Steps:
  1. Remove entries from sub-lists that are no longer in complete.
  2. Refresh metadata for remaining entries from the new complete.
  3. Interactively assign new uncategorized entries to sub-lists.
  4. Re-derive short/shortest lists from their bib files.
"""

import glob
import json
import os
import sys

import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode

COMPLETE_FILE = "complete_publication_list.json"
MAIN_LISTS = [
    "experiment_publication_list.json",
    "physics_publication_list.json",
    "computing_publication_list.json",
]
BIB_DIR = "bib"
# Bib files whose JSON outputs are re-derived automatically (not interactively managed)
BIB_DERIVED = {
    "short_computing_publication_list.bib",
    "short_physics_publication_list.bib",
    "shortest_computing_publication_list.bib",
    "shortest_physics_publication_list.bib",
}


def load_json(path):
    with open(path) as f:
        return json.load(f)


def save_json(data, path):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    data["total"] = data["fetched"] = len(data["records"])


def ask(prompt):
    try:
        return input(prompt).strip().lower()
    except EOFError:
        return "n"


# ── Step 1 & 2: sync main sub-lists ──────────────────────────────────────────

def sync_main_lists(complete_index):
    all_categorized = set()
    print("\n── Syncing main sub-lists ──")
    for list_file in MAIN_LISTS:
        data = load_json(list_file)
        before = len(data["records"])

        updated = []
        removed = []
        for rec in data["records"]:
            rid = rec.get("id") or rec.get("metadata", {}).get("control_number", "")
            rid = str(rid)
            if rid in complete_index:
                updated.append(complete_index[rid])   # refresh with latest data
            else:
                removed.append(rid)

        data["records"] = updated
        data["total"] = data["fetched"] = len(updated)
        save_json(data, list_file)
        all_categorized |= {str(r.get("id", "")) for r in updated}

        msg = f"  {list_file}: {before} → {len(updated)}"
        if removed:
            msg += f"  (removed {len(removed)}: {removed})"
        print(msg)

    return all_categorized


# ── Step 3: interactive assignment of uncategorized entries ───────────────────

def assign_uncategorized(complete, all_categorized):
    uncategorized = [
        r for r in complete["records"]
        if str(r.get("id", "")) not in all_categorized
    ]
    uncategorized.sort(
        key=lambda r: r["metadata"].get("earliest_date", ""), reverse=True
    )

    if not uncategorized:
        print("\nNo uncategorized entries — all good.")
        return

    print(f"\n── {len(uncategorized)} entries not in any sub-list ──")
    lists = {f: load_json(f) for f in MAIN_LISTS}

    for rec in uncategorized:
        meta = rec["metadata"]
        title = meta.get("titles", [{}])[0].get("title", "No title")
        date  = meta.get("earliest_date", "unknown")
        print(f"\n  [{date}] {title[:90]}")

        added_to = []
        for list_file in MAIN_LISTS:
            name = list_file.replace("_publication_list.json", "")
            ans = ask(f"    Add to {name}? [y/N] ")
            if ans == "y":
                lists[list_file]["records"].append(rec)
                added_to.append(name)

        if added_to:
            print(f"    → Added to: {', '.join(added_to)}")
        else:
            print("    → Skipped")

    for list_file, data in lists.items():
        data["total"] = data["fetched"] = len(data["records"])
        save_json(data, list_file)


# ── Step 4: re-derive short/shortest lists from bib files ────────────────────

def rederive_bib_lists(complete):
    doi_index, arxiv_index = {}, {}
    for rec in complete["records"]:
        meta = rec["metadata"]
        for d in (meta.get("dois") or []):
            doi_index[d["value"].strip().lower()] = rec
        for a in (meta.get("arxiv_eprints") or []):
            arxiv_index[a["value"].strip().lower()] = rec

    print("\n── Re-deriving bib-based short/shortest lists ──")
    bib_files = sorted(
        f for f in glob.glob(os.path.join(BIB_DIR, "*.bib"))
        if os.path.basename(f) in BIB_DERIVED
    )

    for bib_file in bib_files:
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
            "author":  complete["author"],
            "source":  bib_file,
            "total":   len(matched),
            "fetched": len(matched),
            "records": matched,
        }
        save_json(output, output_file)

        status = f"Matched {len(matched)}/{len(bib.entries)}"
        if unmatched:
            status += f"  WARNING unmatched: {unmatched}"
        print(f"  {output_file}: {status}")


# ── Cross-check ───────────────────────────────────────────────────────────────

def crosscheck(complete):
    complete_ids = {str(r.get("id", "")) for r in complete["records"]}
    covered = set()
    for f in MAIN_LISTS:
        data = load_json(f)
        covered |= {str(r.get("id", "")) for r in data["records"]}

    missing = len(complete_ids - covered)
    print(f"\n── Cross-check ──")
    for f in MAIN_LISTS:
        data = load_json(f)
        print(f"  {f}: {data['total']}")
    print(f"  complete: {complete['total']}")
    print(f"  union covers complete: {'YES' if missing == 0 else f'NO — {missing} uncategorized'}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"Loading {COMPLETE_FILE} ...")
    complete = load_json(COMPLETE_FILE)
    complete_index = {str(r.get("id", "")): r for r in complete["records"]}
    print(f"  {len(complete_index)} records")

    all_categorized = sync_main_lists(complete_index)
    assign_uncategorized(complete, all_categorized)
    rederive_bib_lists(complete)
    crosscheck(complete)
    print("\nDone.")


if __name__ == "__main__":
    main()
