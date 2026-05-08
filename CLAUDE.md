# CLAUDE.md — ForThePublic Repository

## Overview

This repository manages the public online presence of Oliver Gutsche, Senior Scientist at Fermilab. It contains a Hugo-based academic website, publication management scripts, CV generation, talk/media lists, and supporting tooling.

---

## Repository Structure

```
ForThePublic/
├── academic-webpage/        Hugo site (primary public website, hosted on Netlify)
├── personal-webpage/        Older legacy Hugo site (unused/archived)
├── publication_list/        Publication management system (new Python-based version)
├── talk_list/               Talk/presentation list management (Pandoc + BibTeX)
├── media_list/              Media mentions/press coverage (Pandoc + BibTeX)
├── cv/                      CV and resume generation (Pandoc + LaTeX + M4)
├── profile/                 LinkedIn profile generation
└── other/                   Testing/scratch files
```

---

## Website: academic-webpage/

**Technology:** Hugo static site generator with the Academic/Wowchemy theme  
**Hosting:** Netlify (auto-deploys on push to GitHub)  
**Base URL:** https://gutsche.github.io/  
**Hugo version:** 0.75.1 (pinned in netlify.toml)  
**Build command:** `hugo --gc --minify`

### Key content files:
- `content/home/` — Homepage sections
- `content/physics_pubs/physics_pubs.md` — Physics publications page (hardcoded highlights + links to PDFs)
- `content/computing_pubs/computing_pubs.md` — Computing publications page (hardcoded highlights + links to PDFs)
- `content/cv/cv.md` — CV page
- `content/resume/resume.md` — Resume page
- `content/talks/` — Talks section
- `content/authors/gutsche/_index.md` — Author profile

### How publication lists are integrated into the website:
- Selected papers are **hardcoded as markdown** in `physics_pubs.md` and `computing_pubs.md`
- Full lists are linked via **GitHub raw URLs**, e.g.:
  ```
  https://github.com/gutsche/ForThePublic/raw/master/publication_list/physics_publication_list.pdf
  ```
- The "published on" date is manually maintained in each content file

---

## Publication List System: publication_list/

**This is the "new version" rewritten in Python (replacing the older Pandoc/BibTeX approach).**

### Technology:
- Python 3.12 (containerized via Podman using `Containerfile`)
- InspireHEP REST API as the source of truth
- ReportLab for PDF generation
- bibtexparser + pylatexenc for BibTeX/LaTeX handling

### Workflow (Makefile targets):
| Target | Action |
|--------|--------|
| `make build` | Build the container image |
| `make fetch` | Query InspireHEP API, update `complete_publication_list.json` |
| `make update` | Sync sub-lists; interactively categorize new publications |
| `make docs` | Generate all PDFs and Markdown files from JSON |
| `make fetch-update` | fetch + update (skip PDF generation) |
| `make status` | Show record counts per list |
| `make clean` | Remove generated PDFs/Markdown |

### Key scripts:
| Script | Purpose |
|--------|---------|
| `fetch_publications.py` | Queries InspireHEP for author "O.Gutsche.1" |
| `update_lists.py` | Syncs sub-lists, removes deleted records, interactively categorizes new ones |
| `make_pdf.py` | Generates PDF and Markdown from JSON (using ReportLab, LaTeX→Unicode) |
| `bib_to_json.py` | (Legacy) BibTeX → InspireHEP JSON conversion |
| `extract_computing.py` | (Legacy) Match BibTeX against complete list |

### Publication lists maintained:

| List | Description |
|------|-------------|
| `complete_publication_list` | All publications (~6000+) |
| `experiment_publication_list` | Experiment collaboration papers (~5000+) |
| `physics_publication_list` | Physics papers with personal contributions (~130) |
| `computing_publication_list` | Computing/software papers (~120) |
| `short_physics_publication_list` | Selected highlights — physics |
| `short_computing_publication_list` | Selected highlights — computing |
| `shortest_physics_publication_list` | 2–5 key physics papers |
| `shortest_computing_publication_list` | 2–5 key computing papers |

Each list exists as `.json` (data), `.pdf` (formatted), and `.md` (markdown) versions.

### JSON format (InspireHEP-derived):
```json
{
  "author": "O.Gutsche.1",
  "total": <count>,
  "fetched": <count>,
  "records": [
    {
      "id": <num>,
      "metadata": {
        "first_author": {...},
        "titles": [...],
        "earliest_date": "YYYY-MM-DD",
        "publication_info": [...],
        "dois": [...],
        "arxiv_eprints": [...]
      }
    }
  ]
}
```

### What doesn't yet fit together:
The new `publication_list/` Python system generates `.md` and `.pdf` files but they are **not yet wired into** the `academic-webpage/` Hugo site. The website content files (`physics_pubs.md`, `computing_pubs.md`, `cv.md`, `resume.md`) still contain hardcoded publication snippets and manual GitHub raw URL links. Integration needs to be established.

---

## Other Subsystems

### talk_list/
- Pandoc + BibTeX → PDF and Markdown
- M4 templating for dynamic content
- Makefile-based build

### media_list/
- Same structure as talk_list
- Tracks press coverage/media mentions

### cv/
- Pandoc + LaTeX + M4 templating
- Outputs: `cv.pdf`, `resume.pdf`, `accomplishments.pdf`
- Sources are markdown fragments assembled by Makefile

### profile/
- LinkedIn profile generation
- Markdown → HTML/PDF via Pandoc

---

## Technology Stack Summary

| Tool | Role |
|------|------|
| Hugo 0.75.1 | Static site generator |
| Netlify | Hosting and CI/CD |
| Python 3.12 | Publication list scripts |
| InspireHEP API | Publication metadata source |
| Podman | Container runtime for reproducible builds |
| ReportLab | PDF generation (publication lists) |
| Pandoc | Markdown/BibTeX → PDF (CV, talks, media) |
| M4 | Template processing |
| bibtexparser | BibTeX parsing |
| pylatexenc | LaTeX → Unicode conversion |
| Git / GitHub | Version control; PDFs served via raw GitHub URLs |

---

## Git Conventions

- When creating git commit messages, do not mention that they were written by Claude or any AI tool. No `Co-Authored-By` trailers.

---

## Open Integration Work

The main gap: the `publication_list/` folder's new Python-based system generates clean `.md` and `.pdf` files, but the academic website (`academic-webpage/`) still references old hardcoded content and manually maintained links. Connecting them would involve:

1. Determining whether to embed or link Markdown output in Hugo content
2. Updating `physics_pubs.md` and `computing_pubs.md` to reference new outputs
3. Updating `cv.md` and `resume.md` similarly
4. Potentially automating the "published on" date
5. Ensuring the Makefile (or a wrapper at repo root) can rebuild everything end-to-end
