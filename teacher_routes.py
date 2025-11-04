from flask import render_template, session, Blueprint, flash, request,url_for, redirect
from flask_login import login_required, current_user
from sqlalchemy import text
from helpers import *
from database import db

teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')

teacher_bp = Blueprint("teacher", __name__, url_prefix="/teacher")


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

@teacher_bp.route("/classes/view/<int:class_id>", methods=["GET", "POST"])
@login_required
def view_class(class_id):
    """Display class details and allow inline editing of class info."""

    # Fetch class info with joined names
    class_query = text("""
        SELECT 
            c.id AS class_id,
            c.subject_id,
            c.section_id,
            c.status AS class_status,
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
        subject_id = request.form.get("subject_id")
        section_id = request.form.get("section_id")
        class_status = request.form.get("class_status")

        update_query = text("""
            UPDATE Class
            SET subject_id = :subject_id,
                section_id = :section_id,
                status = :status
            WHERE id = :class_id
        """)
        db.session.execute(update_query, {
            "subject_id": subject_id,
            "section_id": section_id,
            "status": class_status,
            "class_id": class_id
        })
        db.session.commit()
        flash("Class updated successfully!", "success")
        return redirect(url_for("teacher_bp.view_class", class_id=class_id))

    return render_template(
        "teacher/classes/view.html",  # updated template
        class_info=class_info,
        lessons=lessons,
        students=students,
        no_lessons=no_lessons,
        no_students=no_students,
        subjects=subjects,
        sections=sections
    )

@login_required
def edit_class(class_id):
    """Edit class details in the format of the view template."""

    # Fetch class info with joined names
    class_query = text("""
        SELECT 
            c.id AS class_id,
            c.subject_id,
            c.section_id,
            c.status AS class_status,
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

    if request.method == "POST":
        subject_id = request.form.get("subject_id")
        section_id = request.form.get("section_id")
        class_status = request.form.get("class_status")

        update_query = text("""
            UPDATE Class
            SET subject_id = :subject_id,
                section_id = :section_id,
                status = :status
            WHERE id = :class_id
        """)
        db.session.execute(update_query, {
            "subject_id": subject_id,
            "section_id": section_id,
            "status": class_status,
            "class_id": class_id
        })
        db.session.commit()

        flash("Class updated successfully!", "success")
        return redirect(url_for("teacher_bp.view_class", class_id=class_id))

    return render_template(
        "teacher/classes/edit.html",
        class_info=class_info,
        lessons=lessons,
        students=students,
        no_lessons=no_lessons,
        no_students=no_students,
        subjects=subjects,
        sections=sections
    )

