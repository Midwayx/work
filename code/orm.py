import sqlite3

conn = sqlite3.connect("mydatabase.db")

cur = conn.cursor()

cur.execute(
    """CREATE TABLE IF NOT EXISTS test1(
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            file_name TEXT,
            is_created INTEGER,
            is_modified INTEGER,
            is_deleted INTEGER,
            is_moved INTEGER,
            time TEXT,
            is_directory INTEGER);"""
)

conn.commit()
cur.execute(
    """CREATE TABLE IF NOT EXISTS config(
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            file_name TEXT,
            md5 TEXT,
            time TEXT,
            is_directory INTEGER);"""
)

conn.commit()
#cur.execute("""ALTER TABLE CONFIG ADD COLUMN event_type integer""")

# cur.execute(
#     """CREATE TABLE IF NOT EXISTS watched_files(
#             id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
#             ghost TEXT,
#             file_name TEXT,
#             md5 TEXT,
#             time FLOAT,
#             is_directory INTEGER);"""
# )
cur.execute(
    """CREATE TABLE IF NOT EXISTS ghosts(
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            name TEXT UNIQUE NOT NULL,
            ip TEXT UNIQUE NOT NULL,
            time FLOAT);"""
)
conn.commit()

cur.execute(
    """CREATE TABLE IF NOT EXISTS watched_files(
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            ghost TEXT NOT NULL,
            path TEXT NOT NULL,
            md5 TEXT NOT NULL,
            time FLOAT);"""
)
conn.commit()

cur.execute(
    """CREATE TABLE IF NOT EXISTS events(
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            ghost TEXT NOT NULL,
            file TEXT NOT NULL,
            md5 TEXT NOT NULL,
            time FLOAT,
            event_type INTEGER);"""

)
# data = ('ghost1', '//home/dmitry/spam/12.txt')
# cur.execute("DELETE FROM watched_files WHERE name=? AND path=?",data)
conn.commit()