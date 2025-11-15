from flask import render_template, session, Blueprint, flash, request,url_for, redirect, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import text
from database import db
from helpers import *
import json
import os
from datetime import datetime
from decorators import role_required

teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')

# GLOBAL VARIABLE
UPLOAD_FOLDER = "uploads/lessons"

def get_teacher_id():
    result = db.session.execute(
        text("SELECT id FROM TeacherProfile WHERE user_id = :user_id"),
        {"user_id": current_user.get_id()}
    ).mappings().first()
    return result["id"] if result else None

@teacher_bp.route("/")
@login_required
@role_required("teacher")
def dashboard():
    teacher_id = get_teacher_id()
    if not teacher_id:
        return apology("Teacher profile not found.", 404)

    # --- Fetch teacher advisory sections ---
    advisory_sections = db.session.execute(text("""
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
    """), {"teacher_id": teacher_id}).mappings().all()

    # --- Fetch lesson progress for students only in teacher's sections ---
    lesson_progress = db.session.execute(text("""
    SELECT 
        slp.id,
        CONCAT(u.first_name, ' ', u.last_name) AS student_name,
        c.id AS class_id,
        sub.name AS subject_name,
        c.status AS class_status,
        l.title AS lesson_title,
        slp.started_at,
        slp.completed_at
    FROM StudentLessonProgress slp
    JOIN StudentProfile sp ON slp.student_id = sp.id
    JOIN Users u ON sp.user_id = u.id
    JOIN Class c ON slp.class_id = c.id
    JOIN Subject sub ON c.subject_id = sub.id
    JOIN Section sec ON c.section_id = sec.id
    JOIN Lesson l ON slp.lesson_id = l.id
    WHERE (slp.status = 'completed' OR slp.status = 'in_progress')
      AND sec.teacher_id = :teacher_id
    ORDER BY slp.completed_at DESC
    LIMIT 15
"""), {"teacher_id": teacher_id}).mappings().all()


    # --- Fetch daily inspirations ---
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
        "teacher/dashboard.html",
        name=session.get("first_name"),
        sections=advisory_sections,
        daily=daily,
        lesson_progress=lesson_progress
    )

@teacher_bp.route("/classes")
@login_required
@role_required("teacher")
def classes():
    """Display all subjects taught by the current teacher, linked with their sections/classes."""
    teacher_id = get_teacher_id()
    if not teacher_id:
        return apology("Teacher profile not found.", 404)

    # Get query parameters
    selected_status = request.args.get("status", "active")
    search = request.args.get("search", "").strip()

    # Base SQL
    query = """
    SELECT 
        c.id AS class_id,
        s.name AS subject_name,
        sec.name AS section_name,
        el.name AS education_level,
        c.color,
        c.status
    FROM Class c
    JOIN Subject s ON c.subject_id = s.id
    JOIN Section sec ON c.section_id = sec.id
    LEFT JOIN Course co ON sec.course_id = co.id
    LEFT JOIN EducationLevel el ON co.education_level_id = el.id
    WHERE c.teacher_id = :teacher_id
    """

    params = {"teacher_id": teacher_id}

    # Filter by class status
    if selected_status != "all":
        query += " AND c.status = :status"
        params["status"] = selected_status

    # Apply search if provided
    if search:
        query += """
        AND (
            s.name LIKE :search OR
            sec.name LIKE :search OR
            el.name LIKE :search
        )
        """
        params["search"] = f"%{search}%"

    query += " ORDER BY el.name, sec.name, s.name"

    teacher_classes = db.session.execute(text(query), params).mappings().all()

    return render_template(
        "teacher/classes/list.html",
        classes=teacher_classes,
        selected_status=selected_status,
        search=search
    )

# =============
# VIEW class
# =============
@teacher_bp.route("/classes/view/<int:class_id>", methods=["GET", "POST"])
@login_required
@role_required("teacher")
def view_class(class_id):
    """Display class details and allow inline editing of class info, including class color and quick grade overview."""

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
        COALESCE(el_from_course.name, el_from_year.name) AS education_level
    FROM Class c
    JOIN Subject s ON c.subject_id = s.id
    JOIN Section sec ON c.section_id = sec.id
    LEFT JOIN Course co ON sec.course_id = co.id
    LEFT JOIN EducationLevel el_from_course ON co.education_level_id = el_from_course.id
    LEFT JOIN YearLevel yl ON sec.year_id = yl.id
    LEFT JOIN EducationLevel el_from_year ON yl.education_level_id = el_from_year.id
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
    SELECT 
        cs.id AS class_student_id,
        sp.id AS student_profile_id,
        CONCAT(u.first_name, ' ', u.last_name) AS full_name,
        sp.year_id,
        u.school_id,
        yl.name AS year,
        cs.status AS enrollment_status
    FROM ClassStudent cs
    JOIN StudentProfile sp ON cs.student_id = sp.id
    JOIN Users u ON sp.user_id = u.id
    JOIN YearLevel yl ON sp.year_id = yl.id
    WHERE cs.class_id = :class_id
    ORDER BY u.last_name
""")

    students_raw = db.session.execute(students_query, {"class_id": class_id}).mappings().all()
    no_students = len(students_raw) == 0

    # Convert to mutable dict and compute quick overall grade for each student
    students = []
    for student in students_raw:
        student_dict = dict(student)  # make mutable

        grade_query = text("""
            SELECT 
                COALESCE(SUM(asub.score), 0) AS total_score,
                COALESCE(SUM(a.max_score), 0) AS max_score
            FROM Activity a
            LEFT JOIN ActivitySubmission asub
                ON asub.activity_id = a.id
                AND asub.student_id = :student_id
            WHERE a.class_id = :class_id
        """)
        grade_result = db.session.execute(grade_query, {
            "student_id": student_dict["student_profile_id"],
            "class_id": class_id
        }).mappings().first()

        total_score = grade_result["total_score"]
        max_score = grade_result["max_score"]
        overall_percentage = (total_score / max_score * 100) if max_score > 0 else None

        student_dict["total_score"] = total_score
        student_dict["max_score"] = max_score
        student_dict["overall_percentage"] = round(overall_percentage, 1) if overall_percentage is not None else None

        students.append(student_dict)

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

        try:
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
        except Exception:
            flash("Something went wrong updating the class details!", "error")

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

@teacher_bp.route("/classes/<int:class_id>/student_status/<int:cs_id>", methods=["POST"])
@login_required
@role_required("teacher")
def update_student_status(class_id, cs_id):
    """Update enrollment status for a single student in a class."""
    new_status = request.form.get("status")
    if new_status not in ["active", "dropped", "completed"]:
        flash("Invalid status.", "error")
        return redirect(url_for("teacher.view_class", class_id=class_id))

    db.session.execute(
        text("UPDATE ClassStudent SET status = :status WHERE id = :cs_id AND class_id = :class_id"),
        {"status": new_status, "cs_id": cs_id, "class_id": class_id}
    )
    db.session.commit()
    flash("Student status updated successfully.", "success")
    return redirect(url_for("teacher.view_class", class_id=class_id))


# ============================
# Manage Lesson (View / Add)
# ============================
@teacher_bp.route("/classes/view/<int:class_id>/lessons", methods=["GET", "POST"])
@login_required
@role_required("teacher")
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
@role_required("teacher")
def update_lesson_order(class_id):
    order_data = request.form.get("order")

    if not order_data:
        flash("No order data received.", "danger")
        return redirect(url_for("teacher.manage_lesson", class_id=class_id))

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
@role_required("teacher")
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

            # Check if a file already exists
            existing_file = db.session.execute(text("""
                SELECT id FROM LessonFile WHERE lesson_id = :lesson_id
            """), {"lesson_id": lesson_id}).first()

            if existing_file:
                # Update existing file
                db.session.execute(text("""
                    UPDATE LessonFile
                    SET file_name = :file_name,
                        file_path = :file_path,
                        file_type = :file_type,
                        uploaded_at = NOW()
                    WHERE lesson_id = :lesson_id
                """), {
                    "lesson_id": lesson_id,
                    "file_name": filename,
                    "file_path": filepath,
                    "file_type": file.mimetype
                })
            else:
                # Insert new file
                db.session.execute(text("""
                    INSERT INTO LessonFile (lesson_id, file_name, file_path, file_type)
                    VALUES (:lesson_id, :file_name, :file_path, :file_type)
                """), {
                    "lesson_id": lesson_id,
                    "file_name": filename,
                    "file_path": filepath,
                    "file_type": file.mimetype
                })

            db.session.commit()


        flash("Lesson updated successfully!", "success")
        return redirect(url_for("teacher.manage_lesson", class_id=class_id))

    # Fetch lesson info
    lesson = db.session.execute(text("""
        SELECT * FROM Lesson WHERE id = :lesson_id
    """), {"lesson_id": lesson_id}).mappings().first()

    if not lesson:
        flash("Lesson not found.", "danger")
        return redirect(url_for("teacher.manage_lesson", class_id=class_id))

    # ✅ Fetch lesson files
    lesson_files = db.session.execute(text("""
        SELECT * FROM LessonFile WHERE lesson_id = :lesson_id
    """), {"lesson_id": lesson_id}).mappings().all()

    return render_template(
        "teacher/classes/edit_lesson.html",
        lesson=lesson,
        lesson_files=lesson_files,  # Pass to template
        class_id=class_id
    )


# Delete Lesson
@teacher_bp.route("/classes/view/<int:class_id>/lessons/delete/<int:lesson_id>", methods=["POST"])
@login_required
@role_required("teacher")
def delete_lesson(class_id, lesson_id):
    db.session.execute(text("DELETE FROM Lesson WHERE id = :lesson_id"), {"lesson_id": lesson_id})
    db.session.commit()
    flash("Lesson deleted successfully!", "success")
    return redirect(url_for("teacher.manage_lesson", class_id=class_id))

# ============================
# Manage Student Per Class
# ============================
@teacher_bp.route("/classes/view/<int:class_id>/add-student", methods=["GET", "POST"])
@login_required
@role_required("teacher")
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

            
        
        db.session.commit()
        flash("Student(s) added successfully.", "success")
        return redirect(url_for("teacher.manage_student", class_id=class_id))

    search_pattern = f"%{search_query}%"

    # Fetch the education level of this class via its section
    class_edu_level = db.session.execute(
        text("""
            SELECT sec.education_lvl_id
            FROM Class c
            JOIN Section sec ON c.section_id = sec.id
            WHERE c.id = :class_id
        """), {"class_id": class_id}
    ).scalar()

    # Students NOT yet in the class with section and education level info
    students = db.session.execute(
        text("""
            SELECT 
                sp.id AS student_id,
                u.first_name,
                u.last_name,
                u.school_id,
                sp.section_id,
                sec.name AS section_name,
                el.name AS education_level_name
            FROM StudentProfile sp
            JOIN Users u 
                ON sp.user_id = u.id
            LEFT JOIN ClassStudent cs 
                ON cs.student_id = sp.id 
                AND cs.class_id = :class_id
            LEFT JOIN Section sec 
                ON sp.section_id = sec.id
            LEFT JOIN EducationLevel el
                ON sp.education_level_id = el.id
            WHERE cs.id IS NULL
              AND sp.education_level_id = :edu_level
              AND (
                  u.first_name LIKE :search 
                  OR u.last_name LIKE :search 
                  OR u.school_id LIKE :search 
                  OR sec.name LIKE :search 
                  OR el.name LIKE :search
              )
            ORDER BY u.last_name, u.first_name
        """),
        {
            "class_id": class_id,
            "search": search_pattern,
            "edu_level": class_edu_level
        }
    ).fetchall()

    # Students ALREADY in the class with section info
    existing_students = db.session.execute(
        text("""
            SELECT sp.id AS student_id, u.first_name, u.last_name, u.school_id,
                   sp.section_id, sec.name AS section_name
            FROM ClassStudent cs
            JOIN StudentProfile sp ON cs.student_id = sp.id
            JOIN Users u ON sp.user_id = u.id
            LEFT JOIN Section sec ON sp.section_id = sec.id
            WHERE cs.class_id = :class_id
            ORDER BY sec.name, u.last_name, u.first_name
        """),
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
@role_required("teacher")
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

    # Delete all StudentLessonProgress entries for this student in this class
    db.session.execute(
        text(
            "DELETE FROM StudentLessonProgress WHERE class_id = :class_id AND student_id = :student_id"
        ),
        {"class_id": class_id, "student_id": student_id}
    )

    # Delete all ActivitySubmissions by this student for activities in this class
    db.session.execute(
        text("""
            DELETE FROM ActivitySubmission
            WHERE student_id = :student_id
              AND activity_id IN (
                  SELECT id FROM Activity WHERE class_id = :class_id
              )
        """),
        {"class_id": class_id, "student_id": student_id}
    )

    db.session.commit()
    flash("Student removed successfully, including all progress and submissions.", "success")
    return redirect(url_for("teacher.manage_student", class_id=class_id))

@teacher_bp.route("/lesson/progress/<int:class_id>/<string:school_id>")
@login_required
@role_required("teacher")
def student_progress(class_id, school_id):
    # 1) Resolve StudentProfile.id from Users.school_id
    sp_query = text("""
        SELECT sp.id AS student_profile_id, u.first_name, u.last_name, s.name AS section_name, sub.name AS subject_name
        FROM StudentProfile sp
        JOIN Users u ON u.id = sp.user_id
        LEFT JOIN Class c ON c.id = :class_id
        LEFT JOIN Section s ON c.section_id = s.id
        LEFT JOIN Subject sub ON c.subject_id = sub.id
        WHERE u.school_id = :school_id
        LIMIT 1
    """)
    sp_row = db.session.execute(sp_query, {"school_id": school_id, "class_id": class_id}).mappings().first()

    if not sp_row:
        flash("Student not found for the provided school ID.", "error")
        return redirect(url_for("teacher.classes"))

    student_profile_id = sp_row["student_profile_id"]

    # 2) Get lessons + student's lesson progress
    lessons_query = text("""
        SELECT 
            l.id AS lesson_id,
            l.lesson_number,
            l.title,
            l.description,
            IFNULL(slp.status, 'not_started') AS status,
            slp.started_at,
            slp.completed_at
        FROM Lesson l
        LEFT JOIN StudentLessonProgress slp 
            ON slp.lesson_id = l.id 
            AND slp.student_id = :student_profile_id
            AND slp.class_id = :class_id
        WHERE l.class_id = :class_id
        ORDER BY l.lesson_number ASC
    """)

    lessons = db.session.execute(lessons_query, {
        "class_id": class_id,
        "student_profile_id": student_profile_id
    }).mappings().all()

    # 3) Get all activities for this class + student's submissions
    activities_query = text("""
        SELECT 
            a.id AS activity_id,
            a.title AS activity_title,
            a.type AS activity_type,
            a.max_score,
            IFNULL(asub.score, 0) AS student_score
        FROM Activity a
        LEFT JOIN ActivitySubmission asub 
            ON asub.activity_id = a.id 
            AND asub.student_id = :student_profile_id
        WHERE a.class_id = :class_id
        ORDER BY a.created_at ASC
    """)

    activities = db.session.execute(activities_query, {
        "class_id": class_id,
        "student_profile_id": student_profile_id
    }).mappings().all()

    # Compute overall activity score percentage
    total_max_score = sum(a["max_score"] for a in activities)
    total_obtained_score = sum(a["student_score"] for a in activities)
    overall_activity_percentage = (
        (total_obtained_score / total_max_score * 100) if total_max_score > 0 else 0
    )

    # 4) Build student_info
    student_info = {
        "first_name": sp_row.get("first_name"),
        "last_name": sp_row.get("last_name"),
        "section_name": sp_row.get("section_name"),
        "subject_name": sp_row.get("subject_name")
    }

    # 5) Compute lesson progress
    total_lessons = len(lessons)
    completed = sum(1 for l in lessons if l["status"] == "completed")
    in_progress = sum(1 for l in lessons if l["status"] == "in_progress")
    not_started = total_lessons - completed - in_progress
    progress_percentage = (completed / total_lessons * 100) if total_lessons > 0 else 0

    # 6) Render template
    return render_template(
        "teacher/classes/student_progress.html",
        class_id=class_id,
        lessons=lessons,
        activities=activities,
        student_info=student_info,
        total_lessons=total_lessons,
        completed=completed,
        in_progress=in_progress,
        not_started=not_started,
        progress_percentage=progress_percentage,
        total_activity_score=total_obtained_score,
        total_max_score=total_max_score,
        overall_activity_percentage=overall_activity_percentage
    )

# ============================
# Manage Sections (Teacher)
# ============================
@teacher_bp.route("/sections", methods=["GET"])
@login_required
@role_required("teacher")
def manage_sections():
    """Display all sections accessible to the current teacher (by education level), with search and archive filter."""
    teacher_id = get_teacher_id()
    if not teacher_id:
        return apology("Teacher profile not found.", 404)

    # Get the teacher's education level
    teacher = db.session.execute(text("""
        SELECT tp.education_level_id
        FROM TeacherProfile tp
        WHERE tp.id = :teacher_id
    """), {"teacher_id": teacher_id}).mappings().first()

    if not teacher:
        flash("Teacher profile not found or incomplete.", "danger")
        return redirect(url_for("teacher.dashboard"))

    teacher_lvl_id = teacher.education_level_id
    show_archive = session.get("show_archive_section", False)
    search = request.args.get("search", "").strip()

    # Updated query: show all sections in the same education level as the teacher
    base_query = """
        SELECT
            sec.id AS section_id,
            sec.name AS section_name,
            sec.academic_year,
            yl.name AS year_name,
            co.name AS course_name,
            el.name AS education_level_name,
            COUNT(sp.id) AS student_count,
            tp.id AS assigned_teacher_id,
            CONCAT(u.first_name, ' ', u.last_name) AS assigned_teacher_name
        FROM Section sec
        LEFT JOIN YearLevel yl ON sec.year_id = yl.id
        LEFT JOIN Course co ON sec.course_id = co.id
        LEFT JOIN EducationLevel el ON co.education_level_id = el.id
        LEFT JOIN StudentProfile sp ON sp.section_id = sec.id
        LEFT JOIN TeacherProfile tp ON sec.teacher_id = tp.id
        LEFT JOIN Users u ON tp.user_id = u.id
        WHERE el.id = :teacher_lvl_id AND sec.teacher_id = :teacher_id
          AND sec.status = :status
    """

    params = {"teacher_lvl_id": teacher_lvl_id, "teacher_id": teacher_id, "status": 0 if show_archive else 1}

    if search:
        base_query += """
            AND (
                sec.name LIKE :search
                OR sec.academic_year LIKE :search
                OR co.name LIKE :search
                OR yl.name LIKE :search
                OR el.name LIKE :search
                OR u.first_name LIKE :search
                OR u.last_name LIKE :search
            )
        """
        params["search"] = f"%{search}%"

    base_query += """
        GROUP BY sec.id, sec.name, yl.name, co.name, el.name, sec.academic_year, sec.status, tp.id, u.first_name, u.last_name
        ORDER BY el.name, co.name, yl.name, sec.name
    """

    sections = db.session.execute(text(base_query), params).mappings().all()

    return render_template(
        "teacher/section/list.html",
        sections=sections,
        show_archive=show_archive,
        search=search
    )


# ============================
# Edit Section (Teacher)
# ============================
@teacher_bp.route("/sections/edit/<int:section_id>", methods=["GET", "POST"])
@login_required
@role_required("teacher")
def edit_section(section_id):
    """Edit section information (only if in the same education level as the teacher)."""
    teacher_id = get_teacher_id()

    # Get the teacher’s education level
    teacher = db.session.execute(text("""
        SELECT education_level_id
        FROM TeacherProfile
        WHERE id = :teacher_id
    """), {"teacher_id": teacher_id}).mappings().first()

    if not teacher:
        flash("Teacher profile not found or incomplete.", "danger")
        return redirect(url_for("teacher.manage_sections"))

    teacher_lvl_id = teacher.education_level_id

    # Fetch the section ensuring it belongs to the teacher's education level
    section = db.session.execute(text("""
        SELECT 
            s.id,
            s.name,
            s.academic_year,
            s.status,
            s.course_id,
            s.year_id,
            c.education_level_id AS education_lvl_id
        FROM Section s
        JOIN Course c ON s.course_id = c.id
        WHERE s.id = :id
          AND c.education_level_id = :teacher_lvl_id
    """), {"id": section_id, "teacher_lvl_id": teacher_lvl_id}).mappings().first()

    if not section:
        flash("Section not found or not in your education level.", "danger")
        return redirect(url_for("teacher.manage_sections"))

    # Load dropdown options
    education_levels = db.session.execute(text("SELECT id, name FROM EducationLevel")).mappings().all()

    courses = db.session.execute(text("""
        SELECT id, name FROM Course
        WHERE education_level_id = :lvl_id AND status = 1
    """), {"lvl_id": teacher_lvl_id}).mappings().all()

    year_levels = db.session.execute(text("""
        SELECT id, name FROM YearLevel
        WHERE education_level_id = :lvl_id
    """), {"lvl_id": teacher_lvl_id}).mappings().all()

    # Handle POST request (update section)
    if request.method == "POST":
        NOW = datetime.now()
        ACADEMIC_YEAR = str(NOW.year) + '-' + str((NOW.year + 1))
        name = request.form.get("name", "").strip().capitalize()
        academic_year = ACADEMIC_YEAR
        course_id = request.form.get("course_id")
        year_lvl_id = request.form.get("year_lvl_id")
        ed_lvl_id = request.form.get("education_lvl_id")
        status = request.form.get("status", "1")

        if not name or not academic_year or not year_lvl_id:
            flash("Please fill out all required fields.", "warning")
            return redirect(request.url)

        if ed_lvl_id in [3, 4] and not course_id:
            flash("Course is required for Senior High and College.", "warning")
            return redirect(url_for("admin.section_add"))
        if ed_lvl_id in [1, 2]:
            course_id = None
        
         # --- Duplicate check ---
        duplicate_query = """
            SELECT 1 FROM Section
            WHERE name = :name 
              AND academic_year = :academic_year 
              AND year_id = :year_id 
              AND education_lvl_id = :education_lvl_id
              AND (
                    (:course_id IS NULL AND course_id IS NULL) 
                    OR course_id = :course_id
                  )
        """
        duplicate = db.session.execute(
            text(duplicate_query),
            {
                "name": name,
                "academic_year": academic_year,
                "year_id": year_lvl_id,
                "education_lvl_id": ed_lvl_id,
                "course_id": course_id
            }
        ).first()

        if duplicate:
            flash("Section name already exists for this academic year and level.", "info")
            return redirect(request.url)

        try:
            db.session.execute(text("""
                UPDATE Section
                SET name = :name,
                    academic_year = :academic_year,
                    course_id = :course_id,
                    year_id = :year_lvl_id,
                    education_lvl_id = :education_lvl_id,
                    status = :status
                WHERE id = :section_id
            """), {
                "name": name,
                "academic_year": academic_year,
                "course_id": course_id,
                "year_lvl_id": year_lvl_id,
                "status": status,
                "section_id": section_id,
                "education_lvl_id": ed_lvl_id
            })
            db.session.commit()
            flash("Section updated successfully!", "success")
            return redirect(url_for("teacher.manage_sections"))
        except Exception as e:
            db.session.rollback()
            print("Error updating section:", e)
            flash("An error occurred while updating the section.", "danger")

    return render_template(
        "teacher/section/edit.html",
        section=section,
        education_levels=education_levels,
        courses=courses,
        year_levels=year_levels
    )

# ============================
# Archive / Activate Section
# ============================
@teacher_bp.route("/section/archive/<int:section_id>", methods=["POST", "GET"])
@login_required
@role_required("teacher")
def toggle_section_status(section_id):
    db.session.execute(
        text("""
            UPDATE Section
            SET status = CASE
                WHEN status = 1 THEN 0
                ELSE 1
            END
            WHERE id = :section_id
        """),
        {"section_id": section_id}
    )
    db.session.commit()
    flash("Section archive status updated.", "success")
    return redirect(url_for("teacher.manage_sections"))

# Section toggle archive
@teacher_bp.route("/section/archive")
@login_required
@role_required("teacher")
def section_archive_switch():
    session["show_archive_section"] = not session.get("show_archive_section", False)
    return redirect(url_for("teacher.manage_sections"))


# ============================
# Manage student per section
# ============================
@teacher_bp.route("/sections/<int:section_id>/students", methods=["GET", "POST"])
@login_required
@role_required("teacher")
def section_manage_students(section_id):
    """View students assigned to this section and unassigned students, with search.
       Also handles adding students to this section (POST)."""
    teacher_id = get_teacher_id()

    # Verify section belongs to this teacher
    section = db.session.execute(text("""
        SELECT * FROM Section WHERE id = :id AND teacher_id = :teacher_id
    """), {"id": section_id, "teacher_id": teacher_id}).mappings().first()

    if not section:
        flash("Section not found or not assigned to you.", "danger")
        return redirect(url_for("teacher.manage_sections"))

    # ============================
    # Handle POST (Add Students)
    # ============================
    if request.method == "POST":
        student_ids = request.form.getlist("student_ids")
        if not student_ids:
            flash("No students selected.", "warning")
            return redirect(url_for("teacher.section_manage_students", section_id=section_id))

        # Bulk update using WHERE id IN (...)
        db.session.execute(text(f"""
            UPDATE StudentProfile
            SET section_id = :section_id
            WHERE id IN :ids
        """), {"section_id": section_id, "ids": tuple(student_ids)})
        db.session.commit()

        flash(f"Added student(s) to this section.", "success")
        return redirect(url_for("teacher.section_manage_students", section_id=section_id))

    assigned_students = db.session.execute(text("""
        SELECT sp.id AS student_id, u.first_name, u.middle_name AS second_name, u.last_name, u.email, u.school_id, yl.name AS year_name
        FROM StudentProfile sp
        JOIN Users u ON sp.user_id = u.id
        LEFT JOIN YearLevel yl ON sp.year_id = yl.id
        WHERE sp.section_id = :section_id
        ORDER BY u.last_name ASC
    """), {"section_id": section_id}).mappings().all()


    search_query = request.args.get("q", "").strip()
    if search_query:
        unassigned_students = db.session.execute(text("""
            SELECT sp.id AS student_id, u.first_name, u.middle_name AS second_name, u.last_name, u.email,
                   s.name AS section_name                    
            FROM StudentProfile sp
            JOIN Users u ON sp.user_id = u.id
            LEFT JOIN Section s ON sp.section_id = s.id
            WHERE sp.section_id IS NULL
              AND (
                    CAST(sp.id AS CHAR) LIKE :search OR
                    u.first_name LIKE :search OR
                    u.middle_name LIKE :search OR
                    u.last_name LIKE :search OR
                    s.name LIKE :search
                  )
            ORDER BY u.last_name ASC
        """), {"search": f"%{search_query}%"}).mappings().all()
    else:
        unassigned_students = db.session.execute(text("""
                SELECT 
                    sp.id AS student_id, 
                    u.first_name, 
                    u.middle_name AS second_name, 
                    u.last_name, 
                    u.email,
                    s.name AS section_name, 
                    u.school_id, 
                    sp.year_id,
                    yl.name AS year_name
                FROM StudentProfile sp
                JOIN Users u ON sp.user_id = u.id
                LEFT JOIN Section s ON sp.section_id = s.id
                LEFT JOIN YearLevel yl ON sp.year_id = yl.id
                WHERE sp.section_id IS NULL 
                AND sp.education_level_id = :sec_ed_lvl
                ORDER BY u.last_name ASC
            """), {"sec_ed_lvl": section["education_lvl_id"]}).mappings().all()


    return render_template(
        "teacher/section/students.html",
        section=section,
        assigned_students=assigned_students,
        unassigned_students=unassigned_students,
        search_query=search_query
    )


@teacher_bp.route("/sections/<int:section_id>/students/remove/<int:student_id>", methods=["POST"])
@login_required
@role_required("teacher")
def remove_student_from_section(section_id, student_id):
    """Unassign a student from the section."""
    teacher_id = get_teacher_id()

    # Verify teacher owns this section
    section = db.session.execute(text("""
        SELECT id FROM Section WHERE id = :id AND teacher_id = :teacher_id
    """), {"id": section_id, "teacher_id": teacher_id}).mappings().first()

    if not section:
        flash("Unauthorized or invalid section.", "danger")
        return redirect(url_for("teacher.manage_sections"))

    # Unassign student (set section_id to NULL)
    db.session.execute(text("""
        UPDATE StudentProfile
        SET section_id = NULL
        WHERE id = :student_id
    """), {"student_id": student_id})

    db.session.commit()
    flash("Student successfully unassigned from section.", "success")
    return redirect(url_for("teacher.section_manage_students", section_id=section_id))

# ============================
# Lesson form
# ============================
@teacher_bp.route("/class/lesson/<int:lesson_id>/activity", methods=["GET", "POST"])
@login_required
@role_required("teacher")
def activity_form(lesson_id):

    # Fetch the lesson
    lesson_query = text("SELECT * FROM Lesson WHERE id = :lesson_id")
    lesson = db.session.execute(lesson_query, {"lesson_id": lesson_id}).fetchone()
    if not lesson:
        flash("Lesson not found.", "error")
        return redirect(url_for("teacher.dashboard"))

    # Check if an activity (assignment) already exists
    activity_query = text("""
        SELECT * FROM Activity WHERE lesson_id = :lesson_id AND type = 'assignment'
    """)
    activity = db.session.execute(activity_query, {"lesson_id": lesson_id}).fetchone()

    # Fetch existing uploaded files
    files = []
    if activity:
        files_query = text("SELECT * FROM ActivityFile WHERE activity_id = :aid")
        files = db.session.execute(files_query, {"aid": activity.id}).fetchall()

    if request.method == "POST":
        title = request.form.get("title")
        instructions = request.form.get("instructions")
        due_date = request.form.get("due_date")
        max_score = request.form.get("max_score", 100)

        if not title:
            flash("Title is required.", "error")
            return redirect(request.url)

        # ---------------------------
        # INSERT or UPDATE ACTIVITY
        # ---------------------------
        if activity:
            update_query = text("""
                UPDATE Activity
                SET title = :title,
                    instructions = :instructions,
                    due_date = :due_date,
                    max_score = :max_score,
                    updated_at = :updated_at
                WHERE id = :activity_id
            """)
            db.session.execute(update_query, {
                "title": title,
                "instructions": instructions,
                "due_date": due_date if due_date else None,
                "max_score": max_score,
                "updated_at": datetime.now(),
                "activity_id": activity.id
            })
            activity_id = activity.id
            flash("Assignment updated successfully.", "success")

        else:
            insert_query = text("""
                INSERT INTO Activity (class_id, lesson_id, title, instructions, type, due_date, max_score)
                VALUES (:class_id, :lesson_id, :title, :instructions, 'assignment', :due_date, :max_score)
            """)
            result = db.session.execute(insert_query, {
                "class_id": lesson.class_id,
                "lesson_id": lesson_id,
                "title": title,
                "instructions": instructions,
                "due_date": due_date if due_date else None,
                "max_score": max_score
            })
            activity_id = result.lastrowid
            flash("Assignment created successfully.", "success")

        db.session.commit()

        # ---------------------------
        # HANDLE FILE UPLOAD
        # ---------------------------
        if "files" in request.files:
            uploaded_files = request.files.getlist("files")

            if uploaded_files:
                # Create folder: /uploads/activity/<activity_id>
                upload_dir = os.path.join(current_app.root_path, "uploads", "activity", str(activity_id))
                os.makedirs(upload_dir, exist_ok=True)

                for file in uploaded_files:
                    if file and file.filename:
                        filename = secure_filename(file.filename)
                        file_path = os.path.join(upload_dir, filename)
                        file.save(file_path)

                        # Store URL path in DB for download
                        db.session.execute(text("""
                            INSERT INTO ActivityFile (activity_id, file_name, file_path)
                            VALUES (:activity_id, :file_name, :file_path)
                        """), {
                            "activity_id": activity_id,
                            "file_name": filename,
                            "file_path": f"/uploads/activity/{activity_id}/{filename}"
                        })

                db.session.commit()
                flash("Files uploaded successfully.", "success")

        return redirect(url_for("teacher.activity_form", lesson_id=lesson_id))


    return render_template(
        "teacher/classes/activity_form.html",
        activity=activity,
        lesson=lesson,
        files=files
    )


# Submission of activity in that class
@teacher_bp.route("/class/<int:class_id>/activity_list")
@login_required
@role_required("teacher")
def activity_list(class_id):
    teacher_id = current_user.id

    # Make sure this teacher owns the class
    class_check = db.session.execute(text("""
        SELECT id, subject_id, section_id
        FROM Class
        WHERE id = :class_id AND teacher_id = :teacher_id
    """), {"class_id": class_id, "teacher_id": teacher_id}).fetchone()

    # Fetch activities under this class with submission stats
    activities = db.session.execute(text("""
        SELECT 
            a.id,
            a.title,
            a.lesson_id,
            a.type,
            a.due_date,
            a.max_score,
            a.created_at,
            COALESCE(sub_count.submitted, 0) AS submitted_count,
            total_students.total AS student_count,
            COALESCE(total_students.total, 0) - COALESCE(sub_count.submitted, 0) AS not_submitted_count
        FROM Activity a
        -- Count submissions per activity
        LEFT JOIN (
            SELECT activity_id, COUNT(*) AS submitted
            FROM ActivitySubmission
            GROUP BY activity_id
        ) sub_count ON sub_count.activity_id = a.id
        -- Count total students in class
        LEFT JOIN (
            SELECT COUNT(*) AS total
            FROM ClassStudent
            WHERE class_id = :class_id
        ) total_students ON 1=1
        WHERE a.class_id = :class_id
        ORDER BY a.created_at DESC
    """), {"class_id": class_id}).fetchall()

    return render_template(
        "teacher/classes/activity_list.html",
        class_info=class_check,
        activities=activities,
        class_id=class_id
    )

@teacher_bp.route("/activity/<int:activity_id>/submissions")
@login_required
@role_required("teacher")
def view_activity_submissions(activity_id):
    teacher_id = current_user.id

    # Validate activity + class ownership
    activity = db.session.execute(text("""
        SELECT 
            a.id, a.title, a.class_id, a.due_date, a.max_score,
            c.teacher_id
        FROM Activity a
        JOIN Class c ON c.id = a.class_id
        WHERE a.id = :activity_id
    """), {"activity_id": activity_id}).fetchone()

    if not activity:
        flash("Activity not found.", "danger")
        return redirect(url_for("teacher.dashboard"))

    # Fetch all students in the class
    students = db.session.execute(text("""
        SELECT sp.id AS student_id, u.first_name, u.last_name
        FROM ClassStudent cs
        JOIN StudentProfile sp ON sp.id = cs.student_id
        JOIN Users u ON u.id = sp.user_id
        WHERE cs.class_id = :class_id
    """), {"class_id": activity.class_id}).mappings().all()

    # Fetch existing submissions including text_answer
    submissions = db.session.execute(text("""
        SELECT 
            s.id,
            s.student_id,
            s.file_name,
            s.text_answer,
            s.submitted_at,
            s.score,
            s.feedback,
            CASE
                WHEN a.due_date IS NOT NULL AND s.submitted_at > a.due_date
                    THEN 1 ELSE 0 
            END AS is_late
        FROM ActivitySubmission s
        JOIN Activity a ON a.id = s.activity_id
        WHERE s.activity_id = :activity_id
    """), {"activity_id": activity_id}).mappings().all()

    # Map submissions by student_id for easy lookup
    submissions_dict = {s['student_id']: s for s in submissions}

    # Combine: include students without submission
    all_submissions = []
    for student in students:
        sub = submissions_dict.get(student['student_id'])
        if sub:
            all_submissions.append({
                **sub,
                "first_name": student['first_name'],
                "last_name": student['last_name']
            })
        else:
            # Placeholder for not submitted
            all_submissions.append({
                "id": None,
                "student_id": student['student_id'],
                "first_name": student['first_name'],
                "last_name": student['last_name'],
                "file_name": None,
                "text_answer": None,
                "submitted_at": None,
                "score": None,
                "feedback": None,
                "is_late": 0
            })

    return render_template(
        "teacher/classes/submission_list.html",
        activity=activity,
        submissions=all_submissions
    )

@teacher_bp.route("/submission/<int:submission_id>/grade", methods=["POST"])
@login_required
@role_required("teacher")
def grade_submission(submission_id):
    teacher_id = current_user.id

    # Fetch submission + activity + class
    sub = db.session.execute(text("""
        SELECT 
            s.id,
            s.activity_id,
            s.student_id,
            a.max_score,
            a.class_id,
            c.teacher_id
        FROM ActivitySubmission s
        JOIN Activity a ON a.id = s.activity_id
        JOIN Class c ON c.id = a.class_id
        WHERE s.id = :sid
    """), {"sid": submission_id}).fetchone()

    if not sub:
        flash("Submission not found.", "danger")
        return redirect(url_for("teacher.dashboard"))

    # Get score + feedback
    score = request.form.get("score", type=int)
    feedback = request.form.get("feedback", "")

    # Validate score
    if score is None or score < 0:
        flash("Invalid score value.", "danger")
        return redirect(url_for("teacher.view_activity_submissions", activity_id=sub.activity_id))

    if score > sub.max_score:
        flash(f"Score cannot exceed {sub.max_score}.", "danger")
        return redirect(url_for("teacher.view_activity_submissions", activity_id=sub.activity_id))

    # Update submission
    db.session.execute(text("""
        UPDATE ActivitySubmission
        SET score = :score, feedback = :feedback
        WHERE id = :sid
    """), {"score": score, "feedback": feedback, "sid": submission_id})

    db.session.commit()

    flash("Grade saved successfully!", "success")
    return redirect(url_for("teacher.view_activity_submissions", activity_id=sub.activity_id))
