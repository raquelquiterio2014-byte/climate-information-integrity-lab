import pytest
from core import Analysis, Finding, check_grounding, sha256_json, validate_claim
from storage import save, list_reviews


def test_hash_is_stable():
    assert sha256_json({'a':1,'b':2}) == sha256_json({'b':2,'a':1})

def test_hash_changes():
    assert sha256_json({'a':1}) != sha256_json({'a':2})

def test_claim_validation():
    assert validate_claim('  Global   warming is real. ') == 'Global warming is real.'

def test_claim_too_short():
    with pytest.raises(ValueError): validate_claim('short')

def test_quote_and_id_match():
    analysis=Analysis(findings=[Finding(claim='Claim example',status='supported',explanation='Test',evidence_ids=['E1'],quotations=['exact phrase'])])
    assert check_grounding(analysis,[{'id':'E1','excerpt':'This has an exact phrase in it.'}])[0]['literal_checks_pass']

def test_quote_mismatch():
    analysis=Analysis(findings=[Finding(claim='Claim example',status='supported',explanation='Test',evidence_ids=['E1'],quotations=['not present'])])
    assert not check_grounding(analysis,[{'id':'E1','excerpt':'Other words'}])[0]['literal_checks_pass']

def test_unknown_id():
    analysis=Analysis(findings=[Finding(claim='Claim example',status='supported',explanation='Test',evidence_ids=['E99'],quotations=['words'])])
    assert check_grounding(analysis,[{'id':'E1','excerpt':'words'}])[0]['unknown_ids']==['E99']

def test_string_caveat_normalized():
    finding=Finding(claim='Claim example',status='insufficient_evidence',explanation='Test',caveats='needs review')
    assert finding.caveats==['needs review']

def test_audit_save_and_read(tmp_path):
    db=tmp_path/'audit.sqlite3'
    assert save('example claim','needs_revision','Reviewer','Check original','h1','h2',db)==1
    assert list_reviews(db)[0]['decision']=='needs_revision'

def test_audit_requires_notes(tmp_path):
    with pytest.raises(ValueError): save('claim','approved','Reviewer','','h1','h2',tmp_path/'a.sqlite3')
