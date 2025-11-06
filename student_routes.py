from flask import render_template, session, Blueprint, flash, request, url_for, redirect
from flask_login import login_required, current_user
from sqlalchemy import text
from helpers import *
from database import db
from datetime import datetime

student_bp = Blueprint('student', __name__, url_prefix='/student')


# ==============================
# Dashboard
# ==============================
@student_bp.route("/")
@login_required
def dashboard():
    # Main summary counts
    summary_query = text("""
        SELECT 
            COUNT(DISTINCT cs.id) AS total_classes,
            COUNT(DISTINCT CASE WHEN cs.status = 'completed' THEN cs.id END) AS total_classes_completed,
            COUNT(DISTINCT CASE WHEN cs.status = 'active' THEN cs.id END) AS total_classes_active,
            COUNT(DISTINCT CASE WHEN sl.status = 'completed' THEN sl.id END) AS total_lessons_completed,
            COUNT(DISTINCT CASE WHEN sl.status = 'in_progress' THEN sl.id END) AS lessons_in_progress
        FROM StudentProfile sp
        LEFT JOIN ClassStudent cs ON cs.student_id = sp.id
        LEFT JOIN StudentLessonProgress sl 
            ON sl.student_id = sp.id
        WHERE sp.user_id = :user_id
    """)

    result = db.session.execute(summary_query, {'user_id': current_user.id}).fetchone()

    # Recent progress (most recent 5 lessons by started_at or completed_at)
    recent_progress_query = text("""
        SELECT 
            l.id AS lesson_id,
            l.title AS lesson_title,
            c.id AS class_id,
            s.name AS subject_name,
            slp.status,
            slp.started_at,
            slp.completed_at
        FROM StudentLessonProgress slp
        JOIN Lesson l ON l.id = slp.lesson_id
        JOIN Class c ON c.id = slp.class_id
        JOIN Subject s ON s.id = c.subject_id
        JOIN StudentProfile sp ON sp.id = slp.student_id
        WHERE sp.user_id = :user_id
        ORDER BY GREATEST(
            IFNULL(slp.completed_at, '1970-01-01'),
            IFNULL(slp.started_at, '1970-01-01')
        ) DESC
        LIMIT 5
    """)

    recent_progress = db.session.execute(recent_progress_query, {'user_id': current_user.id}).mappings().all()

    # Daily inspiration
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

    return render_template(
        "student/dashboard.html",
        name=session.get("first_name"),
        total_classes=result.total_classes or 0,
        total_classes_completed=result.total_classes_completed or 0,
        total_classes_active=result.total_classes_active or 0,
        total_lessons_completed=result.total_lessons_completed or 0,
        lessons_in_progress=result.lessons_in_progress or 0,
        recent_progress=recent_progress,
        daily=daily
    )



# ==============================
# View Enrolled Classes
# ==============================
@student_bp.route("/classes")
@login_required
def view_classes():
    query = text("""
        SELECT c.id, s.name AS subject_name, sec.name AS section_name,
               c.status, t.user_id AS teacher_user_id, 
               CONCAT(u.first_name, ' ', u.last_name) AS teacher_name
        FROM ClassStudent cs
        JOIN Class c ON cs.class_id = c.id
        JOIN Subject s ON c.subject_id = s.id
        JOIN Section sec ON c.section_id = sec.id
        JOIN TeacherProfile t ON c.teacher_id = t.id
        JOIN Users u ON t.user_id = u.id
        JOIN StudentProfile sp ON cs.student_id = sp.id
        WHERE sp.user_id = :user_id
    """)
    all_classes = db.session.execute(query, {'user_id': current_user.id}).fetchall()

    # Separate active vs history
    active_classes = [c for c in all_classes if c.status == 'active']
    history_classes = [c for c in all_classes if c.status in ('completed', 'cancelled')]

    return render_template(
        "student/classes.html",
        active_classes=active_classes,
        history_classes=history_classes
    )

# ==============================
# View Lessons in a Class (with files)
# ==============================
@student_bp.route("/classes/<int:class_id>/lessons")
@login_required
def view_lessons(class_id):
    # Get class status
    class_status_query = text("SELECT status FROM Class WHERE id = :class_id")
    class_status = db.session.execute(class_status_query, {'class_id': class_id}).scalar()

    # Fetch lessons with progress and files
    query = text("""
        SELECT l.id, l.lesson_number, l.title, l.description,
               slp.status, slp.completed_at,
               lf.id AS file_id, lf.file_name, lf.file_path, lf.file_type
        FROM Lesson l
        LEFT JOIN StudentLessonProgress slp 
            ON l.id = slp.lesson_id 
            AND slp.student_id = (
                SELECT sp.id FROM StudentProfile sp WHERE sp.user_id = :user_id
            )
        LEFT JOIN LessonFile lf
            ON l.id = lf.lesson_id
        WHERE l.class_id = :class_id
        ORDER BY l.lesson_number ASC
    """)
    lessons = db.session.execute(query, {
        'user_id': current_user.id,
        'class_id': class_id
    }).fetchall()

    # If the class is completed or cancelled, flash info but allow view
    if class_status in ('completed', 'cancelled'):
        flash("This class is no longer active. You can view it in your history, but cannot update progress.", "info")

    return render_template(
        "student/lessons.html",
        lessons=lessons,
        class_id=class_id,
        class_status=class_status  # Pass the status to the template
    )

# ==============================
# Update Lesson Progress (Incremental)
# ==============================
@student_bp.route("/lessons/<int:lesson_id>/progress", methods=["POST"])
@login_required
def update_lesson_progress(lesson_id):
    student_query = text("SELECT id FROM StudentProfile WHERE user_id = :user_id")
    student = db.session.execute(student_query, {'user_id': current_user.id}).fetchone()
    class_id_query = text("SELECT class_id FROM Lesson WHERE id = :lesson_id")
    class_id = db.session.execute(class_id_query, {'lesson_id': lesson_id}).scalar()

    # Check class status
    class_status_query = text("SELECT status FROM Class WHERE id = :class_id")
    class_status = db.session.execute(class_status_query, {'class_id': class_id}).scalar()

    if class_status in ('completed', 'cancelled'):
        flash("You cannot update progress for a completed or cancelled class.", "warning")
        return redirect(url_for("student.view_classes"))

    if not student:
        flash("Student profile not found.", "error")
        return redirect(url_for("student.dashboard"))

    progress_query = text("""
        SELECT id, status, started_at, completed_at 
        FROM StudentLessonProgress
        WHERE lesson_id = :lesson_id AND student_id = :student_id
    """)
    progress = db.session.execute(progress_query, {
        'lesson_id': lesson_id,
        'student_id': student.id
    }).fetchone()

    next_status = 'not_started'
    now = datetime.now()

    if progress:
        if progress.status == 'not_started':
            next_status = 'in_progress'
            update = text("""
                UPDATE StudentLessonProgress
                SET status = :status,
                    started_at = NOW()
                WHERE id = :id
            """)
            db.session.execute(update, {'id': progress.id, 'status': next_status})

        elif progress.status == 'in_progress':
            next_status = 'completed'
            update = text("""
                UPDATE StudentLessonProgress
                SET status = :status,
                    completed_at = NOW()
                WHERE id = :id
            """)
            db.session.execute(update, {'id': progress.id, 'status': next_status})

    else:
        # First time clicking → move from not_started → in_progress
        insert = text("""
            INSERT INTO StudentLessonProgress (class_id, lesson_id, student_id, status, started_at)
            SELECT l.class_id, :lesson_id, :student_id, 'in_progress', NOW()
            FROM Lesson l WHERE l.id = :lesson_id
        """)
        db.session.execute(insert, {
            'lesson_id': lesson_id,
            'student_id': student.id
        })

    db.session.commit()
    flash(f"Lesson progress updated to '{next_status}'!", "success")
    return redirect(request.referrer or url_for("student.dashboard"))


@student_bp.route("/history")
@login_required
def history():
    search = request.args.get("search", "").strip().lower()
    query = """
        SELECT c.id, s.name AS subject_name, sec.name AS section_name, 
               CONCAT(u.first_name, ' ', u.last_name) AS teacher_name, 
               c.status, c.color
        FROM Class c
        JOIN Subject s ON c.subject_id = s.id
        JOIN Section sec ON c.section_id = sec.id
        JOIN TeacherProfile tp ON c.teacher_id = tp.id
        JOIN Users u ON tp.user_id = u.id
        WHERE c.status IN ('completed', 'cancelled')
    """
    if search:
        query += " AND (LOWER(s.name) LIKE :s OR LOWER(sec.name) LIKE :s OR LOWER(u.first_name) LIKE :s OR LOWER(u.last_name) LIKE :s)"
        classes = db.session.execute(text(query), {"s": f"%{search}%"}).fetchall()
    else:
        classes = db.session.execute(text(query)).fetchall()

    return render_template("student/history.html", history_classes=classes)
