import json
import os
from pathlib import Path
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from core import Analysis, Finding, check_grounding, sha256_json, validate_claim
from ai_gateway import analyze
from storage import save, list_reviews

load_dotenv()
st.set_page_config(page_title='Climate Information Integrity Lab', page_icon='🔎', layout='wide')
st.markdown('''<style>
.stApp {background: #071d19; color: #eaf7ee;}
[data-testid="stSidebar"] {background: #0c3029;}
h1,h2,h3 {color: #a5e5bf !important;}
div[data-testid="stMetric"] {background:#103c32; border:1px solid #277b60; padding:12px; border-radius:10px;}
</style>''', unsafe_allow_html=True)

ROOT = Path(__file__).parent
DEFAULT_EVIDENCE = pd.read_csv(ROOT / 'data' / 'evidence.csv').fillna('')
DEFAULT_CLAIMS = pd.read_csv(ROOT / 'data' / 'sample_claims.csv')

if 'analysis' not in st.session_state:
    st.session_state.analysis = None
if 'last_input' not in st.session_state:
    st.session_state.last_input = None

st.title('🔎 Climate Information Integrity Lab V1.0')
st.caption('COP31 AI Solutions Lab · Day 6 · Educational prototype · Evidence first. Engineering second. Measurable impact as the goal.')
st.warning('Evidence excerpts in the bundled CSV are EDUCATIONAL PARAPHRASES, not authenticated verbatim quotations. AI results are provisional. No automatic source retrieval or scientific verification is claimed.')

t1,t2,t3,t4,t5 = st.tabs(['📊 Overview', '📚 Evidence Library', '🤖 AI Claim Analyzer', '🛡️ Human Review', '📤 Export & Methodology'])
with t1:
    st.subheader('Scope and educational examples')
    a,b,c = st.columns(3)
    a.metric('Example claims', len(DEFAULT_CLAIMS))
    b.metric('Reference records', len(DEFAULT_EVIDENCE))
    c.metric('Review decisions', len(list_reviews()))
    st.dataframe(DEFAULT_CLAIMS, use_container_width=True, hide_index=True)
    st.info('Statuses are AI-generated hypotheses, not certified truth labels. The local audit is not tamper-proof.')
with t2:
    st.subheader('Evidence records')
    uploaded = st.file_uploader('Optional CSV with id, organization, title, url, excerpt, source_note', type=['csv'])
    if uploaded:
        try:
            df = pd.read_csv(uploaded).fillna('')
            required = {'id','organization','title','url','excerpt','source_note'}
            if not required.issubset(df.columns):
                raise ValueError('Missing columns: '+', '.join(sorted(required-set(df.columns))))
            if df['id'].duplicated().any() or df['id'].astype(str).str.strip().eq('').any():
                raise ValueError('Evidence IDs must be unique and non-empty')
            if len(df)>100 or df['excerpt'].astype(str).str.len().max()>5000:
                raise ValueError('Maximum 100 evidence records and 5,000 characters per excerpt')
            st.session_state.evidence_df = df
        except Exception as exc:
            st.error(f'Invalid CSV: {exc}')
    evidence_df = st.session_state.get('evidence_df', DEFAULT_EVIDENCE)
    st.dataframe(evidence_df, use_container_width=True, hide_index=True)
    st.caption('Uploading excerpts does not authenticate their origin. Verify original documents before drawing conclusions.')
with t3:
    st.subheader('AI-assisted claim assessment')
    example = st.selectbox('Example claim', ['Custom'] + DEFAULT_CLAIMS['claim'].tolist())
    claim_text = st.text_area('Claim to assess', value='' if example=='Custom' else example, height=90)
    evidence_df = st.session_state.get('evidence_df', DEFAULT_EVIDENCE)
    ids = st.multiselect('Evidence records to provide to the model', evidence_df['id'].astype(str).tolist(), default=evidence_df['id'].astype(str).tolist())
    chosen = evidence_df[evidence_df['id'].astype(str).isin(ids)].to_dict(orient='records')
    api_key = os.getenv('GEMINI_API_KEY', '')
    st.caption('Gemini receives the claim and selected excerpts. Do not submit sensitive or personal information.')
    if st.button('Analyze with Gemini', type='primary'):
        try:
            cleaned = validate_claim(claim_text)
            if not chosen: raise ValueError('Select at least one evidence record')
            if not api_key: raise ValueError('Set GEMINI_API_KEY in your local .env file')
            with st.spinner('Requesting Gemini analysis...'):
                result = analyze(cleaned, chosen, api_key, os.getenv('GEMINI_MODEL','gemini-2.5-flash'))
            st.session_state.analysis = result.model_dump()
            st.session_state.last_input = {'claim':cleaned,'evidence':chosen}
            st.success('API response received. Human verification is still required.')
        except Exception as exc:
            st.error(f'Analysis could not be completed: {exc}')
    if st.session_state.analysis:
        analysis = Analysis.model_validate(st.session_state.analysis)
        checks = check_grounding(analysis, st.session_state.last_input['evidence'])
        st.subheader('Structured AI output')
        st.json(st.session_state.analysis)
        st.subheader('Deterministic citation checks')
        st.dataframe(pd.DataFrame(checks), use_container_width=True, hide_index=True)
        if not all(x['literal_checks_pass'] for x in checks):
            st.error('Some citations fail literal checks. Treat these findings as needing revision.')
        else:
            st.warning('Literal citation checks passed; this does NOT establish that claims are scientifically supported.')
with t4:
    st.subheader('Human review and local audit')
    if st.session_state.analysis and st.session_state.last_input:
        decision = st.selectbox('Review decision', ['needs_revision','approved','rejected'])
        reviewer = st.text_input('Reviewer name or pseudonym')
        notes = st.text_area('Review rationale (required)')
        if st.button('Save review'):
            try:
                inp = st.session_state.last_input
                row_id = save(inp['claim'], decision, reviewer, notes, sha256_json(inp), sha256_json(st.session_state.analysis))
                st.success(f'Review saved locally. Record #{row_id}')
            except Exception as exc:
                st.error(str(exc))
    else:
        st.info('Run an AI analysis first to enable review.')
    st.dataframe(pd.DataFrame(list_reviews()), use_container_width=True, hide_index=True)
with t5:
    st.subheader('Export')
    st.download_button('Download evidence CSV', st.session_state.get('evidence_df', DEFAULT_EVIDENCE).to_csv(index=False).encode(), 'evidence.csv', 'text/csv')
    st.download_button('Download review audit CSV', pd.DataFrame(list_reviews(), columns=['id','created_at','claim','decision','reviewer','notes','input_hash','analysis_hash']).to_csv(index=False).encode(), 'human_review_audit.csv', 'text/csv')
    if st.session_state.analysis:
        st.download_button('Download AI analysis JSON', json.dumps(st.session_state.analysis,indent=2,ensure_ascii=False), 'ai_analysis.json', 'application/json')
        st.download_button('Download input JSON', json.dumps(st.session_state.last_input,indent=2,ensure_ascii=False), 'analysis_input.json', 'application/json')
    st.markdown('''**Methodology and limitations**
1. Load source metadata and text excerpts; verify them independently against official documents.
2. Submit a claim and selected excerpts to Gemini, requesting structured preliminary findings.
3. Check that referenced evidence IDs exist and quoted strings literally appear in supplied excerpts.
4. Have a human inspect original sources and approve, reject or request revision.
5. Export the results. SHA-256 identifies exact local payloads, not source authenticity or audit immutability.

**Not implemented:** automatic web retrieval, authenticated source snapshots, semantic entailment scoring, benchmarked accuracy, multi-user authentication, immutable audit logs, or production-scale batch processing.
''')
