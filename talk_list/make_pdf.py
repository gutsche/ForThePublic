#!/usr/bin/env python3
"""Generate PDF and Markdown from JSON talk lists."""

import json
import re
import sys
from datetime import date
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as pdfcanvas

TODAY = date.today().strftime('%B %d, %Y')

DEJAVU = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
DEJAVU_BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

MONTH_NAMES = {
    1: 'January', 2: 'February', 3: 'March', 4: 'April',
    5: 'May', 6: 'June', 7: 'July', 8: 'August',
    9: 'September', 10: 'October', 11: 'November', 12: 'December',
}

PDF_TITLES = {
    'talk_list.json':       'List of Presentations and Talks of Oliver Gutsche',
    'short_talk_list.json': 'Selected Presentations and Talks of Oliver Gutsche',
}


def format_date(year, month):
    if month and month in MONTH_NAMES:
        return f'{MONTH_NAMES[month]} {year}'
    return str(year)


def xml_escape(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def note_to_html(note):
    """Convert LaTeX \\href{url}{text} to ReportLab anchor tags, escaping surrounding text."""
    parts = []
    last = 0
    for m in re.finditer(r'\\href\{([^}]+)\}\{([^}]*)\}', note):
        parts.append(xml_escape(note[last:m.start()]))
        url = m.group(1)
        text = xml_escape(m.group(2))
        parts.append(f'<a href="{url}" color="#0645ad">{text}</a>')
        last = m.end()
    parts.append(xml_escape(note[last:]))
    return ''.join(parts)


def note_to_md(note):
    """Convert LaTeX \\href{url}{text} to Markdown links."""
    return re.sub(r'\\href\{([^}]+)\}\{([^}]*)\}', r'[\2](\1)', note)


def register_fonts():
    pdfmetrics.registerFont(TTFont('DejaVu', DEJAVU))
    pdfmetrics.registerFont(TTFont('DejaVu-Bold', DEJAVU_BOLD))


class FooterCanvas(pdfcanvas.Canvas):
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
        self.setFont('DejaVu', 8)
        self.setFillColor(colors.HexColor('#777777'))
        y = 0.75 * cm
        self.drawString(2 * cm, y, TODAY)
        self.drawRightString(A4[0] - 2 * cm, y, f'Page {self._pageNumber} of {total}')
        self.restoreState()


def build_pdf(records, output_file, pdf_title):
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
        'Header', parent=styles['Heading1'],
        fontName='DejaVu-Bold', fontSize=16, spaceAfter=4,
        alignment=TA_CENTER, textColor=colors.HexColor('#1a1a6e'),
    )
    centered_style = ParagraphStyle(
        'Centered', parent=styles['Normal'],
        fontName='DejaVu', fontSize=12, spaceAfter=4,
        alignment=TA_CENTER, textColor=colors.HexColor('#333333'),
    )
    title_style = ParagraphStyle(
        'EntryTitle', parent=styles['Normal'],
        fontName='DejaVu-Bold', fontSize=10, leading=14,
        spaceAfter=2, textColor=colors.HexColor('#1a1a6e'),
    )
    meta_style = ParagraphStyle(
        'EntryMeta', parent=styles['Normal'],
        fontName='DejaVu', fontSize=8.5, leading=12,
        textColor=colors.HexColor('#333333'),
    )

    story = [
        Paragraph(pdf_title, header_style),
        Paragraph('Oliver Gutsche', centered_style),
        Paragraph(TODAY, centered_style),
        Spacer(1, 16),
    ]

    for i, record in enumerate(records, 1):
        meta = record['metadata']
        title = xml_escape(meta.get('title', 'Untitled'))
        date_str = format_date(meta.get('year', 0), meta.get('month', 0))
        note_html = note_to_html(meta.get('note', ''))

        story.append(Paragraph(f'{i}. {title}', title_style))
        story.append(Paragraph(f'{date_str} \u2014 {note_html}', meta_style))
        story.append(Spacer(1, 8))

    doc.build(story, canvasmaker=FooterCanvas)


def build_md(records, output_file):
    lines = []
    for i, record in enumerate(records, 1):
        meta = record['metadata']
        title = meta.get('title', 'Untitled')
        date_str = format_date(meta.get('year', 0), meta.get('month', 0))
        note_md = note_to_md(meta.get('note', ''))
        lines.append(f'{i}. **{title}**  ')
        lines.append(f'   {date_str} \u2014 {note_md}')
        lines.append('')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def main():
    if len(sys.argv) < 3:
        print(f'Usage: {sys.argv[0]} <input.json> <output.pdf>')
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    with open(input_path, encoding='utf-8') as f:
        data = json.load(f)

    records = data.get('records', [])
    records.sort(
        key=lambda r: (r['metadata'].get('year', 0), r['metadata'].get('month', 0)),
        reverse=True,
    )

    pdf_title = PDF_TITLES.get(input_path.name, 'List of Presentations and Talks of Oliver Gutsche')
    print(f'Building PDF and Markdown for {len(records)} records from {input_path.name}...')
    build_pdf(records, str(output_path), pdf_title)
    print(f'Saved to {output_path}')
    md_path = output_path.with_suffix('.md')
    build_md(records, str(md_path))
    print(f'Saved to {md_path}')


if __name__ == '__main__':
    main()
