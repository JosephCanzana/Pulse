from flask import render_template, session, Blueprint, flash, request, url_for, redirect
from flask_login import login_required, current_user
from sqlalchemy import text
from helpers import *
from database import db
from datetime import datetime
from decorators import role_required
from werkzeug.utils import secure_filename
import os
student_bp = Blueprint('student', __name__, url_prefix='/student')

# ==============================
# Dashboard
# ==============================
@student_bp.route("/")
@login_required
@role_required("student")
def dashboard():
    # Main summary counts
    summary_query = text("""
        SELECT 
            COUNT(DISTINCT cs.id) AS total_classes,
            COUNT(DISTINCT CASE WHEN c.status = 'completed' THEN cs.id END) AS total_classes_completed,
            COUNT(DISTINCT CASE WHEN c.status = 'active' THEN cs.id END) AS total_classes_active,
            COUNT(DISTINCT CASE WHEN sl.status = 'completed' THEN sl.id END) AS total_lessons_completed,
            COUNT(DISTINCT CASE WHEN sl.status = 'in_progress' THEN sl.id END) AS lessons_in_progress
        FROM StudentProfile sp
        LEFT JOIN ClassStudent cs 
            ON cs.student_id = sp.id
        LEFT JOIN Class c 
            ON c.id = cs.class_id
            AND c.status = 'active'        
        LEFT JOIN StudentLessonProgress sl 
            ON sl.student_id = sp.id
            AND sl.class_id = c.id        
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

    points_query = text("""
    SELECT 
        sp.points,
        tl.name AS trophy_name
    FROM StudentProfile sp
    LEFT JOIN TrophyLevel tl 
        ON tl.required_points = (
            SELECT MAX(required_points)
            FROM TrophyLevel
            WHERE required_points <= sp.points
        )
    WHERE sp.user_id = :user_id
""")

    result_trophy = db.session.execute(points_query, {"user_id": current_user.id}).fetchone()
    points = result_trophy.points if result_trophy else 0
    trophy_name = result_trophy.trophy_name if result_trophy else None


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
        daily=daily,
        points=points,
        trophy_name=trophy_name
    )


# ==============================
# View Enrolled Classes
# ==============================
@student_bp.route("/classes")
@login_required
@role_required("student")
def view_classes():
    query = text("""
        SELECT 
            c.id,
            s.name AS subject_name,
            sec.name AS section_name,
            cs.status AS enrollment_status,
            c.status AS class_status,
            c.color,
            t.user_id AS teacher_user_id,
            CONCAT(u.first_name, ' ', u.last_name) AS teacher_name,
            COUNT(l.id) AS total_lessons,
            SUM(CASE WHEN slp.status = 'completed' THEN 1 ELSE 0 END) AS completed_lessons
        FROM ClassStudent cs
        JOIN Class c ON cs.class_id = c.id
        JOIN Subject s ON c.subject_id = s.id
        JOIN Section sec ON c.section_id = sec.id
        JOIN TeacherProfile t ON c.teacher_id = t.id
        JOIN Users u ON t.user_id = u.id
        JOIN StudentProfile sp ON cs.student_id = sp.id
        LEFT JOIN Lesson l ON l.class_id = c.id
        LEFT JOIN StudentLessonProgress slp 
            ON slp.lesson_id = l.id AND slp.student_id = sp.id
        WHERE sp.user_id = :user_id
        GROUP BY c.id, s.name, sec.name, cs.status, c.status, c.color, t.user_id, u.first_name, u.last_name
    """)
    
    all_classes = db.session.execute(query, {'user_id': current_user.id}).fetchall()

    # Add progress percentage
    classes_with_progress = []
    for c in all_classes:
        total = c.total_lessons or 0
        completed = c.completed_lessons or 0
        progress = (completed / total * 100) if total > 0 else 0
        # Use c._mapping to convert Row to dict
        classes_with_progress.append({
            **c._mapping,
            'progress_percentage': round(progress)
        })

    # Separate active vs history
    active_classes = [c for c in classes_with_progress if c['class_status'] == 'active']
    history_classes = [c for c in classes_with_progress if c['class_status'] in ('completed', 'cancelled')]

    return render_template(
        "student/classes.html",
        active_classes=active_classes,
        history_classes=history_classes
    )


# ==============================
# View Lessons in a Class 
# ==============================
@student_bp.route("/classes/<int:class_id>/lessons")
@login_required
@role_required("student")
def view_lessons(class_id):
    # Get class status
    class_status = db.session.execute(
        text("SELECT status FROM Class WHERE id = :class_id"),
        {'class_id': class_id}
    ).scalar()

    # Get class info including current student's enrollment status
    class_info = db.session.execute(
        text("""
            SELECT 
                c.id,
                c.teacher_id,
                c.subject_id,
                c.section_id,
                c.status AS class_status,
                c.color,
                c.created_at,
                c.updated_at,
                t.user_id AS teacher_user_id,
                s.name AS subject_name,
                sec.name AS section_name,
                cs.status AS enrollment_status 
            FROM Class c
            LEFT JOIN TeacherProfile t ON c.teacher_id = t.id
            LEFT JOIN Subject s ON c.subject_id = s.id
            LEFT JOIN Section sec ON c.section_id = sec.id
            LEFT JOIN ClassStudent cs 
                ON cs.class_id = c.id 
                AND cs.student_id = (SELECT id FROM StudentProfile WHERE user_id = :user_id)
            WHERE c.id = :class_id
        """), {'class_id': class_id, 'user_id': current_user.id}
    ).mappings().first()

    # Get student profile ID
    student_profile_id = db.session.execute(
        text("SELECT id FROM StudentProfile WHERE user_id = :user_id"),
        {'user_id': current_user.id}
    ).scalar()
    if not student_profile_id:
        flash("Student profile not found.", "danger")
        return redirect(url_for("student_bp.dashboard"))
    # Ensure StudentLessonProgress entries exist for any new lessons
    lesson_rows = db.session.execute(
        text("SELECT id FROM Lesson WHERE class_id = :class_id"),
        {'class_id': class_id}
    ).mappings().all()

    lesson_ids = [row['id'] for row in lesson_rows]

    if not lesson_ids:
        return render_template(
            "student/lessons.html",
            lessons=[],                # no lessons
            class_id=class_id,
            class_status=class_status,
            class_info=class_info,
            progress_summary={
                'total': 0,
                'completed': 0,
                'in_progress': 0,
                'not_started': 0
            },
            activities_summary={
                'total': 0,
                'passed': 0,
                'not_passed': 0
            },
            overall_score=0,
            total_possible=0
        )


    lesson_ids = [row['id'] for row in lesson_rows]

    if lesson_ids:
        # Existing progress for this student
        existing_progress_rows = db.session.execute(
            text("""
                SELECT lesson_id FROM StudentLessonProgress
                WHERE class_id = :class_id AND student_id = :student_id
            """),
            {'class_id': class_id, 'student_id': student_profile_id}
        ).mappings().all()

        existing_progress = {row['lesson_id'] for row in existing_progress_rows}

        # Only insert missing progress for new lessons
        missing_lessons = set(lesson_ids) - existing_progress
        if missing_lessons:
            for lid in missing_lessons:
                db.session.execute(
                    text("""
                        INSERT INTO StudentLessonProgress (class_id, lesson_id, student_id, status)
                        VALUES (:class_id, :lesson_id, :student_id, 'not_started')
                    """),
                    {'class_id': class_id, 'lesson_id': lid, 'student_id': student_profile_id}
                )
            db.session.commit()

        # Fetch lessons with progress and activity info (duplicate-free)
        lessons = db.session.execute(
        text("""
            SELECT 
                l.id AS lesson_id, 
                l.lesson_number, 
                l.title, 
                l.description,

                slp.status AS progress_status, 
                slp.completed_at, 
                slp.started_at,

                -- Single file per lesson
                lf.file_id,
                lf.file_name,
                lf.file_path,
                lf.file_type,

                -- Single activity per lesson
                a.activity_id,
                a.activity_title,
                a.activity_due,

                -- Submission info
                s.score AS activity_score,
                s.submitted_at AS activity_submitted_at,

                -- Final unified submission status
                CASE 
                    WHEN s.submitted_at IS NULL THEN 'not_submitted'
                    WHEN s.score IS NULL THEN 'submitted_not_graded'
                    WHEN s.score >= 1 THEN 'passed'
                    ELSE 'failed'
                END AS submission_status

            FROM Lesson l

            LEFT JOIN StudentLessonProgress slp 
                ON l.id = slp.lesson_id 
                AND slp.student_id = :student_id

            -- Aggregate files to return only one per lesson
            LEFT JOIN (
                SELECT lesson_id, MAX(id) AS file_id, MAX(file_name) AS file_name,
                    MAX(file_path) AS file_path, MAX(file_type) AS file_type
                FROM LessonFile
                GROUP BY lesson_id
            ) lf ON l.id = lf.lesson_id

            -- Aggregate assignments to return only one per lesson
            LEFT JOIN (
                SELECT lesson_id, MAX(id) AS activity_id, MAX(title) AS activity_title,
                    MAX(due_date) AS activity_due
                FROM Activity
                WHERE type = 'assignment'
                GROUP BY lesson_id
            ) a ON l.id = a.lesson_id

            -- Get submission info (only 1 row per activity/student)
            LEFT JOIN (
                SELECT activity_id, student_id, MAX(score) AS score, MAX(submitted_at) AS submitted_at
                FROM ActivitySubmission
                WHERE student_id = :student_id
                GROUP BY activity_id, student_id
            ) s ON a.activity_id = s.activity_id

            WHERE l.class_id = :class_id
            ORDER BY l.lesson_number ASC
        """),
        {'student_id': student_profile_id, 'class_id': class_id}
    ).mappings().all()


    # Lesson progress summary
    total_lessons = len(lessons)
    completed_count = sum(1 for l in lessons if l['progress_status'] == 'completed')
    in_progress_count = sum(1 for l in lessons if l['progress_status'] == 'in_progress')
    not_started_count = sum(1 for l in lessons if l['progress_status'] == 'not_started')
    
    progress_summary = {
        'total': total_lessons,
        'completed': completed_count,
        'in_progress': in_progress_count,
        'not_started': not_started_count
    }

    # Activity summary
    submissions = [l['activity_score'] for l in lessons if l['activity_id']]
    activities_summary = {
        'total': len(submissions),
        'passed': sum(1 for s in submissions if s is not None and s > 0),
        'not_passed': sum(1 for s in submissions if s is None or s == 0)
    }

    # Overall score
    overall = db.session.execute(
        text("""
            SELECT SUM(s.score) AS total_score, SUM(a.max_score) AS total_possible
            FROM Activity a
            LEFT JOIN ActivitySubmission s ON a.id = s.activity_id AND s.student_id = :student_id
            WHERE a.class_id = :class_id
        """), {'student_id': student_profile_id, 'class_id': class_id}
    ).mappings().first()
    overall_score = overall['total_score'] or 0
    total_possible = overall['total_possible'] or 0

    # Flash info
    if class_status in ('completed', 'cancelled'):
        flash("This class is no longer active. You can view it in your history, but cannot update progress.", "info")
    elif class_info.enrollment_status == 'dropped':
        flash("You have dropped this class. Lessons are hidden and cannot be accessed.", "info")
    elif class_info.enrollment_status == 'completed':
        flash("You are marked as completed.", "info")

    return render_template(
        "student/lessons.html",
        lessons=lessons,
        class_id=class_id,
        class_status=class_status,
        class_info=class_info,
        progress_summary=progress_summary,
        activities_summary=activities_summary,
        overall_score=overall_score,
        total_possible=total_possible
    )

# ==============================
# Update Lesson Progress (Incremental)
# ==============================
@student_bp.route("/lessons/<int:lesson_id>/progress", methods=["POST"])
@login_required
@role_required("student")
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
            # Update lesson progress
            db.session.execute(update, {'id': progress.id, 'status': next_status})

            # POINT SYSTEM
            result = db.session.execute(
                text("SELECT points FROM StudentProfile WHERE id = :student_id"),
                {"student_id": student.id}
            )
            current_point = result.scalar() or 0  # get the integer value safely

            # increment points
            new_points = current_point + 1

            db.session.execute(
                text("UPDATE StudentProfile SET points = :points WHERE id = :student_id"),
                {"student_id": student.id, "points": new_points}
            )


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
    flash(f"Lesson progress updated to {next_status.replace("_", " ")}!", "success")
    return redirect(request.referrer or url_for("student.dashboard"))


@student_bp.route("/history")
@login_required
@role_required("student")
def history():
    search = request.args.get("search", "").strip().lower()
    
    # Base query
    query = text("""
        SELECT 
            c.id,
            s.name AS subject_name,
            sec.name AS section_name,
            CONCAT(u.first_name, ' ', u.last_name) AS teacher_name,
            c.status AS class_status,
            cs.status AS enrollment_status,
            c.color,
            COUNT(l.id) AS total_lessons,
            SUM(CASE WHEN slp.status = 'completed' THEN 1 ELSE 0 END) AS completed_lessons
        FROM ClassStudent cs
        JOIN Class c ON cs.class_id = c.id
        JOIN Subject s ON c.subject_id = s.id
        JOIN Section sec ON c.section_id = sec.id
        JOIN TeacherProfile tp ON c.teacher_id = tp.id
        JOIN Users u ON tp.user_id = u.id
        JOIN StudentProfile sp ON cs.student_id = sp.id
        LEFT JOIN Lesson l ON l.class_id = c.id
        LEFT JOIN StudentLessonProgress slp 
            ON slp.lesson_id = l.id AND slp.student_id = sp.id
        WHERE sp.user_id = :user_id
          AND c.status IN ('completed', 'cancelled')
        GROUP BY c.id, s.name, sec.name, u.first_name, u.last_name, c.status, cs.status, c.color
    """)

    classes = db.session.execute(query, {"user_id": current_user.id}).mappings().all()

    # Filter search after fetching
    if search:
        classes = [
            c for c in classes 
            if search in c['subject_name'].lower() 
               or search in c['section_name'].lower()
               or search in c['teacher_name'].lower()
        ]

    # Add progress percentage
    classes_with_progress = []
    for c in classes:
        total = c['total_lessons'] or 0
        completed = c['completed_lessons'] or 0
        progress = (completed / total * 100) if total > 0 else 0
        classes_with_progress.append({
            **c,
            "progress_percentage": round(progress)
        })

    return render_template("student/history.html", history_classes=classes_with_progress)


# ==============================
# View activity
# ==============================
@student_bp.route("/activity/<int:activity_id>")
@login_required
@role_required("student")
def view_activity(activity_id):
    # Get student profile ID
    student_profile_query = text("SELECT id FROM StudentProfile WHERE user_id = :user_id")
    student_profile_id = db.session.execute(student_profile_query, {"user_id": current_user.id}).scalar()
    if not student_profile_id:
        flash("Student profile not found.", "danger")
        return redirect(url_for("student_bp.dashboard"))

    # Fetch activity
    activity_query = text("""
        SELECT 
            a.id,
            a.title,
            a.instructions,
            a.due_date,
            a.max_score,
            a.lesson_id,
            l.title AS lesson_title,
            c.id AS class_id
        FROM Activity a
        LEFT JOIN Lesson l ON a.lesson_id = l.id
        LEFT JOIN Class c ON l.class_id = c.id
        WHERE a.id = :activity_id AND a.type = 'assignment'
    """)

    activity = db.session.execute(activity_query, {"activity_id": activity_id}).mappings().first()
    if not activity:
        flash("Assignment not found.", "error")
        return redirect(url_for("student_bp.dashboard"))

    # Fetch existing submission if any
    submission_query = text("""
        SELECT * FROM ActivitySubmission
        WHERE activity_id = :activity_id AND student_id = :student_id
    """)
    submission = db.session.execute(submission_query, {
        "activity_id": activity_id,
        "student_id": student_profile_id
    }).mappings().first()

        # Fetch teacher-uploaded files for this activity
    teacher_files_query = text("""
        SELECT * FROM ActivityFile
        WHERE activity_id = :activity_id
    """)
    teacher_files = db.session.execute(teacher_files_query, {"activity_id": activity_id}).mappings().all()


    return render_template(
        "student/activity.html",
        activity=activity,
        submission=submission,
        teacher_files=teacher_files
    )


@student_bp.route("/activity/<int:activity_id>/submit", methods=["POST"])
@login_required
@role_required("student")
def submit_activity(activity_id):
    # Get student profile ID
    student_profile_query = text("SELECT id FROM StudentProfile WHERE user_id = :user_id")
    student_profile_id = db.session.execute(student_profile_query, {"user_id": current_user.id}).scalar()
    if not student_profile_id:
        flash("Student profile not found.", "danger")
        return redirect(url_for("student_bp.dashboard"))

    # Fetch activity to verify it exists
    activity_query = text("SELECT * FROM Activity WHERE id = :activity_id AND type = 'assignment'")
    activity = db.session.execute(activity_query, {"activity_id": activity_id}).mappings().first()
    if not activity:
        flash("Assignment not found.", "error")
        return redirect(url_for("student_bp.dashboard"))

    # Get form data
    text_answer = request.form.get("text_answer", None)
    file = request.files.get("file", None)
    file_path = None
    file_name = None

    # Handle file upload with renaming
    if file and file.filename:
        original_filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")  # e.g., 20251115_071230
        new_filename = f"{student_profile_id}_{activity_id}_{timestamp}_{original_filename}"
        upload_folder = os.path.join("uploads", "activities", str(activity_id))
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, new_filename)
        file.save(file_path)
        file_name = new_filename

    # Check if submission already exists
    submission_query = text("""
        SELECT * FROM ActivitySubmission
        WHERE activity_id = :activity_id AND student_id = :student_id
    """)
    submission = db.session.execute(submission_query, {
        "activity_id": activity_id,
        "student_id": student_profile_id
    }).mappings().first()

    now = datetime.now()

    if submission:
        # Update existing submission
        update_query = text("""
            UPDATE ActivitySubmission
            SET text_answer = :text_answer,
                file_path = :file_path,
                file_name = :file_name,
                submitted_at = :submitted_at
            WHERE id = :submission_id
        """)
        db.session.execute(update_query, {
            "text_answer": text_answer,
            "file_path": file_path if file_path else submission.file_path,
            "file_name": file_name if file_name else submission.file_name,
            "submitted_at": now,
            "submission_id": submission.id
        })
        flash("Assignment submission updated successfully.", "success")
    else:
        # Insert new submission
        insert_query = text("""
            INSERT INTO ActivitySubmission
            (activity_id, student_id, text_answer, file_path, file_name, submitted_at)
            VALUES (:activity_id, :student_id, :text_answer, :file_path, :file_name, :submitted_at)
        """)
        db.session.execute(insert_query, {
            "activity_id": activity_id,
            "student_id": student_profile_id,
            "text_answer": text_answer,
            "file_path": file_path,
            "file_name": file_name,
            "submitted_at": now
        })
        flash("Assignment submitted successfully.", "success")

    db.session.commit()
    return redirect(url_for("student.view_activity", activity_id=activity_id))

@student_bp.route("/grades")
@login_required
@role_required("student")
def grade_overview():
    """Show all ACTIVE classes with total grades for the logged-in student."""

    # Get the student profile ID from the logged-in user
    student_profile = db.session.execute(
        text("SELECT id FROM StudentProfile WHERE user_id = :user_id"),
        {"user_id": current_user.id}
    ).mappings().first()

    if not student_profile:
        flash("Student profile not found.", "error")
        return redirect(url_for("student.dashboard"))

    student_profile_id = student_profile["id"]

    # Fetch active classes the student is enrolled in
    classes_query = text("""
        SELECT 
            c.id AS class_id,
            s.name AS subject_name,
            sec.name AS section_name,
            co.name AS course_name,
            COALESCE(el_from_course.name, el_from_year.name) AS education_level
        FROM ClassStudent cs
        JOIN Class c ON cs.class_id = c.id
        JOIN Subject s ON c.subject_id = s.id
        JOIN Section sec ON c.section_id = sec.id
        LEFT JOIN Course co ON sec.course_id = co.id
        LEFT JOIN EducationLevel el_from_course ON co.education_level_id = el_from_course.id
        LEFT JOIN YearLevel yl ON sec.year_id = yl.id
        LEFT JOIN EducationLevel el_from_year ON yl.education_level_id = el_from_year.id
        WHERE cs.student_id = :student_profile_id
          AND c.status = 'active'         
        ORDER BY s.name
    """)
    enrolled_classes = db.session.execute(classes_query, {"student_profile_id": student_profile_id}).mappings().all()

    # Compute total grades for each class
    classes_with_grades = []
    for cls in enrolled_classes:
        grade_query = text("""
            SELECT
                COALESCE(SUM(asub.score), 0) AS total_score,
                COALESCE(SUM(a.max_score), 0) AS max_score
            FROM Activity a
            LEFT JOIN ActivitySubmission asub
                ON asub.activity_id = a.id
                AND asub.student_id = :student_profile_id
            WHERE a.class_id = :class_id
        """)
        grade_result = db.session.execute(grade_query, {
            "student_profile_id": student_profile_id,
            "class_id": cls["class_id"]
        }).mappings().first()

        total_score = grade_result["total_score"]
        max_score = grade_result["max_score"]
        overall_percentage = (total_score / max_score * 100) if max_score > 0 else None

        cls_dict = dict(cls)
        cls_dict["total_score"] = total_score
        cls_dict["max_score"] = max_score
        cls_dict["overall_percentage"] = round(overall_percentage, 1) if overall_percentage is not None else None

        classes_with_grades.append(cls_dict)

    return render_template("student/grade_overview.html", classes=classes_with_grades)

