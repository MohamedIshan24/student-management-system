import csv
from flask import Response
from flask import Flask, redirect, render_template, request, session, flash
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'secret123'

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# 🏠 HOME
@app.route('/')
def home():
    if 'user' in session:
        if session.get('role') == 'admin':
            return redirect('/students')
        else:
            return redirect(f"/student/{session.get('student_id')}")
    return render_template('login.html')


# 🔐 LOGIN
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    conn.close()

    if user and check_password_hash(user[2], password):
        session['user'] = username
        session['role'] = user[3]
        session['student_id'] = user[4]

        if user[3] == 'admin':
            return redirect('/students')
        else:
            return redirect(f"/student/{user[4]}")
    else:
        flash("Invalid username or password", "danger")
        return redirect('/')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    username = request.form['username']
    password = generate_password_hash(request.form['password'])
    name = request.form['name']
    email = request.form['email']
    reg_no = request.form['reg_no']

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # ❌ Check if username exists
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return "Username already exists"

    # ✅ Insert into students table first
    cursor.execute("""
    INSERT INTO students (name, reg_no, email)
    VALUES (?, ?, ?)
    """, (name, reg_no, email))

    student_id = cursor.lastrowid

    # ✅ Insert into users table
    cursor.execute("""
    INSERT INTO users (username, password, role, student_id)
    VALUES (?, ?, ?, ?)
    """, (username, password, "student", student_id))

    conn.commit()
    conn.close()

    return redirect('/')

# 🚪 LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ➕ ADD STUDENT (ADMIN ONLY)
@app.route('/add', methods=['POST'])
def add_student():
    if session.get('role') != 'admin':
        return "Access Denied"

    name = request.form['name']
    reg_no = request.form['reg_no']
    email = request.form['email']
    nic = request.form['nic']
    address = request.form['address']
    course = request.form['course']
    father_name = request.form['father_name']
    mother_name = request.form['mother_name']
    religion = request.form['religion']
    sports = request.form['sports']

    photo = request.files['photo']
    filename = photo.filename if photo else ""

    if filename:
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        photo.save(photo_path)

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO students
    (name, reg_no, email, nic, address, course, father_name, mother_name, religion, sports, photo)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, reg_no, email, nic, address, course,
          father_name, mother_name, religion, sports, filename))

    conn.commit()
    conn.close()
    flash("Student added successfully!", "success")
    return redirect('/students')

@app.route('/students')
def students():
    if session.get('role') != 'admin':
        return "Access Denied"

    search = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    per_page = 5   # number of students per page
    offset = (page - 1) * per_page

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    if search:
        cursor.execute("""
        SELECT * FROM students
        WHERE name LIKE ? OR reg_no LIKE ? OR course LIKE ?
        LIMIT ? OFFSET ?
        """, ('%' + search + '%', '%' + search + '%', '%' + search + '%', per_page, offset))

        cursor.execute("""
        SELECT COUNT(*) FROM students
        WHERE name LIKE ? OR reg_no LIKE ? OR course LIKE ?
        """, ('%' + search + '%', '%' + search + '%', '%' + search + '%'))

    else:
        cursor.execute("SELECT * FROM students LIMIT ? OFFSET ?", (per_page, offset))
        data = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) FROM students")

    total = cursor.fetchone()[0]
    conn.close()

    pages = (total // per_page) + (1 if total % per_page else 0)

    conn2 = sqlite3.connect('database.db')
    cursor2 = conn2.cursor()
    cursor2.execute("SELECT * FROM courses")
    courses = cursor2.fetchall()
    conn2.close()

    return render_template(
        'students.html',
        students=data,
        count=total,
        page=page,
        pages=pages,
        search=search,
        courses=courses
    )

# ❌ DELETE (ADMIN ONLY)
@app.route('/delete/<int:id>')
def delete_student(id):
    if session.get('role') != 'admin':
        return "Access Denied"

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("DELETE FROM students WHERE id = ?", (id,))

    conn.commit()
    conn.close()
    flash("Student deleted successfully!", "danger")
    return redirect('/students')


# ✏️ EDIT (ADMIN ONLY)
@app.route('/edit/<int:id>')
def edit_student(id):
    if session.get('role') != 'admin':
        return "Access Denied"

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students WHERE id = ?", (id,))
    student = cursor.fetchone()

    # Get courses for dropdown
    cursor.execute("SELECT * FROM courses")
    courses = cursor.fetchall()

    conn.close()

    return render_template('edit.html', student=student, courses=courses)

# 🔄 UPDATE (ADMIN ONLY)
@app.route('/update/<int:id>', methods=['POST'])
def update_student(id):
    if session.get('role') != 'admin':
        return "Access Denied"

    name = request.form['name']
    reg_no = request.form['reg_no']
    email = request.form['email']
    nic = request.form['nic']
    address = request.form['address']
    course = request.form['course']
    father_name = request.form['father_name']
    mother_name = request.form['mother_name']
    religion = request.form['religion']
    sports = request.form['sports']

    photo = request.files['photo']
    filename = photo.filename if photo else ""

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    if filename:
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        photo.save(photo_path)

        cursor.execute("""
        UPDATE students SET
        name=?, reg_no=?, email=?, nic=?, address=?, course=?,
        father_name=?, mother_name=?, religion=?, sports=?, photo=?
        WHERE id=?
        """, (name, reg_no, email, nic, address, course,
              father_name, mother_name, religion, sports, filename, id))
    else:
        cursor.execute("""
        UPDATE students SET
        name=?, reg_no=?, email=?, nic=?, address=?, course=?,
        father_name=?, mother_name=?, religion=?, sports=?
        WHERE id=?
        """, (name, reg_no, email, nic, address, course,
              father_name, mother_name, religion, sports, id))

    conn.commit()
    conn.close()

    return redirect('/students')


# 👨‍🎓 STUDENT PROFILE
@app.route('/student/<int:id>')
def student_profile(id):
    if 'user' not in session:
        return redirect('/')

    if session.get('role') == 'student':
        if session.get('student_id') != id:
            return "Access Denied"

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students WHERE id = ?", (id,))
    student = cursor.fetchone()

    # Get unread announcements count
    course_name = student[6]
    cursor.execute("SELECT id FROM courses WHERE name = ?", (course_name,))
    course = cursor.fetchone()
    course_id = course[0] if course else None

    cursor.execute("""
        SELECT COUNT(*) FROM announcements
        WHERE type = 'general'
        OR (type = 'course' AND course_id = ?)
    """, (course_id,))
    ann_count = cursor.fetchone()[0]

    conn.close()

    return render_template('profile.html', student=student, ann_count=ann_count)

@app.route('/student/edit/<int:id>')
def student_edit(id):
    if 'user' not in session:
        return redirect('/')

    if session.get('role') == 'student':
        if session.get('student_id') != id:
            return "Access Denied"

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students WHERE id = ?", (id,))
    student = cursor.fetchone()

    cursor.execute("SELECT * FROM courses")
    courses = cursor.fetchall()

    conn.close()

    return render_template('student_edit.html', student=student, courses=courses)

@app.route('/student/update/<int:id>', methods=['POST'])
def student_update(id):
    if 'user' not in session:
        return redirect('/')

    if session.get('role') == 'student':
        if session.get('student_id') != id:
            return "Access Denied"

    name = request.form['name']
    email = request.form['email']
    nic = request.form['nic']
    address = request.form['address']
    course = request.form['course']
    father_name = request.form['father_name']
    mother_name = request.form['mother_name']
    religion = request.form['religion']
    sports = request.form['sports']

    photo = request.files.get('photo')
    filename = photo.filename if photo else ""

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    if filename:
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        photo.save(photo_path)
        cursor.execute("""
        UPDATE students SET name=?, email=?, nic=?, address=?, course=?,
        father_name=?, mother_name=?, religion=?, sports=?, photo=?
        WHERE id=?
        """, (name, email, nic, address, course,
              father_name, mother_name, religion, sports, filename, id))
    else:
        cursor.execute("""
        UPDATE students SET name=?, email=?, nic=?, address=?, course=?,
        father_name=?, mother_name=?, religion=?, sports=?
        WHERE id=?
        """, (name, email, nic, address, course,
              father_name, mother_name, religion, sports, id))

    conn.commit()
    conn.close()
    flash("Profile updated successfully!", "success")
    return redirect(f"/student/{id}")

@app.route('/dashboard')
def dashboard():
    if session.get('role') != 'admin':
        return "Access Denied"

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Total students
    cursor.execute("SELECT COUNT(*) FROM students")
    total = cursor.fetchone()[0]

    # Course-wise count
    cursor.execute("""
    SELECT course, COUNT(*)
    FROM students
    WHERE course IS NOT NULL AND course != ''
    GROUP BY course
    """)
    course_data = cursor.fetchall()

    # Recent 5 students
    cursor.execute("SELECT * FROM students ORDER BY id DESC LIMIT 5")
    recent_students = cursor.fetchall()

    conn.close()

    return render_template('dashboard.html',
                           total=total,
                           courses=course_data,
                           recent_students=recent_students)

@app.route('/export')
def export_students():
    if session.get('role') != 'admin':
        return "Access Denied"

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students")
    data = cursor.fetchall()

    conn.close()

    def generate():
        yield 'ID,Name,Reg No,Email,NIC,Address,Course,Father,Mother,Religion,Sports\n'
        for s in data:
            yield f"{s[0]},{s[1]},{s[2]},{s[3]},{s[4]},{s[5]},{s[6]},{s[7]},{s[8]},{s[9]},{s[10]}\n"

    return Response(generate(), mimetype='text/csv',
                    headers={"Content-Disposition": "attachment;filename=students.csv"})

# 🔒 CHANGE PASSWORD (STUDENT ONLY)
@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user' not in session:
        return redirect('/')

    error = None
    success = None

    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        # Get user from database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (session['user'],))
        user = cursor.fetchone()
        conn.close()

        # Check current password
        if not check_password_hash(user[2], current_password):
            error = "Current password is incorrect!"

        # Check new passwords match
        elif new_password != confirm_password:
            error = "New passwords do not match!"

        # Check length
        elif len(new_password) < 6:
            error = "Password must be at least 6 characters!"

        else:
            # Save hashed new password
            hashed = generate_password_hash(new_password)
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET password = ? WHERE username = ?",
                           (hashed, session['user']))
            conn.commit()
            conn.close()
            success = "Password changed successfully!"

    return render_template('change_password.html', error=error, success=success)

# 📚 VIEW ALL COURSES (ADMIN)
@app.route('/courses')
def courses():
    if session.get('role') != 'admin':
        return "Access Denied"

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM courses")
    courses = cursor.fetchall()
    conn.close()

    return render_template('courses.html', courses=courses)


# ➕ ADD COURSE (ADMIN)
@app.route('/course/add', methods=['POST'])
def add_course():
    if session.get('role') != 'admin':
        return "Access Denied"

    name = request.form['name']
    description = request.form['description']

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO courses (name, description) VALUES (?, ?)",
                   (name, description))
    conn.commit()
    conn.close()

    flash("Course added successfully!", "success")
    return redirect('/courses')


# ❌ DELETE COURSE (ADMIN)
@app.route('/course/delete/<int:id>')
def delete_course(id):
    if session.get('role') != 'admin':
        return "Access Denied"

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM courses WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    flash("Course deleted!", "danger")
    return redirect('/courses')

# 🔑 RESET STUDENT PASSWORD (ADMIN ONLY)
@app.route('/reset_password/<int:student_id>', methods=['GET', 'POST'])
def reset_password(student_id):
    if session.get('role') != 'admin':
        return "Access Denied"

    error = None

    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            error = "Passwords do not match!"
        elif len(new_password) < 6:
            error = "Password must be at least 6 characters!"
        else:
            hashed = generate_password_hash(new_password)
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET password = ? WHERE student_id = ?",
                           (hashed, student_id))
            conn.commit()
            conn.close()
            flash("Password reset successfully!", "success")
            return redirect('/students')

    # Get student name to show on page
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM students WHERE id = ?", (student_id,))
    student = cursor.fetchone()
    conn.close()

    return render_template('reset_password.html',
                           student=student,
                           student_id=student_id,
                           error=error)

# 📚 VIEW MODULES (ADMIN)
@app.route('/course/<int:course_id>/modules')
def modules(course_id):
    if session.get('role') != 'admin':
        return "Access Denied"

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM courses WHERE id = ?", (course_id,))
    course = cursor.fetchone()

    cursor.execute("SELECT * FROM modules WHERE course_id = ?", (course_id,))
    modules = cursor.fetchall()

    conn.close()

    return render_template('modules.html', course=course, modules=modules)


# ➕ ADD MODULE (ADMIN)
@app.route('/course/<int:course_id>/module/add', methods=['POST'])
def add_module(course_id):
    if session.get('role') != 'admin':
        return "Access Denied"

    name = request.form['name']
    description = request.form['description']

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO modules (course_id, name, description) VALUES (?, ?, ?)",
                   (course_id, name, description))
    conn.commit()
    conn.close()

    flash("Module added successfully!", "success")
    return redirect(f"/course/{course_id}/modules")


# ❌ DELETE MODULE (ADMIN)
@app.route('/module/delete/<int:module_id>')
def delete_module(module_id):
    if session.get('role') != 'admin':
        return "Access Denied"

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Get course_id before deleting
    cursor.execute("SELECT course_id FROM modules WHERE id = ?", (module_id,))
    module = cursor.fetchone()
    course_id = module[0]

    cursor.execute("DELETE FROM modules WHERE id = ?", (module_id,))
    conn.commit()
    conn.close()

    flash("Module deleted!", "danger")
    return redirect(f"/course/{course_id}/modules")

# 📝 VIEW SUBJECTS (ADMIN)
@app.route('/module/<int:module_id>/subjects')
def subjects(module_id):
    if session.get('role') != 'admin':
        return "Access Denied"

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM modules WHERE id = ?", (module_id,))
    module = cursor.fetchone()

    cursor.execute("SELECT * FROM courses WHERE id = ?", (module[1],))
    course = cursor.fetchone()

    cursor.execute("SELECT * FROM subjects WHERE module_id = ?", (module_id,))
    subjects = cursor.fetchall()

    conn.close()

    return render_template('subjects.html',
                           module=module,
                           course=course,
                           subjects=subjects)


# ➕ ADD SUBJECT (ADMIN)
@app.route('/module/<int:module_id>/subject/add', methods=['POST'])
def add_subject(module_id):
    if session.get('role') != 'admin':
        return "Access Denied"

    name = request.form['name']
    description = request.form['description']

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO subjects (module_id, name, description) VALUES (?, ?, ?)",
                   (module_id, name, description))
    conn.commit()
    conn.close()

    flash("Subject added successfully!", "success")
    return redirect(f"/module/{module_id}/subjects")


# ❌ DELETE SUBJECT (ADMIN)
@app.route('/subject/delete/<int:subject_id>')
def delete_subject(subject_id):
    if session.get('role') != 'admin':
        return "Access Denied"

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT module_id FROM subjects WHERE id = ?", (subject_id,))
    subject = cursor.fetchone()
    module_id = subject[0]

    cursor.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
    conn.commit()
    conn.close()

    flash("Subject deleted!", "danger")
    return redirect(f"/module/{module_id}/subjects")

# 📄 VIEW MATERIALS (ADMIN)
@app.route('/subject/<int:subject_id>/materials')
def materials(subject_id):
    if session.get('role') != 'admin':
        return "Access Denied"

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM subjects WHERE id = ?", (subject_id,))
    subject = cursor.fetchone()

    cursor.execute("SELECT * FROM modules WHERE id = ?", (subject[1],))
    module = cursor.fetchone()

    cursor.execute("SELECT * FROM courses WHERE id = ?", (module[1],))
    course = cursor.fetchone()

    cursor.execute("SELECT * FROM materials WHERE subject_id = ?", (subject_id,))
    materials = cursor.fetchall()

    conn.close()

    return render_template('materials.html',
                           subject=subject,
                           module=module,
                           course=course,
                           materials=materials)


# ➕ UPLOAD MATERIAL (ADMIN)
@app.route('/subject/<int:subject_id>/material/add', methods=['POST'])
def add_material(subject_id):
    if session.get('role') != 'admin':
        return "Access Denied"

    title = request.form['title']
    file = request.files.get('file')
    filename = ""

    if file and file.filename:
        filename = file.filename
        os.makedirs('static/materials', exist_ok=True)
        file_path = os.path.join('static/materials', filename)
        file.save(file_path)

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO materials (subject_id, title, filename) VALUES (?, ?, ?)",
                   (subject_id, title, filename))
    conn.commit()
    conn.close()

    flash("Material uploaded successfully!", "success")
    return redirect(f"/subject/{subject_id}/materials")

# ❌ DELETE MATERIAL (ADMIN)
@app.route('/material/delete/<int:material_id>')
def delete_material(material_id):
    if session.get('role') != 'admin':
        return "Access Denied"

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM materials WHERE id = ?", (material_id,))
    material = cursor.fetchone()
    subject_id = material[1]

    # Delete file from disk
    if material[3]:
        file_path = os.path.join('static/materials', material[3])
        if os.path.exists(file_path):
            os.remove(file_path)

    cursor.execute("DELETE FROM materials WHERE id = ?", (material_id,))
    conn.commit()
    conn.close()

    flash("Material deleted!", "danger")
    return redirect(f"/subject/{subject_id}/materials")

# 🎓 VIEW GRADES (ADMIN)
@app.route('/subject/<int:subject_id>/grades')
def grades(subject_id):
    if session.get('role') != 'admin':
        return "Access Denied"

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM subjects WHERE id = ?", (subject_id,))
    subject = cursor.fetchone()

    cursor.execute("SELECT * FROM modules WHERE id = ?", (subject[1],))
    module = cursor.fetchone()

    cursor.execute("SELECT * FROM courses WHERE id = ?", (module[1],))
    course = cursor.fetchone()

    # Get all students enrolled in this course
    cursor.execute("SELECT * FROM students WHERE course = ?", (course[1],))
    students = cursor.fetchall()

    # Get existing grades for this subject
    cursor.execute("SELECT * FROM grades WHERE subject_id = ?", (subject_id,))
    grades_list = cursor.fetchall()

    # Make a dict for easy lookup {student_id: grade}
    grades_dict = {g[1]: g for g in grades_list}

    conn.close()

    return render_template('grades.html',
                           subject=subject,
                           module=module,
                           course=course,
                           students=students,
                           grades_dict=grades_dict)


# 💾 SAVE GRADES (ADMIN)
@app.route('/subject/<int:subject_id>/grades/save', methods=['POST'])
def save_grades(subject_id):
    if session.get('role') != 'admin':
        return "Access Denied"

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Get all students from form
    student_ids = request.form.getlist('student_id')

    for student_id in student_ids:
        marks = request.form.get(f'marks_{student_id}', '')
        grade = request.form.get(f'grade_{student_id}', '')

        # Check if grade already exists
        cursor.execute("SELECT * FROM grades WHERE student_id = ? AND subject_id = ?",
                       (student_id, subject_id))
        existing = cursor.fetchone()

        if existing:
            cursor.execute("UPDATE grades SET marks = ?, grade = ? WHERE student_id = ? AND subject_id = ?",
                           (marks, grade, student_id, subject_id))
        else:
            cursor.execute("INSERT INTO grades (student_id, subject_id, marks, grade) VALUES (?, ?, ?, ?)",
                           (student_id, subject_id, marks, grade))

    conn.commit()
    conn.close()

    flash("Grades saved successfully!", "success")
    return redirect(f"/subject/{subject_id}/grades")

# 🎓 STUDENT VIEW GRADES
@app.route('/student/<int:id>/grades')
def student_grades(id):
    if 'user' not in session:
        return redirect('/')

    if session.get('role') == 'student':
        if session.get('student_id') != id:
            return "Access Denied"

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students WHERE id = ?", (id,))
    student = cursor.fetchone()

    # Get all grades with subject and module info
    cursor.execute("""
        SELECT 
            grades.marks,
            grades.grade,
            subjects.name as subject_name,
            modules.name as module_name,
            courses.name as course_name
        FROM grades
        JOIN subjects ON grades.subject_id = subjects.id
        JOIN modules ON subjects.module_id = modules.id
        JOIN courses ON modules.course_id = courses.id
        WHERE grades.student_id = ?
        ORDER BY courses.name, modules.name, subjects.name
    """, (id,))
    grades = cursor.fetchall()

    conn.close()

    return render_template('student_grades.html',
                           student=student,
                           grades=grades)

# 📚 STUDENT VIEW COURSE MATERIALS
@app.route('/student/<int:id>/materials')
def student_materials(id):
    if 'user' not in session:
        return redirect('/')

    if session.get('role') == 'student':
        if session.get('student_id') != id:
            return "Access Denied"

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students WHERE id = ?", (id,))
    student = cursor.fetchone()

    # Get course of student
    course_name = student[6]

    # Get course details
    cursor.execute("SELECT * FROM courses WHERE name = ?", (course_name,))
    course = cursor.fetchone()

    modules_with_subjects = []

    if course:
        # Get all modules for this course
        cursor.execute("SELECT * FROM modules WHERE course_id = ?", (course[0],))
        modules = cursor.fetchall()

        for module in modules:
            # Get subjects for each module
            cursor.execute("SELECT * FROM subjects WHERE module_id = ?", (module[0],))
            subjects = cursor.fetchall()

            subjects_with_materials = []
            for subject in subjects:
                # Get materials for each subject
                cursor.execute("SELECT * FROM materials WHERE subject_id = ?", (subject[0],))
                materials = cursor.fetchall()
                subjects_with_materials.append({
                    'subject': subject,
                    'materials': materials
                })

            modules_with_subjects.append({
                'module': module,
                'subjects': subjects_with_materials
            })

    conn.close()

    return render_template('student_materials.html',
                           student=student,
                           course=course,
                           modules_with_subjects=modules_with_subjects)

# 📢 VIEW ALL ANNOUNCEMENTS (ADMIN)
@app.route('/announcements')
def announcements():
    if 'user' not in session:
        return redirect('/')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    if session.get('role') == 'admin':
        # Admin sees all announcements
        cursor.execute("""
            SELECT announcements.*, courses.name
            FROM announcements
            LEFT JOIN courses ON announcements.course_id = courses.id
            ORDER BY created_at DESC
        """)
        announcements = cursor.fetchall()
        cursor.execute("SELECT * FROM courses")
        courses = cursor.fetchall()
        conn.close()
        return render_template('announcements_admin.html',
                               announcements=announcements,
                               courses=courses)
    else:
        # Student sees general + their course announcements
        student_id = session.get('student_id')
        cursor.execute("SELECT course FROM students WHERE id = ?", (student_id,))
        student = cursor.fetchone()
        course_name = student[0] if student else None

        cursor.execute("SELECT id FROM courses WHERE name = ?", (course_name,))
        course = cursor.fetchone()
        course_id = course[0] if course else None

        cursor.execute("""
            SELECT announcements.*, courses.name
            FROM announcements
            LEFT JOIN courses ON announcements.course_id = courses.id
            WHERE announcements.type = 'general'
            OR (announcements.type = 'course' AND announcements.course_id = ?)
            ORDER BY created_at DESC
        """, (course_id,))
        announcements = cursor.fetchall()
        conn.close()
        return render_template('announcements_student.html',
                               announcements=announcements)


# ➕ ADD ANNOUNCEMENT (ADMIN)
@app.route('/announcement/add', methods=['POST'])
def add_announcement():
    if session.get('role') != 'admin':
        return "Access Denied"

    title = request.form['title']
    content = request.form['content']
    ann_type = request.form['type']
    course_id = request.form.get('course_id') or None

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO announcements (title, content, type, course_id)
        VALUES (?, ?, ?, ?)
    """, (title, content, ann_type, course_id))
    conn.commit()
    conn.close()

    flash("Announcement added successfully!", "success")
    return redirect('/announcements')


# ❌ DELETE ANNOUNCEMENT (ADMIN)
@app.route('/announcement/delete/<int:id>')
def delete_announcement(id):
    if session.get('role') != 'admin':
        return "Access Denied"

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM announcements WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    flash("Announcement deleted!", "danger")
    return redirect('/announcements')

@app.route('/attendance')
def attendance():
    if session.get('role') != 'admin':
        return "Access Denied"

    import datetime
    today = str(datetime.date.today())

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Get all students
    cursor.execute("SELECT id, name FROM students")
    students = cursor.fetchall()

    # Get today's attendance
    cursor.execute("""
        SELECT student_id, status 
        FROM attendance 
        WHERE date = ?
    """, (today,))
    
    records = cursor.fetchall()

    # Convert to dictionary {student_id: status}
    attendance_dict = {r[0]: r[1] for r in records}

    conn.close()

    return render_template(
        'attendance.html',
        students=students,
        attendance_dict=attendance_dict
    )

@app.route('/attendance/mark', methods=['POST'])
def mark_attendance():
    if session.get('role') != 'admin':
        return "Access Denied"

    import datetime
    date = str(datetime.date.today())

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    for key in request.form:
        if not key.isdigit():
            continue

        student_id = int(key)
        status = request.form[key]

        try:
            cursor.execute("""
            INSERT INTO attendance (student_id, date, status)
            VALUES (?, ?, ?)
            """, (student_id, date, status))

        except sqlite3.IntegrityError:
            continue

    conn.commit()
    conn.close()

    flash("Attendance saved (duplicates ignored)", "success")
    return redirect('/attendance')

@app.route('/student/attendance')
def student_attendance():
    if 'user' not in session:
        return redirect('/')

    student_id = session.get('student_id')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM attendance WHERE student_id=?", (student_id,))
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM attendance WHERE student_id=? AND status='Present'", (student_id,))
    present = cursor.fetchone()[0]

    conn.close()

    percentage = (present / total * 100) if total > 0 else 0

    return render_template('attendance_view.html', total=total, present=present, percentage=percentage)

# 📢 VIEW SINGLE ANNOUNCEMENT
@app.route('/announcement/<int:id>')
def view_announcement(id):
    if 'user' not in session:
        return redirect('/')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT announcements.*, courses.name
        FROM announcements
        LEFT JOIN courses ON announcements.course_id = courses.id
        WHERE announcements.id = ?
    """, (id,))
    announcement = cursor.fetchone()
    conn.close()

    return render_template('announcement_detail.html', ann=announcement)

# 🚀 RUN
if __name__ == '__main__':
    app.run(debug=True)