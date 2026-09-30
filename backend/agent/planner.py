
from ..models.schemas import InputAnalysis, TaskPlan, PlanStep

TOOL_ALIASES = {
    "document_reader": "Document reader",
    "pdf_reader": "PDF reader",
    "spreadsheet_analyzer": "Spreadsheet analyzer",
    "data_analyzer": "Data analyzer",
    "chart_generator": "Chart generator",
    "image_analyzer": "Image analyzer",
    "vision": "Image analyzer",
    "code_executor": "Code executor",
    "calculator": "Calculator",
    "web_search": "Web research",
    "research": "Web research",
    "document_generator": "Document generator",
    "presentation_generator": "Presentation generator",
    "pptx_generator": "Presentation generator",
    "artifact_generator": "Artifact generator",
    "ai_analysis": "Sarvam AI analysis",
}

def normalize_tools(tools):
    out=[]
    for t in tools:
        key=t.lower().replace(" ","_")
        label=TOOL_ALIASES.get(key, t)
        if label not in out:
            out.append(label)
    return out or ["Sarvam AI"]

def build_plan(a: InputAnalysis) -> TaskPlan:
    tools=normalize_tools(a.recommended_tools)
    steps=[]
    idx=1
    if a.requires_file:
        steps.append(PlanStep(id=idx, action="Inspect supplied file metadata and extract usable content", tool="Document reader"))
        idx+=1
    if a.sub_intents:
        for intent in a.sub_intents[:6]:
            steps.append(PlanStep(id=idx, action=f"Complete sub-task: {intent}", tool=tools[min(len(steps), len(tools)-1)]))
            idx+=1
    else:
        steps.append(PlanStep(id=idx, action=f"Complete the primary task: {a.intent}", tool=tools[0]))
        idx+=1
    if a.requires_generation:
        steps.append(PlanStep(id=idx, action=f"Generate the requested {a.output_format or 'artifact'}", tool="Artifact generator"))
        idx+=1
    steps.append(PlanStep(id=idx, action="Verify important facts, calculations, constraints and output format", tool="Verifier"))
    return TaskPlan(goal=a.user_goal, steps=steps)
