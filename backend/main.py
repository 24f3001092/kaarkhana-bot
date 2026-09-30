
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from .config import ROOT, SARVAM_API_KEY, SARVAM_MODEL, ARTIFACT_DIR
from .db.store import init_db
from .api.tasks import router as task_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

app=FastAPI(title="KaarkhanaBot AI Work Agent", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
app.include_router(task_router)

@app.on_event("startup")
def startup():
    init_db()

@app.get("/api/health")
def health():
    return {"ok":True,"sarvam_configured":bool(SARVAM_API_KEY),"model":SARVAM_MODEL}

@app.get("/api/artifacts/{name}")
def artifact(name: str):
    path=(ARTIFACT_DIR/name).resolve()
    if path.parent != ARTIFACT_DIR.resolve() or not path.exists():
        return JSONResponse({"error":"Artifact not found"},status_code=404)
    return FileResponse(path, media_type="application/pdf", filename=path.name)

# Serve the existing frontend without requiring a second local web server.
app.mount("/static", StaticFiles(directory=str(ROOT)), name="static")

@app.get("/{path:path}")
def frontend(path: str=""):
    candidate=ROOT/path if path else ROOT/"index.html"
    if candidate.is_file() and candidate.resolve().parent == ROOT.resolve():
        return FileResponse(candidate)
    return FileResponse(ROOT/"index.html")
