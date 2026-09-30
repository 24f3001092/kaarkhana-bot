
import json
from pydantic import ValidationError
from ..models.schemas import InputAnalysis
from ..providers.sarvam import SarvamProvider, ProviderError
from .prompts import ANALYZER_SYSTEM, analyzer_user

class InputAnalyzer:
    def __init__(self, provider: SarvamProvider):
        self.provider = provider

    async def analyze(self, prompt, context, file_metadata, extracted_text):
        schema = InputAnalysis.model_json_schema()
        messages = [
            {"role": "system", "content": ANALYZER_SYSTEM},
            {"role": "user", "content": analyzer_user(prompt, context, file_metadata, extracted_text)},
        ]
        raw = await self.provider.structured(messages, schema, "kaarkhanabot_input_analysis")
        try:
            return InputAnalysis.model_validate(raw)
        except ValidationError as exc:
            raise ProviderError("Input analysis failed schema validation.") from exc
