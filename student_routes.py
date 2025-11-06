from flask import render_template, session, Blueprint, flash, request, url_for, redirect
from flask_login import login_required, current_user
from sqlalchemy import text
from helpers import *
from database import db
import os
from werkzeug.utils import secure_filename

student_bp = Blueprint('student', __name__, url_prefix='/student')


# ==============================
# Dashboard
# ==============================
@student_bp.route("/")
@login_required
def dashboard():
    query = text("""
        SELECT 
            COUNT(DISTINCT cs.id) AS total_classes,
            COUNT(DISTINCT CASE WHEN cs.status = 'completed' THEN cs.id END) AS total_classes_completed,
            COUNT(DISTINCT CASE WHEN cs.status = 'active' THEN cs.id END) AS total_classes_active,
            COUNT(DISTINCT sl.id) AS total_lessons_completed
        FROM StudentProfile sp
        LEFT JOIN ClassStudent cs ON cs.student_id = sp.id
        LEFT JOIN StudentLessonProgress sl 
            ON sl.student_id = sp.id AND sl.status = 'completed'
        WHERE sp.user_id = :user_id
    """)
    
    result = db.session.execute(query, {'user_id': current_user.id}).fetchone()
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
    classes = db.session.execute(query, {'user_id': current_user.id}).fetchall()

    return render_template("student/classes.html", classes=classes)


# ==============================
# View Lessons in a Class
# ==============================
@student_bp.route("/classes/<int:class_id>/lessons")
@login_required
def view_lessons(class_id):
    query = text("""
        SELECT l.id, l.lesson_number, l.title, l.description,
               slp.status, slp.completed_at
        FROM Lesson l
        LEFT JOIN StudentLessonProgress slp 
            ON l.id = slp.lesson_id 
            AND slp.student_id = (
                SELECT sp.id FROM StudentProfile sp WHERE sp.user_id = :user_id
            )
        WHERE l.class_id = :class_id
        ORDER BY l.lesson_number ASC
    """)
    lessons = db.session.execute(query, {
        'user_id': current_user.id,
        'class_id': class_id
    }).fetchall()

    return render_template("student/lessons.html", lessons=lessons, class_id=class_id)


# ==============================
# Mark Lesson as Completed
# ==============================
@student_bp.route("/lessons/<int:lesson_id>/complete", methods=["POST"])
@login_required
def complete_lesson(lesson_id):
    student_query = text("SELECT id FROM StudentProfile WHERE user_id = :user_id")
    student = db.session.execute(student_query, {'user_id': current_user.id}).fetchone()

    if not student:
        flash("Student profile not found.", "error")
        return redirect(url_for("student.dashboard"))

    check_query = text("""
        SELECT id FROM StudentLessonProgress
        WHERE lesson_id = :lesson_id AND student_id = :student_id
    """)
    existing = db.session.execute(check_query, {
        'lesson_id': lesson_id,
        'student_id': student.id
    }).fetchone()

    if existing:
        update = text("""
            UPDATE StudentLessonProgress
            SET status = 'completed', completed_at = NOW()
            WHERE id = :id
        """)
        db.session.execute(update, {'id': existing.id})
    else:
        insert = text("""
            INSERT INTO StudentLessonProgress (class_id, lesson_id, student_id, status, completed_at)
            SELECT l.class_id, :lesson_id, :student_id, 'completed', NOW()
            FROM Lesson l WHERE l.id = :lesson_id
        """)
        db.session.execute(insert, {
            'lesson_id': lesson_id,
            'student_id': student.id
        })

    db.session.commit()
    flash("Lesson marked as completed!", "success")
    return redirect(request.referrer or url_for("student.dashboard"))
