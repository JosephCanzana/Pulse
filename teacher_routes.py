from flask import render_template, session, Blueprint
from flask_login import login_required, current_user
from sqlalchemy import text
from helpers import *
from database import db

teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')

from flask import Blueprint, render_template, session
from flask_login import login_required, current_user
from sqlalchemy import text
from app import db
from helpers import apology

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
    """Teacher dashboard — shows advisory sections with their course and level."""
    teacher_id = get_teacher_id()
    if not teacher_id:
        return apology("Teacher profile not found.", 404)

    # Fetch advisory sections with course + education level details
    query = text("""
        SELECT 
            sec.id AS section_id,
            sec.name AS section_name,
            co.name AS course_name,
            el.name AS education_level,
            COUNT(st.id) AS student_count
        FROM Section sec
        JOIN Course co ON sec.course_id = co.id
        JOIN EducationLevel el ON co.education_level_id = el.id
        LEFT JOIN StudentProfile st ON st.section_id = sec.id
        WHERE sec.teacher_id = :teacher_id
        GROUP BY sec.id, sec.name, co.name, el.name
        ORDER BY el.name, co.name, sec.name
    """)

    advisory_sections = db.session.execute(query, {"teacher_id": teacher_id}).mappings().all()

    return render_template(
        "teacher/dashboard.html",
        name=session.get("first_name"),
        sections=advisory_sections
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
