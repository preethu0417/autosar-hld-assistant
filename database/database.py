# database/database.py

from pathlib import Path
import sqlite3
import json
from datetime import datetime


class ArchitectureDatabase:
    """
    SQLite database layer for the AUTOSAR HLD Assistant.

    Stores:
    - Document metadata
    - Architecture query history
    - Revision comparison history
    """

    def __init__(self, database_path=None):

        if database_path is None:

            project_root = Path(__file__).resolve().parent.parent

            database_path = (
                project_root
                / "database"
                / "autosar_hld.db"
            )

        self.database_path = Path(database_path)

        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.initialize()

    # ========================================================
    # CONNECTION
    # ========================================================

    def connect(self):

        return sqlite3.connect(
            self.database_path
        )

    # ========================================================
    # INITIALIZE DATABASE
    # ========================================================

    def initialize(self):

        connection = self.connect()

        cursor = connection.cursor()

        # ----------------------------------------------------
        # DOCUMENTS
        # ----------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_name TEXT NOT NULL,
                document_path TEXT,
                version TEXT,
                status TEXT,
                page_count INTEGER,
                created_at TEXT NOT NULL
            )
            """
        )

        # ----------------------------------------------------
        # QUERY HISTORY
        # ----------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS query_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                intent TEXT,
                answer TEXT,
                evidence_count INTEGER DEFAULT 0,
                citation_count INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """
        )

        # ----------------------------------------------------
        # REVISION COMPARISON HISTORY
        # ----------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS comparison_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                old_document TEXT,
                new_document TEXT,
                added_count INTEGER DEFAULT 0,
                removed_count INTEGER DEFAULT 0,
                changed_count INTEGER DEFAULT 0,
                unchanged_count INTEGER DEFAULT 0,
                comparison_json TEXT,
                created_at TEXT NOT NULL
            )
            """
        )

        connection.commit()
        connection.close()

    # ========================================================
    # DOCUMENT
    # ========================================================

    def add_document(
        self,
        document_name,
        document_path=None,
        version=None,
        status=None,
        page_count=None
    ):

        connection = self.connect()

        cursor = connection.cursor()

        created_at = datetime.now().isoformat()

        cursor.execute(
            """
            INSERT INTO documents (
                document_name,
                document_path,
                version,
                status,
                page_count,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                document_name,
                document_path,
                version,
                status,
                page_count,
                created_at
            )
        )

        document_id = cursor.lastrowid

        connection.commit()
        connection.close()

        return document_id

    def get_documents(self):

        connection = self.connect()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                document_name,
                document_path,
                version,
                status,
                page_count,
                created_at
            FROM documents
            ORDER BY id DESC
            """
        )

        rows = cursor.fetchall()

        connection.close()

        columns = [
            "id",
            "document_name",
            "document_path",
            "version",
            "status",
            "page_count",
            "created_at"
        ]

        return [
            dict(zip(columns, row))
            for row in rows
        ]

    # ========================================================
    # QUERY HISTORY
    # ========================================================

    def add_query(
        self,
        question,
        intent,
        answer,
        evidence_count=0,
        citation_count=0
    ):

        connection = self.connect()

        cursor = connection.cursor()

        created_at = datetime.now().isoformat()

        cursor.execute(
            """
            INSERT INTO query_history (
                question,
                intent,
                answer,
                evidence_count,
                citation_count,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                question,
                intent,
                answer,
                evidence_count,
                citation_count,
                created_at
            )
        )

        query_id = cursor.lastrowid

        connection.commit()
        connection.close()

        return query_id

    def get_query_history(
        self,
        limit=50
    ):

        connection = self.connect()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                question,
                intent,
                answer,
                evidence_count,
                citation_count,
                created_at
            FROM query_history
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,)
        )

        rows = cursor.fetchall()

        connection.close()

        columns = [
            "id",
            "question",
            "intent",
            "answer",
            "evidence_count",
            "citation_count",
            "created_at"
        ]

        return [
            dict(zip(columns, row))
            for row in rows
        ]

    # ========================================================
    # COMPARISON HISTORY
    # ========================================================

    def add_comparison(
        self,
        old_document,
        new_document,
        comparison
    ):

        summary = comparison.get(
            "summary",
            {}
        )

        overall = summary.get(
            "overall",
            {}
        )

        added = overall.get(
            "added",
            0
        )

        removed = overall.get(
            "removed",
            0
        )

        changed = overall.get(
            "changed",
            0
        )

        unchanged = overall.get(
            "unchanged",
            0
        )

        connection = self.connect()

        cursor = connection.cursor()

        created_at = datetime.now().isoformat()

        cursor.execute(
            """
            INSERT INTO comparison_history (
                old_document,
                new_document,
                added_count,
                removed_count,
                changed_count,
                unchanged_count,
                comparison_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                old_document,
                new_document,
                added,
                removed,
                changed,
                unchanged,
                json.dumps(
                    comparison,
                    ensure_ascii=False
                ),
                created_at
            )
        )

        comparison_id = cursor.lastrowid

        connection.commit()
        connection.close()

        return comparison_id

    def get_comparison_history(
        self,
        limit=50
    ):

        connection = self.connect()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                old_document,
                new_document,
                added_count,
                removed_count,
                changed_count,
                unchanged_count,
                comparison_json,
                created_at
            FROM comparison_history
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,)
        )

        rows = cursor.fetchall()

        connection.close()

        columns = [
            "id",
            "old_document",
            "new_document",
            "added_count",
            "removed_count",
            "changed_count",
            "unchanged_count",
            "comparison_json",
            "created_at"
        ]

        results = []

        for row in rows:

            record = dict(
                zip(
                    columns,
                    row
                )
            )

            try:

                record["comparison"] = json.loads(
                    record["comparison_json"]
                )

            except Exception:

                record["comparison"] = {}

            del record["comparison_json"]

            results.append(record)

        return results

    # ========================================================
    # DATABASE HEALTH
    # ========================================================

    def health_check(self):

        connection = self.connect()

        cursor = connection.cursor()

        cursor.execute(
            "SELECT 1"
        )

        result = cursor.fetchone()

        connection.close()

        return result == (1,)