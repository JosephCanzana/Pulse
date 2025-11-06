from flask import render_template, session, Blueprint, flash, request,url_for, redirect
from flask_login import login_required, current_user
from sqlalchemy import text
from helpers import *
from database import db
import os
from werkzeug.utils import secure_filename

teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')

UPLOAD_FOLDER = "uploads/lessons"


def get_teacher_id():
    """Helper function to get the teacher ID for the current user."""
    result = db.session.execute(
        text("SELECT id FROM TeacherProfile WHERE user_id = :user_id"),
        {"user_id": current_user.get_id()}
    ).mappings().first()
    return result["id"] if result else None


@teacher_bp.route("/")
@login_required
def dashboard():
    teacher_id = get_teacher_id()
    if not teacher_id:
        return apology("Teacher profile not found.", 404)

    # --- Fetch teacher advisory sections ---
    query = text("""
        SELECT 
            sec.id AS section_id,
            sec.name AS section_name,
            co.name AS course_name,
            el.name AS education_level,
            sec.status AS section_status,
            COUNT(st.id) AS student_count
        FROM Section sec
        JOIN Course co ON sec.course_id = co.id
        JOIN EducationLevel el ON co.education_level_id = el.id
        LEFT JOIN StudentProfile st ON st.section_id = sec.id
        WHERE sec.teacher_id = :teacher_id AND sec.status = 1
        GROUP BY sec.id, sec.name, co.name, el.name
        ORDER BY el.name, co.name, sec.name
    """)

    advisory_sections = db.session.execute(query, {"teacher_id": teacher_id}).mappings().all()

    # --- Fetch daily inspirations (already generated globally) ---
    daily = db.session.execute(text("""
        SELECT di.*, 
               q.quote, q.author, 
               v.verse_text, v.reference, 
               m.message, m.theme
        FROM daily_inspirations di
        LEFT JOIN motivational_quotes q ON di.quote_id = q.id
        LEFT JOIN bible_verses v ON di.verse_id = v.id
        LEFT JOIN grateful_peace_messages m ON di.message_id = m.id
        ORDER BY di.date DESC
        LIMIT 1
    """)).mappings().first()

    # --- Render Template ---
    return render_template(
        "teacher/dashboard.html",
        name=session.get("first_name"),
        sections=advisory_sections,
        daily=daily
    )

@teacher_bp.route("/classes")
@login_required
def classes():
    """Display all subjects taught by the current teacher, linked with their sections/classes."""
    teacher_id = get_teacher_id()
    if not teacher_id:
        return apology("Teacher profile not found.", 404)

    query = text("""
        SELECT 
            c.id AS class_id,
            s.name AS subject_name,
            sec.name AS section_name,
            el.name AS education_level
        FROM Class c
        JOIN Subject s ON c.subject_id = s.id
        JOIN Section sec ON c.section_id = sec.id
        JOIN Course co ON sec.course_id = co.id
        JOIN EducationLevel el ON co.education_level_id = el.id
        WHERE c.teacher_id = :teacher_id
        ORDER BY el.name, sec.name, s.name
    """)

    teacher_classes = db.session.execute(query, {"teacher_id": teacher_id}).mappings().all()

    return render_template(
        "teacher/classes/list.html",
        classes=teacher_classes
    )

# =============
# VIEW classes
# =============
@teacher_bp.route("/classes/view/<int:class_id>", methods=["GET", "POST"])
@login_required
def view_class(class_id):
    """Display class details and allow inline editing of class info, including class color."""

    # Fetch class info with joined names (now includes color)
    class_query = text("""
        SELECT 
            c.id AS class_id,
            c.subject_id,
            c.section_id,
            c.status AS class_status,
            c.color AS class_color,
            s.name AS subject_name,
            sec.name AS section_name,
            co.name AS course_name,
            el.name AS education_level
        FROM Class c
        JOIN Subject s ON c.subject_id = s.id
        JOIN Section sec ON c.section_id = sec.id
        LEFT JOIN Course co ON sec.course_id = co.id
        LEFT JOIN EducationLevel el ON co.education_level_id = el.id
        WHERE c.id = :class_id
    """)
    class_info = db.session.execute(class_query, {"class_id": class_id}).mappings().first()

    if not class_info:
        return apology("Class not found.", 404)

    # Fetch lessons
    lessons_query = text("""
        SELECT id, lesson_number, title, description
        FROM Lesson
        WHERE class_id = :class_id
        ORDER BY lesson_number
    """)
    lessons = db.session.execute(lessons_query, {"class_id": class_id}).mappings().all()
    no_lessons = len(lessons) == 0

    # Fetch students
    students_query = text("""
        SELECT CONCAT(u.first_name, ' ', COALESCE(u.middle_name,''), ' ', u.last_name) AS full_name,
               sp.year_id,
               cs.status AS enrollment_status
        FROM ClassStudent cs
        JOIN StudentProfile sp ON cs.student_id = sp.id
        JOIN Users u ON sp.user_id = u.id
        WHERE cs.class_id = :class_id
        ORDER BY u.last_name
    """)
    students = db.session.execute(students_query, {"class_id": class_id}).mappings().all()
    no_students = len(students) == 0

    # Dropdown options
    subjects = db.session.execute(text("SELECT id, name FROM Subject WHERE status = 1")).mappings().all()
    sections = db.session.execute(text("SELECT id, name FROM Section WHERE status = 1")).mappings().all()

    # Handle inline edit submission
    if request.method == "POST":
        subject_name = request.form.get("subject_id")
        section_name = request.form.get("section_id")
        class_status = request.form.get("class_status")
        class_color = request.form.get("class_color") 

        # Look up IDs from the names
        subject_row = db.session.execute(
            text("SELECT id FROM Subject WHERE name = :name"), {"name": subject_name}
        ).fetchone()
        section_row = db.session.execute(
            text("SELECT id FROM Section WHERE name = :name"), {"name": section_name}
        ).fetchone()

        if not subject_row or not section_row:
            flash("Invalid subject or section name selected.", "error")
            return redirect(url_for("teacher.view_class", class_id=class_id))

        subject_id = subject_row.id
        section_id = section_row.id

        # Proceed with updating using IDs (and color)
        update_query = text("""
            UPDATE Class
            SET subject_id = :subject_id,
                section_id = :section_id,
                status = :status,
                color = :color
            WHERE id = :class_id
        """)
        db.session.execute(update_query, {
            "subject_id": subject_id,
            "section_id": section_id,
            "status": class_status,
            "color": class_color,
            "class_id": class_id
        })
        db.session.commit()
        flash("Class updated successfully!", "success")
        return redirect(url_for("teacher.view_class", class_id=class_id))

    return render_template(
        "teacher/classes/view.html",
        class_info=class_info,
        lessons=lessons,
        students=students,
        no_lessons=no_lessons,
        no_students=no_students,
        subjects=subjects,
        sections=sections
    )

# ============================
# Manage Lesson (View / Add)
# ============================
@teacher_bp.route("/classes/view/<int:class_id>/lessons", methods=["GET", "POST"])
@login_required
def manage_lesson(class_id):
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        file = request.files.get("file")

        if not title:
            flash("Lesson title is required.", "danger")
            return redirect(request.url)

        # Determine next lesson number
        next_num_query = text("""
            SELECT COALESCE(MAX(lesson_number), 0) + 1 AS next_number
            FROM Lesson
            WHERE class_id = :class_id
        """)
        next_number = db.session.execute(next_num_query, {"class_id": class_id}).scalar()

        # Insert lesson
        insert_lesson = text("""
            INSERT INTO Lesson (class_id, lesson_number, title, description, created_at, updated_at)
            VALUES (:class_id, :lesson_number, :title, :description, NOW(), NOW())
        """)
        db.session.execute(insert_lesson, {
            "class_id": class_id,
            "lesson_number": next_number,
            "title": title,
            "description": description
        })
        db.session.commit()

        # Get inserted lesson ID
        lesson_id = db.session.execute(text("SELECT LAST_INSERT_ID()")).scalar()

        # NEW: create StudentLessonProgress for all enrolled students 
        create_progress = text("""
            INSERT IGNORE INTO StudentLessonProgress (class_id, lesson_id, student_id, status, started_at, completed_at)
            SELECT cs.class_id, :lesson_id, cs.student_id, 'not_started', NULL, NULL
            FROM ClassStudent cs
            WHERE cs.class_id = :class_id
        """)
        db.session.execute(create_progress, {"lesson_id": lesson_id, "class_id": class_id})
        db.session.commit()


        # Handle file upload
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

            insert_file = text("""
                INSERT INTO LessonFile (lesson_id, file_name, file_path, file_type, uploaded_at)
                VALUES (:lesson_id, :file_name, :file_path, :file_type, NOW())
            """)
            db.session.execute(insert_file, {
                "lesson_id": lesson_id,
                "file_name": filename,
                "file_path": filepath,
                "file_type": file.mimetype
            })
            db.session.commit()

        flash("Lesson added successfully!", "success")
        return redirect(url_for("teacher.manage_lesson", class_id=class_id))


    # Fetch lessons
    lessons = db.session.execute(text("""
        SELECT * FROM Lesson
        WHERE class_id = :class_id
        ORDER BY lesson_number ASC
    """), {"class_id": class_id}).mappings().all()

    return render_template("teacher/classes/lesson_form.html", lessons=lessons, class_id=class_id)

# Lesson order
@teacher_bp.route("/classes/view/<int:class_id>/lessons/update-order", methods=["POST"])
@login_required
def update_lesson_order(class_id):
    order_data = request.form.get("order")

    if not order_data:
        flash("No order data received.", "danger")
        return redirect(url_for("teacher.manage_lesson", class_id=class_id))

    import json
    try:
        order_list = json.loads(order_data)
        for item in order_list:
            db.session.execute(text("""
                UPDATE Lesson
                SET lesson_number = :new_order
                WHERE id = :lesson_id AND class_id = :class_id
            """), {
                "new_order": item["new_order"],
                "lesson_id": item["id"],
                "class_id": class_id
            })
        db.session.commit()
        flash("Lesson order updated successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating lesson order: {e}", "danger")

    return redirect(url_for("teacher.manage_lesson", class_id=class_id))


# Edit Lesson
@teacher_bp.route("/classes/view/<int:class_id>/lessons/edit/<int:lesson_id>", methods=["GET", "POST"])
@login_required
def edit_lesson(class_id, lesson_id):
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        file = request.files.get("file")

        # Update lesson info
        update_lesson = text("""
            UPDATE Lesson
            SET title = :title,
                description = :description,
                updated_at = NOW()
            WHERE id = :lesson_id
        """)
        db.session.execute(update_lesson, {
            "title": title,
            "description": description,
            "lesson_id": lesson_id
        })
        db.session.commit()

        # Optional file upload
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

            insert_file = text("""
                INSERT INTO LessonFile (lesson_id, file_name, file_path, file_type, uploaded_at)
                VALUES (:lesson_id, :file_name, :file_path, :file_type, NOW())
            """)
            db.session.execute(insert_file, {
                "lesson_id": lesson_id,
                "file_name": filename,
                "file_path": filepath,
                "file_type": file.mimetype
            })
            db.session.commit()

        flash("Lesson updated successfully!", "success")
        return redirect(url_for("teacher.manage_lesson", class_id=class_id))

    # Fetch lesson
    lesson = db.session.execute(text("""
        SELECT * FROM Lesson WHERE id = :lesson_id
    """), {"lesson_id": lesson_id}).mappings().first()

    if not lesson:
        flash("Lesson not found.", "danger")
        return redirect(url_for("teacher.manage_lesson", class_id=class_id))

    return render_template("teacher/classes/edit_lesson.html", lesson=lesson, class_id=class_id)


# Delete Lesson
@teacher_bp.route("/classes/view/<int:class_id>/lessons/delete/<int:lesson_id>", methods=["POST"])
@login_required
def delete_lesson(class_id, lesson_id):
    db.session.execute(text("DELETE FROM Lesson WHERE id = :lesson_id"), {"lesson_id": lesson_id})
    db.session.commit()
    flash("Lesson deleted successfully!", "success")
    return redirect(url_for("teacher.manage_lesson", class_id=class_id))

# ============================
# Manage Student
# ============================
@teacher_bp.route("/classes/view/<int:class_id>/add-student", methods=["GET", "POST"])
@login_required
def manage_student(class_id):
    search_query = request.form.get("search", "").strip()
    selected_students = request.form.getlist("student_ids")  # checkboxes for multiple add

    if request.method == "POST" and selected_students:
        for student_id in selected_students:
            # Add student to class
            db.session.execute(
                text(
                    "INSERT IGNORE INTO ClassStudent (class_id, student_id) VALUES (:class_id, :student_id)"
                ),
                {"class_id": class_id, "student_id": student_id}
            )

            # create StudentLessonProgress for all existing lessons in this class 
            create_progress = text("""
                INSERT IGNORE INTO StudentLessonProgress (class_id, lesson_id, student_id, status, started_at, completed_at)
                SELECT id AS class_id, l.id AS lesson_id, :student_id, 'not_started', NULL, NULL
                FROM Lesson l
                WHERE l.class_id = :class_id
            """)
            db.session.execute(create_progress, {"student_id": student_id, "class_id": class_id})
        
        db.session.commit()
        flash("Student(s) added successfully.", "success")
        return redirect(url_for("teacher.manage_student", class_id=class_id))


    search_pattern = f"%{search_query}%"

    # Students NOT yet in the class with section info
    students = db.session.execute(
        text(
            """
            SELECT sp.id AS student_id, u.first_name, u.last_name, u.school_id,
                   sp.section_id, sec.name AS section_name
            FROM StudentProfile sp
            JOIN Users u ON sp.user_id = u.id
            LEFT JOIN ClassStudent cs 
                ON cs.student_id = sp.id AND cs.class_id = :class_id
            LEFT JOIN Section sec ON sp.section_id = sec.id
            WHERE cs.id IS NULL
              AND (
                  u.first_name LIKE :search OR 
                  u.last_name LIKE :search OR 
                  u.school_id LIKE :search OR
                  sec.name LIKE :search
              )
            ORDER BY sec.name, u.last_name, u.first_name
            """
        ),
        {"class_id": class_id, "search": search_pattern}
    ).fetchall()

    # Students ALREADY in the class with section info
    existing_students = db.session.execute(
        text(
            """
            SELECT sp.id AS student_id, u.first_name, u.last_name, u.school_id,
                   sp.section_id, sec.name AS section_name
            FROM ClassStudent cs
            JOIN StudentProfile sp ON cs.student_id = sp.id
            JOIN Users u ON sp.user_id = u.id
            LEFT JOIN Section sec ON sp.section_id = sec.id
            WHERE cs.class_id = :class_id
            ORDER BY sec.name, u.last_name, u.first_name
            """
        ),
        {"class_id": class_id}
    ).fetchall()

    return render_template(
        "teacher/classes/add_student.html",
        students=students,
        existing_students=existing_students,
        class_id=class_id,
        search_query=search_query
    )

# Remove student
@teacher_bp.route("/classes/view/<int:class_id>/remove-student", methods=["POST"])
@login_required
def remove_student_from_class(class_id):
    """
    Remove a student from a class.
    Expects POST with 'id' = student_id
    """
    student_id = request.form.get("id")
    if not student_id:
        flash("Invalid student ID.", "error")
        return redirect(url_for("teacher.manage_student", class_id=class_id))

    # Delete the record from ClassStudent
    db.session.execute(
        text(
            "DELETE FROM ClassStudent WHERE class_id = :class_id AND student_id = :student_id"
        ),
        {"class_id": class_id, "student_id": student_id}
    )
    db.session.commit()
    flash("Student removed successfully.", "success")
    return redirect(url_for("teacher.manage_student", class_id=class_id))

