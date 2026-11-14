# Climate Information Integrity Lab V1.0

COP31 AI Solutions Lab · Day 6 · Educational prototype. **This is not a certified climate fact-checking system.**

## Features
- Five dark-green Streamlit tabs: Overview, Evidence Library, AI Claim Analyzer, Human Review, Export & Methodology.
- Optional live Gemini 2.5 Flash structured analysis of user-supplied claims and excerpts.
- Deterministic evidence-ID and literal-quotation matching. **Matching does not prove semantic support.**
- Human review with SQLite, SHA-256 payload fingerprints and CSV/JSON exports.
- Small bundled educational examples and automated unit tests.

## Setup (Windows PowerShell, Python 3.12)
```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```
Edit `.env` locally and replace `YOUR_API_KEY_HERE` with your Gemini API key. Never commit `.env`.

## Run
```powershell
python -m pytest -q
python -m streamlit run app.py
```

## How to test manually
1. Open the Evidence Library; confirm three reference records are shown.
2. Select an example claim in AI Claim Analyzer and select evidence IDs.
3. Click Analyze with Gemini. A successful API response shows structured findings and literal citation checks.
4. Check whether quoted text is literally present in the selected evidence. **The default excerpts are educational paraphrases, not verified verbatim quotes.**
5. In Human Review, choose `needs_revision`, add a reviewer and reason, then save.
6. Export evidence, audit and AI JSON. Inspect their contents.

## Limitations
The bundled reference records point to public organizations but their excerpts are **author-written paraphrases**; their wording has not been authenticated against the linked documents. Gemini sees only submitted excerpts, does not browse, and can be wrong. The app does not perform semantic grounding verification, authoritative fact checking, source retrieval, batch processing or immutable audit logging. User-provided text is sent to Google's API when analysis is invoked; do not enter private data. SQLite review records are local. No live Gemini API test is included in unit tests.
