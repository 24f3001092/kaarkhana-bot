
import csv, json, mimetypes, os, re
from pathlib import Path
from typing import Any

ALLOWED_EXTENSIONS = {
    ".pdf",".docx",".pptx",".xlsx",".csv",".txt",".md",".json",
    ".png",".jpg",".jpeg",".webp"
}

def safe_filename(name: str) -> str:
    name = Path(name or "upload").name
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name)[:150] or "upload"

def metadata_for(path: Path) -> dict[str, Any]:
    suffix=path.suffix.lower()
    mime=mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return {"name": path.name, "extension": suffix, "size_bytes": path.stat().st_size, "mime_type": mime}

def extract_text(path: Path) -> tuple[str, dict[str, Any]]:
    suffix=path.suffix.lower()
    meta=metadata_for(path)
    if suffix == ".pdf":
        from pypdf import PdfReader
        reader=PdfReader(str(path))
        meta["pages"]=len(reader.pages)
        parts=[]
        for i,p in enumerate(reader.pages):
            text=p.extract_text() or ""
            if text:
                parts.append(f"[PAGE {i+1}]\n{text}")
        return "\n\n".join(parts), meta
    if suffix == ".docx":
        from docx import Document
        doc=Document(str(path))
        text="\n".join(p.text for p in doc.paragraphs if p.text.strip())
        meta["paragraphs"]=len(doc.paragraphs)
        return text, meta
    if suffix == ".pptx":
        from pptx import Presentation
        prs=Presentation(str(path))
        parts=[]
        for i,slide in enumerate(prs.slides):
            vals=[]
            for shape in slide.shapes:
                if hasattr(shape,"text") and shape.text.strip():
                    vals.append(shape.text.strip())
            parts.append(f"[SLIDE {i+1}]\n"+"\n".join(vals))
        meta["slides"]=len(prs.slides)
        return "\n\n".join(parts), meta
    if suffix in {".xlsx",".xls"}:
        from openpyxl import load_workbook
        wb=load_workbook(str(path), read_only=True, data_only=True)
        meta["sheets"]=wb.sheetnames
        chunks=[]
        for ws in wb.worksheets:
            rows=[]
            for row in ws.iter_rows(values_only=True):
                vals=[("" if v is None else str(v)) for v in row]
                if any(vals):
                    rows.append("\t".join(vals))
                if len(rows)>=250:
                    break
            chunks.append(f"[SHEET {ws.title}]\n"+"\n".join(rows))
        return "\n\n".join(chunks), meta
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as f:
            rows=list(csv.reader(f))
        meta["rows"]=max(0,len(rows)-1)
        meta["columns"]=len(rows[0]) if rows else 0
        return "\n".join("\t".join(r) for r in rows[:251]), meta
    if suffix in {".txt",".md",".json"}:
        text=path.read_text(encoding="utf-8",errors="replace")
        if suffix==".json":
            try:
                obj=json.loads(text)
                text=json.dumps(obj,ensure_ascii=False,indent=2)
            except Exception:
                pass
        return text, meta
    if suffix in {".png",".jpg",".jpeg",".webp"}:
        meta["image"]=True
        return "", meta
    return "", meta
