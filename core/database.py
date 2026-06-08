import sqlite3
import time

DB_NAME = "factory.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp REAL,
        defects INTEGER,
        machine_load INTEGER,
        decision TEXT
    )
    """)

    conn.commit()
    conn.close()


def insert_log(defects, load, decision):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    INSERT INTO logs (timestamp, defects, machine_load, decision)
    VALUES (?, ?, ?, ?)
    """, (time.time(), len(defects), load, decision))

    conn.commit()
    conn.close()