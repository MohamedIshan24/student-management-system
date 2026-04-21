import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    reg_no TEXT,
    email TEXT,
    nic TEXT,
    address TEXT,
    course TEXT,
    father_name TEXT,
    mother_name TEXT,
    religion TEXT,
    sports TEXT,
    photo TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT,
    role TEXT,
    student_id INTEGER
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT
)
''')

# 🆕 Modules (belongs to a course)
cursor.execute('''
CREATE TABLE IF NOT EXISTS modules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    FOREIGN KEY (course_id) REFERENCES courses(id)
)
''')

# 🆕 Subjects (belongs to a module)
cursor.execute('''
CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    FOREIGN KEY (module_id) REFERENCES modules(id)
)
''')

# 🆕 Materials (belongs to a subject)
cursor.execute('''
CREATE TABLE IF NOT EXISTS materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    filename TEXT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(id)
)
''')

# 🆕 Grades (student + subject + grade)
cursor.execute('''
CREATE TABLE IF NOT EXISTS grades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    subject_id INTEGER NOT NULL,
    grade TEXT,
    marks INTEGER,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (subject_id) REFERENCES subjects(id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS announcements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    type TEXT NOT NULL,
    course_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    date TEXT,
    status TEXT
)
''')

# ✅ Insert Admin only if not exists
cursor.execute("SELECT * FROM users WHERE username = 'admin'")
if not cursor.fetchone():
    cursor.execute(
        "INSERT INTO users (username, password, role, student_id) VALUES (?, ?, ?, ?)",
        ("admin", generate_password_hash("1234"), "admin", None)
    )

# ✅ Update courses — delete old, insert new
cursor.execute("DELETE FROM courses")
cursor.executemany(
    "INSERT INTO courses (name, description) VALUES (?, ?)",
    [
        ("Computer Science", "Computer Science"),
        ("Software Engineering", "Software Engineering"),
        ("Information Systems", "Information Systems"),
        ("Information Technology", "Information Technology"),
        ("Data Science", "Data Science"),
        ("Artificial Intelligence", "Artificial Intelligence"),
    ]
)

conn.commit()
conn.close()

print("Database updated successfully!")