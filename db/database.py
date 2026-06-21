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
                patient_name TEXT,
                amount REAL,
                thumbnail_path TEXT,
                document_path TEXT,
                ocr_text TEXT,
                created_at TIMESTAMP
            );
            """
        )


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
                patient_name,
                amount,
                thumbnail_path,
                document_path,
                ocr_text,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                document.id,
                document.event_date,
                document.date_source,
                document.event_type,
                document.event_title,
                document.hospital_name,
                document.patient_name,
                document.amount,
                document.thumbnail_path,
                document.document_path,
                document.ocr_text,
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
                patient_name = ?,
                amount = ?,
                thumbnail_path = ?,
                document_path = ?,
                ocr_text = ?,
                created_at = ?
            WHERE id = ?;
            """,
            (
                document.event_date,
                document.date_source,
                document.event_type,
                document.event_title,
                document.hospital_name,
                document.patient_name,
                document.amount,
                document.thumbnail_path,
                document.document_path,
                document.ocr_text,
                document.created_at,
                document.id,
            ),
        )
