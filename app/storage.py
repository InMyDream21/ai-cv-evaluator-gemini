import sqlite3, json, time
from typing import Optional, Tuple

def get_conn(db_path: str = "local.db") -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_db(db_path: str = "local.db"):
    conn = get_conn(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS uploads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cv_text TEXT,
        project_text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        upload_id INTEGER,
        status TEXT,
        result_json TEXT,
        error TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS embeddings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        namespace TEXT, -- 'job: cv', 'job:project', 'rubric:cv', 'rubric:project'
        chunk_id TEXT,
        text TEXT,
        vector BLOB -- np.float32 bytes
    );
    """)
    conn.commit()
    return conn

def insert_upload(conn: sqlite3.Connection, cv_text: str, project_text: str) -> int:
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO uploads (cv_text, project_text) VALUES (?, ?)
    """, (cv_text, project_text))
    conn.commit()
    if cursor.lastrowid is None:
        raise ValueError("Failed to retrieve lastrowid after job creation.")
    return cursor.lastrowid

def create_job(conn: sqlite3.Connection, upload_id: int) -> int:
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO jobs (upload_id, status, result_json, error) VALUES (?, 'queued', NULL, NULL)
    """, (upload_id,))
    conn.commit()
    if cursor.lastrowid is None:
        raise ValueError("Failed to retrieve lastrowid after job creation.")
    return cursor.lastrowid

def update_job_status(conn: sqlite3.Connection, job_id: int, status: str, result: Optional[dict] = None, error: Optional[str] = None):
    cursor = conn.cursor()
    result_json = json.dumps(result) if result else None
    cursor.execute("""
    UPDATE jobs SET status = ?, result_json = ?, error = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
    """, (status, result_json, error, job_id))
    conn.commit()

def get_job(conn: sqlite3.Connection, job_id: int) -> Optional[Tuple]:
    cursor = conn.cursor()
    cursor.execute("SELECT id, upload_id, status, result_json, error FROM jobs WHERE id = ?", (job_id,))
    return cursor.fetchone()

def get_upload(conn: sqlite3.Connection, upload_id: int) -> Optional[Tuple]:
    cursor = conn.cursor()
    cursor.execute("SELECT id, cv_text, project_text FROM uploads WHERE id = ?", (upload_id,))
    return cursor.fetchone()

def upsert_embedding(conn: sqlite3.Connection, namespace: str, chunk_id: str, text: str, vector: bytes):
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO embeddings (namespace, chunk_id, text, vector) VALUES (?, ?, ?, ?)
    """, (namespace, chunk_id, text, vector))
    conn.commit()

def get_embeddings_by_namespace(conn: sqlite3.Connection, namespace: str) -> list:
    cursor = conn.cursor()
    cursor.execute("SELECT chunk_id, text, vector FROM embeddings WHERE namespace = ?", (namespace,))
    return cursor.fetchall()