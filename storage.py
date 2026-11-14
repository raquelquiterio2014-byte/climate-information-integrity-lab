"""SQLite audit trail: locally stored, not tamper-proof."""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB = Path('local_reviews.sqlite3')

def init(db=DB):
    with sqlite3.connect(db) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL,
            claim TEXT NOT NULL, decision TEXT NOT NULL, reviewer TEXT NOT NULL,
            notes TEXT NOT NULL, input_hash TEXT NOT NULL, analysis_hash TEXT NOT NULL)''')

def save(claim, decision, reviewer, notes, input_hash, analysis_hash, db=DB):
    if decision not in ('approved', 'rejected', 'needs_revision'):
        raise ValueError('Invalid review decision')
    if not reviewer.strip() or not notes.strip():
        raise ValueError('Reviewer and rationale are required')
    init(db)
    with sqlite3.connect(db) as conn:
        cursor = conn.execute('''INSERT INTO reviews
            (created_at,claim,decision,reviewer,notes,input_hash,analysis_hash)
            VALUES (?,?,?,?,?,?,?)''', (datetime.now(timezone.utc).isoformat(), claim,
                decision, reviewer.strip(), notes.strip(), input_hash, analysis_hash))
        return cursor.lastrowid

def list_reviews(db=DB):
    init(db)
    with sqlite3.connect(db) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(r) for r in conn.execute('SELECT * FROM reviews ORDER BY id DESC')]
