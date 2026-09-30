
from typing import Any, Literal
from pydantic import BaseModel, Field, ConfigDict

class Entity(BaseModel):
    name: str
    value: str

class InputAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_goal: str
    intent: str
    sub_intents: list[str] = Field(default_factory=list)
    language: str
    user_context: str
    entities: list[Entity] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    provided_inputs: list[str] = Field(default_factory=list)
    missing_inputs: list[str] = Field(default_factory=list)
    expected_output: str
    output_format: str
    complexity: Literal["simple", "medium", "complex"]
    requires_file: bool
    requires_web: bool
    requires_calculation: bool
    requires_code_execution: bool
    requires_generation: bool
    recommended_tools: list[str] = Field(default_factory=list)
    needs_clarification: bool
    clarification_question: str = ""

class PlanStep(BaseModel):
    id: int
    action: str
    tool: str

class TaskPlan(BaseModel):
    goal: str
    steps: list[PlanStep]

class TaskRequest(BaseModel):
    prompt: str = ""
    conversation_id: str = "default"
    language: str | None = None

class TaskResponse(BaseModel):
    task_id: str
    conversation_id: str
    status: str
    analysis: InputAnalysis | None = None
    plan: list[PlanStep] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    activity: list[str] = Field(default_factory=list)
    answer: dict[str, Any] | None = None
    artifact: dict[str, Any] | None = None
    error: str | None = None
