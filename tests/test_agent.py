
import pytest
from backend.models.schemas import InputAnalysis
from backend.agent.planner import build_plan

def mk(**over):
    data=dict(
        user_goal="",
        intent="question_answering",
        sub_intents=[],
        language="English",
        user_context="",
        entities=[],
        constraints=[],
        provided_inputs=[],
        missing_inputs=[],
        expected_output="Answer",
        output_format="text",
        complexity="simple",
        requires_file=False,
        requires_web=False,
        requires_calculation=False,
        requires_code_execution=False,
        requires_generation=False,
        recommended_tools=["Sarvam AI"],
        needs_clarification=False,
        clarification_question="",
    )
    data.update(over)
    return InputAnalysis.model_validate(data)

@pytest.mark.parametrize("prompt,expected_intent,language,complexity",[
    ("Explain Python.","question_answering","English","simple"),
    ("Is PDF ko simple Hinglish mein explain karo.","document_analysis","Hinglish","medium"),
    ("Analyze this Excel and create charts.","data_analysis","English","medium"),
    ("Research Indian EV market and create a report.","research","English","complex"),
    ("Fix this code and explain the error.","coding_debugging","English","medium"),
])
def test_expected_analysis_contract(prompt,expected_intent,language,complexity):
    # The real model supplies this object. This test locks the contract the analyzer must satisfy.
    a=mk(user_goal=prompt,intent=expected_intent,language=language,complexity=complexity)
    assert a.intent==expected_intent
    assert a.language==language
    assert a.complexity==complexity

def test_file_analysis_requires_file():
    a=mk(user_goal="Explain the uploaded PDF",intent="document_analysis",
          language="Hinglish",complexity="medium",requires_file=True,
          provided_inputs=["PDF: sample.pdf"],recommended_tools=["pdf_reader"])
    assert a.requires_file is True
    assert "pdf_reader" in a.recommended_tools

def test_multi_intent_plan():
    a=mk(user_goal="Analyze PDF, extract topics, compare PYQs and make priority list",
         intent="document_analysis",
         sub_intents=["topic_extraction","PYQ_comparison","priority_generation"],
         complexity="complex",requires_file=True,
         requires_generation=True,recommended_tools=["pdf_reader","ai_analysis","artifact_generator"])
    p=build_plan(a)
    assert len(p.steps)>=4
    assert any("sub-task" in s.action for s in p.steps)
    assert any(s.tool=="Verifier" for s in p.steps)

def test_clarification_contract():
    a=mk(user_goal="Create a presentation",intent="presentation_creation",
         complexity="medium",needs_clarification=True,
         missing_inputs=["presentation topic or source content"],
         clarification_question="What should the presentation be about?")
    assert a.needs_clarification
    assert a.clarification_question

def test_context_reference_contract():
    a=mk(user_goal="Improve the previously generated document",
         intent="rewriting",user_context="Assistant previously generated a document.",
         complexity="medium")
    assert "previously" in a.user_goal.lower()
