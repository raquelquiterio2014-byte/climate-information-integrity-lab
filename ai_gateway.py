"""Optional live Gemini analysis, with strict structured output."""
import json
import os
from core import Analysis

SYSTEM = '''You are an educational climate-evidence analyst. Use ONLY the supplied evidence excerpts.
Do not browse or invent sources. A URL is provenance metadata, not proof of a claim.
For each finding use one of: supported, contradicted, insufficient_evidence.
Only use supported/contradicted when the provided excerpt directly warrants it; otherwise insufficient_evidence.
Every quotation MUST be an exact substring of the provided excerpt, and evidence_ids must match supplied IDs.
State caveats and distinguish short-term weather from long-term climate. This is a preliminary assessment, not fact-check certification.'''


def analyze(claim: str, evidence: list[dict], api_key: str, model: str = 'gemini-2.5-flash') -> Analysis:
    if not api_key:
        raise ValueError('GEMINI_API_KEY is required for live analysis.')
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=api_key)
    payload = {'claim': claim, 'evidence': evidence}
    response = client.models.generate_content(
        model=model,
        contents=json.dumps(payload, ensure_ascii=False),
        config=types.GenerateContentConfig(system_instruction=SYSTEM,
            response_mime_type='application/json', response_schema=Analysis, temperature=0),
    )
    if not response.text:
        raise ValueError('The model returned no usable text.')
    return Analysis.model_validate_json(response.text)
