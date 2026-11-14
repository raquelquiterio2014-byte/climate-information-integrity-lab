"""Deterministic evidence handling; no AI verdict is automatically verified."""
import hashlib
import json
import re
from typing import Literal
from pydantic import BaseModel, Field, field_validator

class Finding(BaseModel):
    claim: str
    status: Literal['supported', 'contradicted', 'insufficient_evidence']
    explanation: str
    evidence_ids: list[str] = Field(default_factory=list)
    quotations: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)

    @field_validator('caveats', mode='before')
    @classmethod
    def normalize_caveats(cls, value):
        return [value] if isinstance(value, str) else value

class Analysis(BaseModel):
    findings: list[Finding]
    overall_limitations: list[str] = Field(default_factory=list)


def sha256_json(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


def check_grounding(analysis: Analysis, evidence: list[dict]) -> list[dict]:
    """Literal quote/ID checks only; semantic support still requires human review."""
    by_id = {row['id']: row for row in evidence}
    results = []
    for index, finding in enumerate(analysis.findings, 1):
        unknown = [eid for eid in finding.evidence_ids if eid not in by_id]
        excerpts = [by_id[eid]['excerpt'] for eid in finding.evidence_ids if eid in by_id]
        missing_quotes = [q for q in finding.quotations if not any(q.strip() in text for text in excerpts)]
        results.append({'finding': index, 'unknown_ids': unknown, 'unmatched_quotes': missing_quotes,
                        'has_cited_evidence': bool(excerpts),
                        'literal_checks_pass': bool(excerpts) and not unknown and not missing_quotes and bool(finding.quotations)})
    return results


def validate_claim(claim: str):
    claim = re.sub(r'\s+', ' ', claim).strip()
    if not 10 <= len(claim) <= 2000:
        raise ValueError('Claim must be between 10 and 2,000 characters.')
    return claim
