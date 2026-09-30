
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.units import mm
import re, uuid

def markdownish_to_flowables(text: str):
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name="KBTitle", parent=styles["Title"], alignment=TA_CENTER, spaceAfter=10))
    styles.add(ParagraphStyle(name="KBBody", parent=styles["BodyText"], leading=15, spaceAfter=7))
    styles.add(ParagraphStyle(name="KBHeading", parent=styles["Heading2"], spaceBefore=8, spaceAfter=6))
    story=[]
    for raw in text.splitlines():
        line=raw.strip()
        if not line:
            story.append(Spacer(1,3)); continue
        if line.startswith("# "):
            story.append(Paragraph(esc(line[2:]), styles["KBTitle"]))
        elif line.startswith("## "):
            story.append(Paragraph(esc(line[3:]), styles["KBHeading"]))
        elif re.match(r"^\d+\.\s+",line):
            story.append(Paragraph(esc(line), styles["KBBody"]))
        elif line.startswith("- "):
            story.append(Paragraph("• "+esc(line[2:]), styles["KBBody"]))
        else:
            story.append(Paragraph(esc(line), styles["KBBody"]))
    return story

def esc(s):
    return (str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;"))

def create_pdf(title: str, content: str, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    name=f"{re.sub(r'[^A-Za-z0-9_-]+','_',title)[:80] or 'KaarkhanaBot'}_{uuid.uuid4().hex[:8]}.pdf"
    path=out_dir/name
    doc=SimpleDocTemplate(str(path), pagesize=A4, rightMargin=18*mm,leftMargin=18*mm,topMargin=18*mm,bottomMargin=18*mm)
    doc.build(markdownish_to_flowables(f"# {title}\n\n{content}"))
    return name, path
