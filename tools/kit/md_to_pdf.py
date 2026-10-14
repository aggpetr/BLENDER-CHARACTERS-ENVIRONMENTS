"""Small Markdown -> PDF converter for the project guides (headings, paragraphs, lists, tables, code blocks, quotes).

    python tools/kit/md_to_pdf.py docs/Edo_Village_Unreal_Guide.md docs/Edo_Village_Unreal_Guide.pdf        (needs reportlab)
"""
import re, sys
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Preformatted, HRFlowable, KeepTogether

INK, ACCENT, MUTED, HEAD_BG, ALT = colors.HexColor('#1f2937'), colors.HexColor('#8b2e2e'), colors.HexColor('#6b7280'), colors.HexColor('#2b2b2b'), colors.HexColor('#f3f1ee')
ss = getSampleStyleSheet()
body = ParagraphStyle('body', parent=ss['Normal'], fontName='Helvetica', fontSize=9.4, leading=13, textColor=INK, spaceAfter=5)
cell = ParagraphStyle('cell', parent=body, fontSize=8.2, leading=10.4, spaceAfter=0)
cellh = ParagraphStyle('cellh', parent=cell, fontName='Helvetica-Bold', textColor=colors.white)
h1 = ParagraphStyle('h1', parent=ss['Title'], fontName='Helvetica-Bold', fontSize=22, leading=26, textColor=INK, alignment=0, spaceAfter=8)
h2 = ParagraphStyle('h2', parent=ss['Heading1'], fontName='Helvetica-Bold', fontSize=14.5, leading=18, textColor=ACCENT, spaceBefore=14, spaceAfter=5)
h3 = ParagraphStyle('h3', parent=ss['Heading2'], fontName='Helvetica-Bold', fontSize=11, leading=14, textColor=INK, spaceBefore=8, spaceAfter=3)
bullet = ParagraphStyle('bullet', parent=body, leftIndent=16, bulletIndent=4, spaceAfter=2.5)
quote = ParagraphStyle('quote', parent=body, leftIndent=12, textColor=colors.HexColor('#7a4a00'), backColor=colors.HexColor('#fbf3e2'), borderPadding=6, spaceBefore=4, spaceAfter=8)
code = ParagraphStyle('code', parent=ss['Code'], fontName='Courier', fontSize=7.6, leading=9.6, backColor=colors.HexColor('#f4f4f4'), borderPadding=5, spaceBefore=3, spaceAfter=8)


def inline(t):
    t = escape(t)
    t = re.sub(r'`([^`]+)`', r'<font face="Courier" size="8">\1</font>', t)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'(?<![\w*])\*([^*\n]+)\*(?![\w*])', r'<i>\1</i>', t)
    return t


def table(rows):
    data = [[Paragraph(inline(c), cellh if i == 0 else cell) for c in r] for i, r in enumerate(rows)]
    n = len(rows[0]); W = A4[0] - 3.6 * cm
    lens = [max(len(r[j]) for r in rows) for j in range(n)]
    w = [max(0.08, min(l, 70) ** 0.8) for l in lens]; tot = sum(w); widths = [W * x / tot for x in w]
    t = Table(data, colWidths=widths, repeatRows=1)
    st = [('BACKGROUND', (0, 0), (-1, 0), HEAD_BG), ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#d6d3ce')),
          ('LEFTPADDING', (0, 0), (-1, -1), 4), ('RIGHTPADDING', (0, 0), (-1, -1), 4), ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3)]
    for i in range(1, len(rows)):
        if i % 2 == 0: st.append(('BACKGROUND', (0, i), (-1, i), ALT))
    t.setStyle(TableStyle(st)); return t


def build(md, out):
    story = []; lines = md.split('\n'); i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith('```'):
            j = i + 1; buf = []
            while j < len(lines) and not lines[j].startswith('```'): buf.append(lines[j]); j += 1
            story.append(Preformatted('\n'.join(buf), code)); i = j + 1; continue
        if ln.startswith('|') and i + 1 < len(lines) and re.match(r'^\|[\s:|-]+\|$', lines[i + 1].strip()):
            rows = [[c.strip() for c in ln.strip().strip('|').split('|')]]; j = i + 2
            while j < len(lines) and lines[j].startswith('|'):
                rows.append([c.strip() for c in lines[j].strip().strip('|').split('|')]); j += 1
            story += [table(rows), Spacer(1, 8)]; i = j; continue
        m = re.match(r'^(#{1,3}) (.*)', ln)
        if m: story.append(Paragraph(inline(m.group(2)), {1: h1, 2: h2, 3: h3}[len(m.group(1))])); i += 1; continue
        if ln.strip() == '---': story += [HRFlowable(width='100%', color=colors.HexColor('#d6d3ce'), spaceBefore=4, spaceAfter=4)]; i += 1; continue
        if ln.startswith('>'):
            buf = []
            while i < len(lines) and lines[i].startswith('>'): buf.append(lines[i].lstrip('> ').strip()); i += 1
            story.append(Paragraph(inline(' '.join(buf)), quote)); continue
        m = re.match(r'^(\s*)(?:[-*]|\d+\.) (.*)', ln)
        if m:
            numbered = re.match(r'^\s*\d+\.', ln); k = 0
            while i < len(lines):
                mm = re.match(r'^(\s*)([-*]|\d+\.) (.*)', lines[i])
                if not mm: break
                k += 1; text = mm.group(3); i += 1
                while i < len(lines) and lines[i].startswith('   ') and lines[i].strip() and not re.match(r'^\s*([-*]|\d+\.) ', lines[i]): text += ' ' + lines[i].strip(); i += 1
                story.append(Paragraph(inline(text), bullet, bulletText=(f'{k}.' if numbered else '•')))
            continue
        if ln.strip() == '': i += 1; continue
        buf = [ln.strip()]; i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r'^(#|>|\||```|---|\s*([-*]|\d+\.) )', lines[i]): buf.append(lines[i].strip()); i += 1
        story.append(Paragraph(inline(' '.join(buf)), body))
    def footer(c, d):
        c.saveState(); c.setFont('Helvetica', 7.5); c.setFillColor(MUTED); c.drawString(1.8 * cm, 1.1 * cm, 'Edo Village in Unreal Engine: import and setup guide'); c.drawRightString(A4[0] - 1.8 * cm, 1.1 * cm, f'{d.page}'); c.restoreState()
    SimpleDocTemplate(out, pagesize=A4, leftMargin=1.8 * cm, rightMargin=1.8 * cm, topMargin=1.6 * cm, bottomMargin=1.8 * cm, title='Edo Village in Unreal Engine: import and setup guide').build(story, onFirstPage=footer, onLaterPages=footer)


if __name__ == '__main__':
    build(open(sys.argv[1], encoding='utf-8').read(), sys.argv[2]); print('wrote', sys.argv[2])
