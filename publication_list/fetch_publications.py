import requests
import json
import time

BASE_URL = "https://inspirehep.net/api/literature"
AUTHOR = "O.Gutsche.1"
OUTPUT_FILE = "complete_publication_list.json"
PAGE_SIZE = 200
MAX_ENTRIES = None  # fetch all
MAX_RETRIES = 5


HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; publication-fetcher/1.0)",
    "Accept": "application/json",
}


def fetch_page(params, retries=MAX_RETRIES):
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if attempt == retries:
                raise
            wait = 2 ** attempt
            print(f"error ({e}), retrying in {wait}s ...", end=" ", flush=True)
            time.sleep(wait)


def fetch_all_publications():
    pages = []
    page = 1
    total = None

    params = {
        "q": f"a {AUTHOR}",
        "size": PAGE_SIZE,
        "page": page,
        "sort": "mostrecent",
        "fields": "titles,first_author,earliest_date,publication_info,arxiv_eprints,dois",
    }

    print(f"Querying InspireHEP for author: {AUTHOR}")

    while True:
        params["page"] = page
        print(f"  Fetching page {page} ...", end=" ", flush=True)

        data = fetch_page(params)
        hits = data.get("hits", {})
        total = hits.get("total", 0)
        records = hits.get("hits", [])

        print(f"got {len(records)} records (total: {total})")
        pages.append(records)

        fetched = sum(len(p) for p in pages)
        if (MAX_ENTRIES and fetched >= MAX_ENTRIES) or fetched >= total or not records:
            break

        page += 1
        time.sleep(0.5)  # be polite to the API

    return pages, total


def main():
    pages, total = fetch_all_publications()

    # concatenate all pages into a single list, capped at MAX_ENTRIES
    all_records = [r for page in pages for r in page]
    if MAX_ENTRIES:
        all_records = all_records[:MAX_ENTRIES]

    output = {
        "author": AUTHOR,
        "total": total,
        "fetched": len(all_records),
        "records": all_records,
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nDone. {len(all_records)}/{total} records saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
