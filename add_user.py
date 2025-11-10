# add_user.py
import sqlite3

DB_NAME = "learnlangbot.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Agar jadval mavjud bo‘lmasa yaratadi
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def add_user(user_id: int, username: str, full_name: str):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        INSERT OR REPLACE INTO users (id, username, full_name)
        VALUES (?, ?, ?)
    """, (user_id, username, full_name))

    conn.commit()
    conn.close()
    print(f"[+] User qo'shildi: {username} ({full_name})")


if __name__ == "__main__":
    init_db()
    add_user(
        user_id=999999,
        username="demo_user",
        full_name="Demo User"
    )
