import sqlite3
from pathlib import Path

from models.document import Document


BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "meditrackk.db"


def get_connection() -> sqlite3.Connection:
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                event_date TEXT,
                date_source TEXT,
                event_type TEXT,
                event_title TEXT,
                hospital_name TEXT,
                provider_city TEXT,
                normalized_provider TEXT,
                patient_name TEXT,
                amount REAL,
                thumbnail_path TEXT,
                document_path TEXT,
                ocr_text TEXT,
                conditions TEXT,
                test_results TEXT,
                document_hash TEXT,
                duplicate_key TEXT,
                source_file_name TEXT,
                page_number INTEGER,
                created_at TIMESTAMP
            );
            """
        )
        _ensure_columns(connection)


def _ensure_columns(connection: sqlite3.Connection) -> None:
    cursor = connection.execute("PRAGMA table_info(documents);")
    existing = {row["name"] for row in cursor.fetchall()}
    columns = {
        "provider_city": "TEXT",
        "normalized_provider": "TEXT",
        "conditions": "TEXT",
        "test_results": "TEXT",
        "document_hash": "TEXT",
        "duplicate_key": "TEXT",
        "source_file_name": "TEXT",
        "page_number": "INTEGER",
    }
    for name, column_type in columns.items():
        if name not in existing:
            connection.execute(f"ALTER TABLE documents ADD COLUMN {name} {column_type};")


def insert_document(document: Document) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO documents (
                id,
                event_date,
                date_source,
                event_type,
                event_title,
                hospital_name,
                provider_city,
                normalized_provider,
                patient_name,
                amount,
                thumbnail_path,
                document_path,
                ocr_text,
                conditions,
                test_results,
                document_hash,
                duplicate_key,
                source_file_name,
                page_number,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                document.id,
                document.event_date,
                document.date_source,
                document.event_type,
                document.event_title,
                document.hospital_name,
                document.provider_city,
                document.normalized_provider,
                document.patient_name,
                document.amount,
                document.thumbnail_path,
                document.document_path,
                document.ocr_text,
                document.conditions,
                document.test_results,
                document.document_hash,
                document.duplicate_key,
                document.source_file_name,
                document.page_number,
                document.created_at,
            ),
        )


def fetch_documents() -> list[sqlite3.Row]:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT *
            FROM documents
            ORDER BY event_date ASC, created_at ASC;
            """
        )
        return list(cursor.fetchall())


def fetch_document(document_id: str) -> sqlite3.Row | None:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT *
            FROM documents
            WHERE id = ?;
            """,
            (document_id,),
        )
        return cursor.fetchone()


def update_document(document: Document) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE documents
            SET
                event_date = ?,
                date_source = ?,
                event_type = ?,
                event_title = ?,
                hospital_name = ?,
                provider_city = ?,
                normalized_provider = ?,
                patient_name = ?,
                amount = ?,
                thumbnail_path = ?,
                document_path = ?,
                ocr_text = ?,
                conditions = ?,
                test_results = ?,
                document_hash = ?,
                duplicate_key = ?,
                source_file_name = ?,
                page_number = ?,
                created_at = ?
            WHERE id = ?;
            """,
            (
                document.event_date,
                document.date_source,
                document.event_type,
                document.event_title,
                document.hospital_name,
                document.provider_city,
                document.normalized_provider,
                document.patient_name,
                document.amount,
                document.thumbnail_path,
                document.document_path,
                document.ocr_text,
                document.conditions,
                document.test_results,
                document.document_hash,
                document.duplicate_key,
                document.source_file_name,
                document.page_number,
                document.created_at,
                document.id,
            ),
        )


def find_duplicates(duplicate_key: str, document_hash: str) -> list[sqlite3.Row]:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT *
            FROM documents
            WHERE duplicate_key = ?
               OR (document_hash IS NOT NULL AND document_hash = ?);
            """,
            (duplicate_key, document_hash),
        )
        return list(cursor.fetchall())


def delete_document(document_id: str) -> None:
    with get_connection() as connection:
        connection.execute("DELETE FROM documents WHERE id = ?;", (document_id,))
