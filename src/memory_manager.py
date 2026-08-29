from datetime import datetime
import json
import os
import sqlite3

DATABASE_PATH = "data/credit_memory.db"
print("DATABASE PATH:", os.path.abspath(DATABASE_PATH))


class MemoryManager:
    """Manage long-term memory storage using SQLite database."""

    def __init__(self):
        # اطمینان از وجود پوشه data قبل از اتصال به دیتابیس
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        self.create_memory_table()

    def get_connection(self):
        """Create database connection."""
        return sqlite3.connect(DATABASE_PATH)

    def create_memory_table(self):
        """Create memory table if it does not exist."""
        connection = self.get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS company_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT,
                memory_type TEXT,
                memory_content TEXT,
                created_at TEXT
            )
            """
        )

        connection.commit()
        connection.close()

    def save_memory(self, company_name, memory_type, memory_content):
        """Store important company information permanently.

        اگر آخرین رکورد همین شرکت، محتوای یکسانی داشته باشد،
          رکورد تکراری جدید ذخیره نمی‌شود.
        """
        connection = self.get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT memory_content FROM company_memory
            WHERE company_name = ? AND memory_type = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (company_name, memory_type),
        )
        last_record = cursor.fetchone()

        if last_record and last_record[0] == memory_content:
            connection.close()
            return  # محتوا تغییری نکرده، رکورد تکراری ذخیره نشود

        cursor.execute(
            """
            INSERT INTO company_memory
            (company_name, memory_type, memory_content, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                company_name,
                memory_type,
                memory_content,
                datetime.now().isoformat(),
            ),
        )

        connection.commit()
        connection.close()

    def get_company_memory(self, company_name):
        """Retrieve previous memories of a company."""
        connection = self.get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                memory_type,
                memory_content,
                created_at
            FROM company_memory
            WHERE company_name = ?
            ORDER BY created_at DESC
            """,
            (company_name,),
        )

        memories = cursor.fetchall()
        connection.close()

        return memories

    def get_latest_memory_summary(self, company_name):
        """Parse raw memory entries and return a clean, readable summary of the

        most recent analysis.
        """
        raw_memories = self.get_company_memory(company_name)

        if not raw_memories:
            return "هیچ تحلیل قبلی برای این شرکت یافت نشد."

        # Latest entry is first due to ORDER BY created_at DESC
        memory_type, json_string, date_str = raw_memories[0]

        try:
            data = json.loads(json_string)
        except json.JSONDecodeError:
            return f"تحلیل قبلی ({date_str}): داده نامعتبر."

        decision = data.get("decision", "نامشخص")
        risk_level = data.get("risk_level", "نامشخص")
        summary = data.get("summary") or data.get(
            "executive_summary", "بدون خلاصه"
        )

        readable = (
            f"تحلیل قبلی شرکت {company_name} ({date_str}):\n"
            f"- تصمیم: {decision}\n"
            f"- سطح ریسک: {risk_level}\n"
            f"- خلاصه: {summary}"
        )

        return readable

    def clear_memory(self):
        """Remove all stored memories."""
        connection = self.get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM company_memory
            """
        )

        connection.commit()
        connection.close()
