# db.py
import sqlite3
import os

DB_PATH = "database.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            class TEXT,
            section TEXT,
            image_path TEXT,
            qr_path TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            date TEXT,
            status TEXT,
            UNIQUE(student_id, date)
        )
    """)
    conn.commit()
    conn.close()

def add_student(name, class_name, section, image_path, qr_path=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO students (name, class, section, image_path, qr_path) VALUES (?, ?, ?, ?, ?)",
              (name, class_name, section, image_path, qr_path))
    student_id = c.lastrowid
    conn.commit()
    conn.close()
    return student_id

def get_students(class_name=None, section=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if class_name and section:
        c.execute("SELECT id, name, image_path FROM students WHERE class=? AND section=? ORDER BY id", (class_name, section))
    else:
        c.execute("SELECT id, name, image_path FROM students ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return rows

def get_student_by_id(student_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, class, section, image_path, qr_path FROM students WHERE id=?", (student_id,))
    row = c.fetchone()
    conn.close()
    return row

def mark_attendance(student_id, date, status="Present"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id FROM attendance WHERE student_id=? AND date=?", (student_id, date))
    r = c.fetchone()
    if r:
        c.execute("UPDATE attendance SET status=? WHERE student_id=? AND date=?", (status, student_id, date))
    else:
        c.execute("INSERT INTO attendance (student_id, date, status) VALUES (?, ?, ?)", (student_id, date, status))
    conn.commit()
    conn.close()

def get_attendance_report(class_name, section, date):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # left join students with attendance for the date
    c.execute("""
        SELECT s.id, s.name, COALESCE(a.status, 'Absent') as status
        FROM students s
        LEFT JOIN attendance a ON s.id = a.student_id AND a.date = ?
        WHERE s.class = ? AND s.section = ?
        ORDER BY s.id
    """, (date, class_name, section))
    rows = c.fetchall()
    conn.close()
    return rows

def get_monthly_report(class_name, section, month_prefix):
    # month_prefix like "2025-09" to get YYYY-MM records
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # basic aggregation: present count per student for the month
    c.execute("""
        SELECT s.id, s.name,
               SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) as presents,
               COUNT(a.date) as total_marked
        FROM students s
        LEFT JOIN attendance a ON s.id = a.student_id AND a.date LIKE ?
        WHERE s.class = ? AND s.section = ?
        GROUP BY s.id, s.name
        ORDER BY s.id
    """, (f"{month_prefix}%", class_name, section))
    rows = c.fetchall()
    conn.close()
    return rows
