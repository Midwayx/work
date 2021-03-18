import sqlite3

conn = sqlite3.connect('mydatabase.db')

cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS test1(
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            file_name TEXT,
            is_created INTEGER,
            is_modified INTEGER,
            is_deleted INTEGER,
            is_moved INTEGER,
            time TEXT,
            is_directory INTEGER);""")

conn.commit()
cur.execute("""CREATE TABLE IF NOT EXISTS config(
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            file_name TEXT,
            md5 TEXT,
            time TEXT,
            is_directory INTEGER);""")

conn.commit()
cur.execute("""ALTER TABLE CONFIG ADD COLUMN event_type integer""")

