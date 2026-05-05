import json
import re
import sys
from datetime import date
import xml.etree.ElementTree as ET
from pylatexenc.latex2text import LatexNodes2Text
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as pdfcanvas

TODAY = date.today().strftime("%B %d, %Y")

INPUT_FILES = ["complete_publication_list.json"]
OUTPUT_FILE = "publication_list.pdf"
MAX_AUTHORS = 10

DEJAVU = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
DEJAVU_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
DEJAVU_MATH = "/usr/share/fonts/truetype/dejavu/DejaVuMathTeXGyre.ttf"

# Unicode characters that can appear raw inside LaTeX math blocks,
# mapped to their LaTeX equivalents so pylatexenc can process them.
UNICODE_IN_MATH = {
    'α': r'\alpha', 'β': r'\beta', 'γ': r'\gamma', 'δ': r'\delta',
    'ε': r'\epsilon', 'ζ': r'\zeta', 'η': r'\eta', 'θ': r'\theta',
    'ι': r'\iota', 'κ': r'\kappa', 'λ': r'\lambda', 'μ': r'\mu',
    'ν': r'\nu', 'ξ': r'\xi', 'π': r'\pi', 'ρ': r'\rho',
    'σ': r'\sigma', 'τ': r'\tau', 'υ': r'\upsilon', 'φ': r'\phi',
    'χ': r'\chi', 'ψ': r'\psi', 'ω': r'\omega',
    'Γ': r'\Gamma', 'Δ': r'\Delta', 'Θ': r'\Theta', 'Λ': r'\Lambda',
    'Ξ': r'\Xi', 'Π': r'\Pi', 'Σ': r'\Sigma', 'Υ': r'\Upsilon',
    'Φ': r'\Phi', 'Ψ': r'\Psi', 'Ω': r'\Omega',
    '→': r'\to', '←': r'\leftarrow', '↔': r'\leftrightarrow',
    '±': r'\pm', '∓': r'\mp', '×': r'\times', '÷': r'\div',
    '∞': r'\infty', '∂': r'\partial', '∇': r'\nabla',
    '≤': r'\leq', '≥': r'\geq', '≠': r'\neq', '≈': r'\approx',
    '∈': r'\in', '∉': r'\notin', '⊂': r'\subset', '⊃': r'\supset',
    '∑': r'\sum', '∏': r'\prod', '∫': r'\int',
    '√': r'\sqrt{}',
}

_converter = LatexNodes2Text()


def mathml_to_text(mathml_str):
    """Convert a MathML string to plain Unicode text."""
    try:
        root = ET.fromstring(mathml_str)
    except ET.ParseError:
        return mathml_str  # fallback: return as-is

    def node_to_text(el):
        tag = el.tag.split("}")[-1]  # strip namespace
        children = list(el)
        text = (el.text or "").strip()

        if tag == "math":
            return "".join(node_to_text(c) for c in children)
        elif tag == "msqrt":
            inner = "".join(node_to_text(c) for c in children)
            return f"\u221a({inner})"   # √(...)
        elif tag == "mroot":
            base = node_to_text(children[0]) if len(children) > 0 else ""
            idx  = node_to_text(children[1]) if len(children) > 1 else ""
            return f"{idx}\u221a({base})"
        elif tag == "mfrac":
            num = node_to_text(children[0]) if len(children) > 0 else ""
            den = node_to_text(children[1]) if len(children) > 1 else ""
            return f"({num}/{den})"
        elif tag == "msub":
            base = node_to_text(children[0]) if len(children) > 0 else ""
            sub  = node_to_text(children[1]) if len(children) > 1 else ""
            return f"{base}_{sub}"
        elif tag == "msup":
            base = node_to_text(children[0]) if len(children) > 0 else ""
            sup  = node_to_text(children[1]) if len(children) > 1 else ""
            return f"{base}^{sup}"
        elif tag == "msubsup":
            base = node_to_text(children[0]) if len(children) > 0 else ""
            sub  = node_to_text(children[1]) if len(children) > 1 else ""
            sup  = node_to_text(children[2]) if len(children) > 2 else ""
            return f"{base}_{sub}^{sup}"
        elif tag in ("mrow", "mstyle", "mpadded", "mphantom"):
            return "".join(node_to_text(c) for c in children)
        elif tag == "mtext":
            # skip thin/hairspace unicode separators
            return "".join(c for c in text if ord(c) > 32)
        elif tag in ("mi", "mn", "mo", "ms"):
            return text
        elif tag == "mspace":
            return " "
        else:
            # unknown tag: recurse into children + include text
            return text + "".join(node_to_text(c) for c in children)

    return node_to_text(root)


def replace_mathml(text):
    """Replace all <math>...</math> blocks in a string with plain text."""
    def replacer(match):
        return mathml_to_text(match.group(0))
    return re.sub(r'<math\b[^>]*>.*?</math>', replacer, text, flags=re.DOTALL)


def normalize_math_block(content):
    """Replace bare Unicode chars with LaTeX equivalents inside a math block."""
    for char, latex in UNICODE_IN_MATH.items():
        content = content.replace(char, latex)
    return content


def latex_to_unicode(text):
    """Convert a title string (LaTeX or MathML) to plain Unicode."""
    # Handle MathML blocks first
    text = replace_mathml(text)

    def replace_math(match):
        inner = normalize_math_block(match.group(1))
        try:
            return _converter.latex_to_text('$' + inner + '$')
        except Exception:
            return match.group(0)  # leave unchanged on failure

    # Handle $...$
    text = re.sub(r'\$(.+?)\$', replace_math, text)
    # Convert any remaining LaTeX outside math (e.g. \sqrt, \ell outside $)
    try:
        text = _converter.latex_to_text(text)
    except Exception:
        pass
    return text


def xml_escape(text):
    """Escape characters that would break ReportLab's XML-like parser."""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;'))


def xml_unescape(text):
    """Reverse XML escaping for plain-text output."""
    return (text
            .replace('&amp;', '&')
            .replace('&lt;', '<')
            .replace('&gt;', '>'))


def format_authors(first_author):
    if not first_author:
        return "Unknown authors"
    name = first_author.get("full_name", "")
    return f"{name} et al." if name else "Unknown authors"


def format_journal(pub_info):
    if not pub_info:
        return None
    entry = next((p for p in pub_info if p.get("material") == "publication"), pub_info[0])
    parts = []
    if entry.get("journal_title"):
        parts.append(entry["journal_title"])
    if entry.get("journal_volume"):
        parts.append(entry["journal_volume"])
    if entry.get("year"):
        parts.append(f"({entry['year']})")
    if entry.get("artid"):
        parts.append(entry["artid"])
    elif entry.get("page_start"):
        parts.append(entry["page_start"])
    return " ".join(parts) if parts else None


def extract_sort_date(meta):
    """Return the best available ISO date string for sorting."""
    date = meta.get("earliest_date", "")
    if len(date) == 4:  # year only — try to get month/day from cnum
        pub_info = meta.get("publication_info") or []
        for p in pub_info:
            m = re.match(r'C(\d{2})-(\d{2})-(\d{2})', p.get("cnum", ""))
            if m:
                yy, mm, dd = m.groups()
                year = "20" + yy if int(yy) < 50 else "19" + yy
                return f"{year}-{mm}-{dd}"
        return date + "-07-01"  # mid-year fallback
    return date


def format_entry(meta):
    title_list = meta.get("titles", [])
    raw_title = title_list[0].get("title", "Untitled") if title_list else "Untitled"
    title = xml_escape(latex_to_unicode(raw_title))

    authors = xml_escape(format_authors(meta.get("first_author")))
    date = meta.get("earliest_date", "")
    journal = format_journal(meta.get("publication_info"))

    arxiv_list = meta.get("arxiv_eprints", [])
    arxiv = arxiv_list[0].get("value") if arxiv_list else None

    doi_list = meta.get("dois", [])
    doi = next(
        (d["value"] for d in doi_list if d.get("material") == "publication"),
        doi_list[0]["value"] if doi_list else None,
    )

    return {
        "date": date,
        "title": title,
        "authors": authors,
        "journal": journal,
        "arxiv": arxiv,
        "doi": doi,
        "_meta": meta,  # kept for sort key only, not rendered
    }


PDF_TITLES = {
    "experiment_publication_list.json":         "Physics Publications with Major Personal Contributions",
    "physics_publication_list.json":            "Physics Publications with Major Personal Contributions",
    "computing_publication_list.json":          "Computing Publications with Major Personal Contributions",
    "short_physics_publication_list.json":      "Physics Publications with Major Personal Contributions",
    "short_computing_publication_list.json":    "Computing Publications with Major Personal Contributions",
    "shortest_physics_publication_list.json":   "Physics Publications with Major Personal Contributions",
    "shortest_computing_publication_list.json": "Computing Publications with Major Personal Contributions",
    "complete_publication_list.json":           "Complete Publication List",
}


def register_fonts():
    pdfmetrics.registerFont(TTFont("DejaVu", DEJAVU))
    pdfmetrics.registerFont(TTFont("DejaVu-Bold", DEJAVU_BOLD))
    pdfmetrics.registerFont(TTFont("DejaVuMath", DEJAVU_MATH))


class FooterCanvas(pdfcanvas.Canvas):
    """Canvas that adds a footer with date (left) and page X of Y (right)."""

    def __init__(self, *args, **kwargs):
        pdfcanvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_footer(total)
            pdfcanvas.Canvas.showPage(self)
        pdfcanvas.Canvas.save(self)

    def _draw_footer(self, total):
        self.saveState()
        self.setFont("DejaVu", 8)
        self.setFillColor(colors.HexColor("#777777"))
        y = 0.75 * cm
        self.drawString(2 * cm, y, TODAY)
        self.drawRightString(A4[0] - 2 * cm, y, f"Page {self._pageNumber} of {total}")
        self.restoreState()


def build_md(entries, output_file):
    lines = []
    for i, entry in enumerate(entries, 1):
        title   = xml_unescape(entry["title"])
        authors = xml_unescape(entry["authors"])
        lines.append(f"{i}. **{title}**  ")
        lines.append(f"   {authors}  ")

        detail_parts = []
        if entry["journal"] and entry["doi"]:
            detail_parts.append(f"[{entry['journal']}](https://doi.org/{entry['doi']})")
        elif entry["journal"]:
            detail_parts.append(entry["journal"])
        if entry["arxiv"]:
            detail_parts.append(f"[arXiv:{entry['arxiv']}](https://arxiv.org/abs/{entry['arxiv']})")
        if entry["doi"]:
            detail_parts.append(f"[DOI:{entry['doi']}](https://doi.org/{entry['doi']})")
        if entry["date"]:
            detail_parts.append(entry["date"])

        lines.append(f"   {' | '.join(detail_parts)}")
        lines.append("")

    with open(output_file, "w") as f:
        f.write("\n".join(lines))


def build_pdf(records, output_file=OUTPUT_FILE, pdf_title="Publication List"):
    register_fonts()

    doc = SimpleDocTemplate(
        output_file,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    header_style = ParagraphStyle(
        "Header",
        parent=styles["Heading1"],
        fontName="DejaVu-Bold",
        fontSize=16,
        spaceAfter=4,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#1a1a6e"),
    )
    centered_style = ParagraphStyle(
        "Centered",
        parent=styles["Normal"],
        fontName="DejaVu",
        fontSize=12,
        spaceAfter=4,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#333333"),
    )
    title_style = ParagraphStyle(
        "EntryTitle",
        parent=styles["Normal"],
        fontName="DejaVuMath",
        fontSize=10,
        leading=14,
        spaceAfter=2,
        textColor=colors.HexColor("#1a1a6e"),
    )
    meta_style = ParagraphStyle(
        "EntryMeta",
        parent=styles["Normal"],
        fontName="DejaVu",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#333333"),
    )

    story = []
    story.append(Paragraph(pdf_title, header_style))
    story.append(Paragraph("Oliver Gutsche", centered_style))
    story.append(Paragraph(TODAY, centered_style))
    story.append(Spacer(1, 16))

    for i, entry in enumerate(records, 1):
        story.append(Paragraph(f"{i}. {entry['title']}", title_style))
        story.append(Paragraph(entry["authors"], meta_style))

        detail_parts = []
        if entry["journal"] and entry["doi"]:
            detail_parts.append(f'<a href="https://doi.org/{entry["doi"]}" color="#0645ad">{entry["journal"]}</a>')
        elif entry["journal"]:
            detail_parts.append(entry["journal"])
        if entry["arxiv"]:
            detail_parts.append(f'<a href="https://arxiv.org/abs/{entry["arxiv"]}" color="#0645ad">arXiv:{entry["arxiv"]}</a>')
        if entry["doi"]:
            detail_parts.append(f'<a href="https://doi.org/{entry["doi"]}" color="#0645ad">DOI:{entry["doi"]}</a>')
        if entry["date"]:
            detail_parts.append(entry["date"])

        story.append(Paragraph(" | ".join(detail_parts), meta_style))
        story.append(Spacer(1, 8))

    doc.build(story, canvasmaker=FooterCanvas)


def main():
    # Allow: make_pdf.py input1.json [input2.json ...] output.pdf
    args = sys.argv[1:]
    if args:
        input_files = [a for a in args if a.endswith(".json")]
        out = next((a for a in args if a.endswith(".pdf")), None)
        output_file = out if out else OUTPUT_FILE
    else:
        input_files = INPUT_FILES
        output_file = OUTPUT_FILE

    records_raw = []
    for input_file in input_files:
        with open(input_file) as f:
            data = json.load(f)
        records_raw.extend(data.get("records", []))
        print(f"Loaded {len(data.get('records', []))} records from {input_file}")

    entries = [format_entry(r["metadata"]) for r in records_raw]
    entries.sort(key=lambda e: extract_sort_date(e["_meta"]), reverse=True)

    # Determine title from first input file name
    first_input = input_files[0].split("/")[-1]
    pdf_title = PDF_TITLES.get(first_input, "Publication List")
    print(f"Building PDF and Markdown for {len(entries)} records ...")
    build_pdf(entries, output_file, pdf_title=pdf_title)
    print(f"Saved to {output_file}")
    md_file = output_file.replace(".pdf", ".md")
    build_md(entries, md_file)
    print(f"Saved to {md_file}")


if __name__ == "__main__":
    main()
