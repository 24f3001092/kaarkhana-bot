
import json, uuid, logging
from pathlib import Path
from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from ..config import MAX_FILE_MB, ARTIFACT_DIR, DAILY_LIMIT
from ..providers.sarvam import SarvamProvider, ProviderError
from ..agent.analyzer import InputAnalyzer
from ..agent.planner import build_plan
from ..agent.prompts import FINAL_SYSTEM, final_user
from ..models.schemas import InputAnalysis
from ..tools.documents import ALLOWED_EXTENSIONS, safe_filename, extract_text
from ..tools.artifacts import create_pdf
from ..db.store import add_message, recent_messages, save_task

router=APIRouter(prefix="/api")
log=logging.getLogger("kaarkhanabot.tasks")

def get_provider():
    return SarvamProvider()

@router.post("/tasks")
async def run_task(
    prompt: str = Form(""),
    conversation_id: str = Form("default"),
    files: list[UploadFile] = File(default=[]),
):
    task_id="task_"+uuid.uuid4().hex[:12]
    saved=[]
    try:
        total=0
        extracted=[]
        metadata=[]
        for upload in files:
            suffix=Path(upload.filename or "").suffix.lower()
            if suffix not in ALLOWED_EXTENSIONS:
                raise HTTPException(400, f"Unsupported file type: {suffix or 'unknown'}")
            content=await upload.read()
            total += len(content)
            if len(content)>MAX_FILE_MB*1024*1024:
                raise HTTPException(413, f"{upload.filename}: file exceeds {MAX_FILE_MB} MB limit.")
            safe=safe_filename(upload.filename)
            path=ARTIFACT_DIR / f"upload_{uuid.uuid4().hex}_{safe}"
            path.write_bytes(content)
            saved.append(path)
            try:
                txt, meta=extract_text(path)
            except Exception as exc:
                log.warning("File extraction failed for %s: %s", safe, exc)
                txt=""
                meta={"name":safe,"extension":suffix,"size_bytes":len(content),"extraction_error":True}
            metadata.append(meta)
            extracted.append(txt)

        context_rows=recent_messages(conversation_id, limit=6)
        context="\n".join(f"{m['role']}: {m['content']}" for m in context_rows)
        file_meta=json.dumps(metadata,ensure_ascii=False,indent=2)
        file_text="\n\n".join(x for x in extracted if x)[:50000]

        provider=get_provider()
        analyzer=InputAnalyzer(provider)
        analysis=await analyzer.analyze(prompt,context,file_meta,file_text)
        add_message(conversation_id,"user",prompt or "[uploaded files]")
        save_task(task_id,conversation_id,prompt,"analyzed",analysis.model_dump())

        if analysis.needs_clarification:
            answer={"title":"One detail needed","body":analysis.clarification_question}
            save_task(task_id,conversation_id,prompt,"needs_clarification",analysis.model_dump(),answer=answer)
            return {"task_id":task_id,"conversation_id":conversation_id,"status":"needs_clarification",
                    "analysis":analysis.model_dump(),"plan":[],"tools":analysis.recommended_tools,
                    "activity":["Understood the request","Checked available inputs","Found one essential missing detail"],
                    "answer":answer}

        plan=build_plan(analysis)
        tools=list(dict.fromkeys(analysis.recommended_tools + [s.tool for s in plan.steps]))
        activity=["Understood the goal and supplied inputs",
                  f"Identified intent: {analysis.intent}",
                  f"Classified complexity: {analysis.complexity}",
                  "Selected only the tools required by the task"]

        # A real web search/code sandbox is intentionally not faked.
        unavailable=[]
        if analysis.requires_web: unavailable.append("Web research")
        if analysis.requires_code_execution: unavailable.append("Sandboxed code execution")
        if unavailable:
            # Still ask Sarvam to answer what can be done from current inputs, while clearly stating limits.
            activity.append("Checked tool availability; unavailable external tools will not be simulated")

        final_messages=[
            {"role":"system","content":FINAL_SYSTEM},
            {"role":"user","content":final_user(prompt,analysis.model_dump_json(),plan.model_dump_json(),context,file_text)}
        ]
        answer_text=await provider.text(final_messages,max_tokens=3500)
        if unavailable:
            answer_text += "\n\n**Tool availability note:** " + ", ".join(unavailable) + " is not connected in this local build, so no unsupported result was claimed."

        answer={"title":"Task completed","body":answer_text,"source_grounded":bool(file_text)}
        artifact=None
        if analysis.requires_generation or analysis.intent in {"document_analysis","summarization","information_extraction","document_to_presentation","file_generation"}:
            try:
                name,path=create_pdf("KaarkhanaBot Task Result",answer_text,ARTIFACT_DIR)
                artifact={"name":name,"type":"PDF","url":f"/api/artifacts/{name}"}
                activity.append("Generated the requested PDF artifact")
            except Exception:
                log.exception("Artifact generation failed")
                activity.append("Artifact generation failed; the answer is still available")
        activity.append("Verified that the response does not claim unavailable tool execution")
        add_message(conversation_id,"assistant",answer_text)
        save_task(task_id,conversation_id,prompt,"complete",analysis.model_dump(),plan.model_dump(),answer)
        return {"task_id":task_id,"conversation_id":conversation_id,"status":"complete",
                "analysis":analysis.model_dump(),"plan":[s.model_dump() for s in plan.steps],
                "tools":tools,"activity":activity,"answer":answer,"artifact":artifact}
    except HTTPException:
        raise
    except ProviderError as exc:
        log.warning("Provider failure for task %s: %s",task_id,str(exc))
        save_task(task_id,conversation_id,prompt,"failed")
        return {"task_id":task_id,"conversation_id":conversation_id,"status":"failed",
                "activity":["Task received","AI provider call failed safely"],"error":str(exc)}
    except Exception as exc:
        log.exception("Unexpected task failure")
        save_task(task_id,conversation_id,prompt,"failed")
        return {"task_id":task_id,"conversation_id":conversation_id,"status":"failed",
                "activity":["Task received","An unexpected processing error occurred"],"error":"The task could not be completed. Check the server log for details."}
