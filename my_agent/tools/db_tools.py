"""Database tools for CareerOS — SQLite storage layer."""

import json
import os
import sqlite3
from datetime import datetime

# DB file lives next to the agent code
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "career_os.db")


def _get_connection() -> sqlite3.Connection:
    """Return a connection to the SQLite database, creating tables if needed."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    _ensure_tables(conn)
    return conn


def _ensure_tables(conn: sqlite3.Connection) -> None:
    """Create all required tables if they don't exist yet."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS resumes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT,
            email       TEXT,
            phone       TEXT,
            education   TEXT,
            experience  TEXT,
            skills      TEXT,
            projects    TEXT,
            certifications TEXT,
            raw_text    TEXT,
            created_at  TEXT
        );

        CREATE TABLE IF NOT EXISTS resume_analysis (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_id        INTEGER,
            strengths        TEXT,
            weaknesses       TEXT,
            experience_level TEXT,
            domain_focus     TEXT,
            key_technologies TEXT,
            summary          TEXT,
            created_at       TEXT
        );

        CREATE TABLE IF NOT EXISTS profiles (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_id           INTEGER,
            tech_stack          TEXT,
            interests           TEXT,
            career_goals        TEXT,
            preferred_roles     TEXT,
            experience_summary  TEXT,
            location_preference TEXT,
            search_keywords     TEXT,
            created_at          TEXT
        );

        CREATE TABLE IF NOT EXISTS opportunities (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id  INTEGER,
            title       TEXT,
            url         TEXT,
            description TEXT,
            source      TEXT,
            category    TEXT,
            deadline    TEXT,
            raw_data    TEXT,
            created_at  TEXT
        );

        CREATE TABLE IF NOT EXISTS ranked_opportunities (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            opportunity_id   INTEGER,
            profile_id       INTEGER,
            relevance_score  INTEGER,
            match_reasons    TEXT,
            rank             INTEGER,
            category         TEXT,
            created_at       TEXT
        );
    """)
    conn.commit()


# ── Public tool functions (called by agents) ─────────────────────────────────


def store_to_db(table: str, data: str) -> dict:
    """Stores a JSON record into the specified database table.

    Args:
        table: The name of the table to insert into (e.g. 'resumes', 'profiles').
        data: A JSON string representing the record to insert.

    Returns:
        A dict with status and the inserted row id.
    """
    try:
        record = json.loads(data) if isinstance(data, str) else data
    except json.JSONDecodeError:
        return {"status": "error", "message": "Invalid JSON in data parameter"}

    record["created_at"] = datetime.now().isoformat()

    conn = _get_connection()
    try:
        columns = ", ".join(record.keys())
        placeholders = ", ".join(["?"] * len(record))
        values = []
        for v in record.values():
            if isinstance(v, (dict, list)):
                values.append(json.dumps(v))
            else:
                values.append(v)

        cursor = conn.execute(
            f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", values
        )
        conn.commit()
        return {"status": "success", "id": cursor.lastrowid, "table": table}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()


def read_from_db(table: str, query_filter: str = "") -> dict:
    """Reads records from the specified database table.

    Args:
        table: The name of the table to read from.
        query_filter: Optional SQL WHERE clause (e.g. 'id = 1' or 'resume_id = 1').
                      Leave empty to read all records.

    Returns:
        A dict with status and a list of matching records.
    """
    conn = _get_connection()
    try:
        if query_filter and query_filter.strip():
            sql = f"SELECT * FROM {table} WHERE {query_filter} ORDER BY id DESC"
        else:
            sql = f"SELECT * FROM {table} ORDER BY id DESC"

        rows = conn.execute(sql).fetchall()
        results = []
        for row in rows:
            record = dict(row)
            # Try to parse JSON fields back into Python objects
            for key, value in record.items():
                if isinstance(value, str):
                    try:
                        parsed = json.loads(value)
                        if isinstance(parsed, (list, dict)):
                            record[key] = parsed
                    except (json.JSONDecodeError, TypeError):
                        pass
            results.append(record)

        return {"status": "success", "count": len(results), "records": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()
