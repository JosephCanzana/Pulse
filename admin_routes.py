import re
from flask import render_template, request, redirect, url_for, session, flash, Blueprint, jsonify
from flask_login import login_required
from sqlalchemy import text
from helpers import *
from database import db

# ==== GLOBAL VARIABLES ====
DEFAULT_PASSWORD = "mcmY_1946"
ADMIN_DELETABLE_ROWS = ("Users", "Subject", "Course", "Department", "Section", "Class")

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# =======================
# API(AJAX)
# =======================
@admin_bp.route("/api/sections/search", methods=["GET"])
@login_required
def search_sections():
    """
    Search sections dynamically by education level, course, year, or section name.
    Supports partial matches for easier search.
    """
    education_lvl = request.args.get("education_level_id")
    query_text = request.args.get("q", "").strip()  # user search input

    sql = """
        SELECT Section.id, Section.name AS section_name,
               Course.name AS course_name,
               YearLevel.name AS year_name
        FROM Section
        LEFT JOIN Course ON Section.course_id = Course.id
        LEFT JOIN YearLevel ON Section.year_id = YearLevel.id
        WHERE 1=1
    """
    params = {}

    if education_lvl:
        sql += " AND YearLevel.education_level_id = :education_lvl"
        params["education_lvl"] = education_lvl

    if query_text:
        sql += """ AND (
            Section.name LIKE :q OR
            Course.name LIKE :q OR
            YearLevel.name LIKE :q
        )"""
        params["q"] = f"%{query_text}%"

    sql += " ORDER BY Section.name ASC"

    results = db.session.execute(text(sql), params).mappings().all()
    # Return combined display text for easy searching
    return jsonify([
        {"id": r["id"], "text": f"{r['course_name']} - {r['year_name']} - {r['section_name']}"}
        for r in results
    ])

# =======================
# HOME
# =======================
@admin_bp.route("/")
@login_required
def dashboard():
    # --- Summary Counts ---
    def get_count(query):
        return db.session.execute(text(query)).scalar() or 0

    total_students = get_count("SELECT COUNT(*) FROM Users WHERE role='student' AND status=1")
    archived_students = get_count("SELECT COUNT(*) FROM Users WHERE role='student' AND status=0")
    total_teachers = get_count("SELECT COUNT(*) FROM Users WHERE role='teacher' AND status=1")
    archived_teachers = get_count("SELECT COUNT(*) FROM Users WHERE role='teacher' AND status=0")
    total_courses = get_count("SELECT COUNT(*) FROM Course")
    total_departments = get_count("SELECT COUNT(*) FROM Department")
    total_subjects = get_count("SELECT COUNT(*) FROM Subject")

    # --- Recent Activity ---
    recent_students = db.session.execute(text("""
        SELECT first_name, middle_name, last_name, school_id 
        FROM Users 
        WHERE role='student' 
        ORDER BY id DESC LIMIT 5
    """)).mappings().all()

    recent_teachers = db.session.execute(text("""
        SELECT first_name, middle_name, last_name, school_id 
        FROM Users 
        WHERE role='teacher' 
        ORDER BY id DESC LIMIT 5
    """)).mappings().all()

    # --- Chart Data ---
    students_per_course = db.session.execute(text("""
        SELECT COALESCE(c.name, 'Unassigned') AS course_name, COUNT(s.id) AS student_count
        FROM StudentProfile s
        LEFT JOIN Course c ON s.course_id = c.id
        GROUP BY c.name
        ORDER BY student_count DESC
    """)).mappings().all()

    teachers_per_dept = db.session.execute(text("""
        SELECT COALESCE(d.name, 'Unassigned') AS department_name, COUNT(t.id) AS teacher_count
        FROM TeacherProfile t
        LEFT JOIN Department d ON t.department_id = d.id
        GROUP BY d.name
        ORDER BY teacher_count DESC
    """)).mappings().all()

    top_courses = db.session.execute(text("""
        SELECT 
            COALESCE(c.name, 'Unassigned') AS course_name,
            COUNT(s.id) AS total_students
        FROM StudentProfile s
        LEFT JOIN Course c ON s.course_id = c.id
        GROUP BY c.name
        ORDER BY total_students DESC
        LIMIT 5
    """)).mappings().all()


    return render_template(
        "admin/dashboard.html",
        total_students=total_students,
        archived_students=archived_students,
        total_teachers=total_teachers,
        archived_teachers=archived_teachers,
        total_courses=total_courses,
        total_departments=total_departments,
        total_subjects=total_subjects,
        recent_students=recent_students,
        recent_teachers=recent_teachers,
        students_per_course=students_per_course,
        teachers_per_dept=teachers_per_dept,
        top_courses=top_courses,
        name=session.get("first_name")
    )

# =======================
# Admin utilities
# =======================
@admin_bp.route("/delete", methods=["POST"])
@login_required
def delete():
    row_id = request.form.get("id")
    table = request.form.get("table")

    # Validate that both fields exist and have valid values
    if not row_id or not table:
        flash("Missing table or ID — cannot proceed with deletion.", "error")
        return redirect(request.referrer)

    if table not in ADMIN_DELETABLE_ROWS:
        flash("The table your trying to delete is unavailable")
        return redirect(request.referrer)

    try:
        delete_table_row(db, table, row_id)
    except:
        flash("Something went wrong.", "error")
        return redirect(request.referrer)
    flash("Successfully deleted the row.", "success")
    return redirect(request.referrer)

@admin_bp.route("/reset", methods=["POST"])
@login_required
def reset():
    row_id = request.form.get("id")
    table = request.form.get("table")

    # Validate that both fields exist and have valid values
    if not row_id or not table:
        flash("Missing table or ID — cannot proceed with deletion.", "error")
        return redirect(request.referrer)

    if table not in ADMIN_DELETABLE_ROWS:
        flash("The table your trying to reset is unavailable")
        return redirect(request.referrer)

    try:
        reset_table_row(db, table, row_id)
    except:
        flash("Something went wrong.", "error")
        return redirect(request.referrer)
    flash("Successfully reset.", "success")
    return redirect(request.referrer)

@admin_bp.route("/student")
@login_required
def student():
    show_archive = session.get("show_archive_student", False)
    search = request.args.get("search", "").strip()

    base_query = """
        SELECT 
            Users.id AS user_id,
            Users.first_name,
            Users.middle_name,
            Users.last_name,
            Users.email,
            Users.school_id,
            Users.is_verified,
            StudentProfile.id AS profile_id,
            EducationLevel.name AS education_level_name,
            Course.name AS course_name,
            Section.name AS section_name,
            YearLevel.name AS academic_year_name
        FROM Users
        JOIN StudentProfile ON Users.id = StudentProfile.user_id
        LEFT JOIN EducationLevel ON StudentProfile.education_level_id = EducationLevel.id
        LEFT JOIN Course ON StudentProfile.course_id = Course.id
        LEFT JOIN Section ON StudentProfile.section_id = Section.id
        LEFT JOIN YearLevel ON StudentProfile.year_id = YearLevel.id
        WHERE Users.role = 'student'
        AND Users.status = :status
    """

    params = {"status": 0 if show_archive else 1}

    # Add search filter if present
    if search:
        base_query += """
            AND (
                Users.first_name LIKE :search OR
                Users.middle_name LIKE :search OR
                Users.last_name LIKE :search OR
                Users.email LIKE :search OR
                Users.school_id LIKE :search
            )
        """
        params["search"] = f"%{search}%"

    base_query += " ORDER BY Users.last_name, Users.first_name"

    students = db.session.execute(text(base_query), params).mappings().all()

    return render_template("admin/student/list.html", students=students, show_archive=show_archive, search=search)

# Student add
@admin_bp.route("/student/add", methods=["POST", "GET"])
@login_required
def student_add():
    if request.method == "POST":
        first = request.form.get("first_name").capitalize()
        second = request.form.get("second_name").capitalize()
        last = request.form.get("last_name").capitalize()
        school_id = request.form.get("school_id")
        gender = request.form.get("gender").capitalize()
        email = f"{school_id}@holycross.edu.ph"

        if not all([first, last, school_id, gender]):
            flash("Please fill up the form.", "info")
            return redirect(url_for("admin.student_add"))

        if len(school_id) != 8:
            flash("The school ID must be 8 digits.", "info")
            return redirect(url_for("admin.student_add"))

        try:
            school_id = int(school_id)
        except (TypeError, ValueError):
            flash("School ID must be an integer.", "warning")
            return redirect(url_for("admin.student_add"))

        if is_exist(db, school_id, "school_id", "Users"):
            flash("The school ID already exists.", "info")
            return redirect(url_for("admin.student_add"))

        if is_exist(db, (first,second,last), "(first_name, middle_name, last_name)", "Users"):
            flash("The name already exists.", "info")
            return redirect(url_for("admin.student_add"))
        
        user = add_user(db, first, second, last, email, school_id, gender, "student")
        user_id = user["id"]

        education_lvl = request.form.get("education_lvl")
        section_id = request.form.get("section")

        if not (education_lvl and section_id):
            flash("Some fields are missing!", "warning")
            return redirect(url_for("admin.student_add"))

        # Auto-detect year and course from section
        query = text("""
            SELECT Section.course_id, Section.year_id
            FROM Section
            WHERE Section.id = :section_id
        """)
        section_info = db.session.execute(query, {"section_id": section_id}).mappings().first()

        course_id = section_info["course_id"] if section_info else None
        year_id = section_info["year_id"] if section_info else None

        assign_student_profile(db, user_id, education_lvl, course_id, section_id, year_id)

        flash("Student added successfully!", "success")
        return redirect(url_for("admin.student_add"))

    else:
        education_lvls = db.session.execute(text("SELECT * FROM EducationLevel")).mappings().all()
        sections = db.session.execute(text("SELECT * FROM Section")).mappings().all()

        return render_template("admin/student/add_form.html",
                               education_lvls=education_lvls,
                               sections=sections)

# Student edit
@admin_bp.route("/student/edit/<string:school_id>", methods=["POST", "GET"])
@login_required
def student_edit(school_id):
    # GET the school id user
    student = db.session.execute(text("""
        SELECT u.id AS user_id, u.first_name, u.middle_name, u.last_name, 
               u.school_id, u.gender, u.email, u.is_verified,
               sp.education_level_id, sp.course_id, sp.section_id, sp.year_id
        FROM Users u
        JOIN StudentProfile sp ON u.id = sp.user_id
        WHERE u.school_id = :school_id
    """), {"school_id": school_id}).mappings().first()

    if not student:
        flash("Student not found.", "warning")
        return redirect(url_for("admin.student"))  

    if request.method == "POST":
        # Form data
        first = request.form.get("first_name").capitalize()
        second = request.form.get("second_name").capitalize()
        last = request.form.get("last_name").capitalize()
        gender = request.form.get("gender").capitalize()
        school_id_new = request.form.get("school_id")
        education_lvl = request.form.get("education_lvl")
        course_id = request.form.get("course")
        section_id = request.form.get("section")
        year_id = request.form.get("year_id")

        # Email auto-update
        new_email = f"{school_id_new}@holycross.edu.ph"
        query = text("""
            SELECT Section.course_id, Section.year_id
            FROM Section
            WHERE Section.id = :section_id
        """)
        section_info = db.session.execute(query, {"section_id": section_id}).mappings().first()

        course_id = section_info["course_id"] if section_info else None
        year_id = section_info["year_id"] if section_info else None

        if not all([first, last, gender, education_lvl, section_id, year_id]):
            flash(f"{[first, last, gender, education_lvl, section_id, year_id]}Some parameters are missing.", "warning")
            return redirect(url_for("admin.student_edit", school_id=school_id))

        # --- Update Users table ---
        db.session.execute(text("""
            UPDATE Users
            SET first_name = :first,
                middle_name = :second,
                last_name = :last,
                gender = :gender,
                email = :email
            WHERE school_id = :school_id
        """), {
            "first": first,
            "second": second,
            "last": last,
            "gender": gender,
            "email": new_email,
            "school_id": school_id
        })


        # --- Update StudentProfile table ---
        db.session.execute(text("""
            UPDATE StudentProfile
            SET education_level_id = :education_lvl,
                course_id = :course_id,
                section_id = :section_id,
                year_id = :year_id
            WHERE user_id = :user_id
        """), {
            "education_lvl": education_lvl,
            "course_id": course_id,
            "section_id": section_id,
            "year_id": year_id,
            "user_id": student["user_id"]
        })

        if school_id_new != school_id:
            db.session.execute(text("UPDATE Users SET school_id = :new_id, email = :new_email WHERE school_id = :school_id"), {"new_id": school_id_new, "new_email": new_email, "school_id": school_id})


        db.session.commit()
        flash("Student record updated successfully.", "success")
        return redirect(url_for("admin.student", school_id=school_id))

    else:
        # GET all needed information
        education_lvls = db.session.execute(text("SELECT * FROM EducationLevel")).mappings().all()
        courses = db.session.execute(text("SELECT * FROM Course")).mappings().all()
        sections = db.session.execute(text("SELECT * FROM Section")).mappings().all()
        years = db.session.execute(text("SELECT * FROM YearLevel")).mappings().all()

        return render_template(
            "admin/student/edit_form.html",
            student=student,
            education_lvls=education_lvls,
            courses=courses,
            sections=sections,
            years=years
        )

# Student archive
@admin_bp.route("/student/archive/<string:school_id>", methods=["POST", "GET"])
def student_archive(school_id):
    # Toggle status (example: 1 = active, 0 = archived)
    db.session.execute(
        text("""
            UPDATE Users
            SET status = CASE 
                WHEN status = 1 THEN 0
                ELSE 1
            END
            WHERE school_id = :school_id
        """),
        {"school_id": school_id}
    )
    db.session.commit()
    return redirect(url_for("admin.student"))

# Student toggle
@admin_bp.route("/student/archive")
@login_required
def student_archive_switch():
    # Toggle the archive visibility stored in session
    session["show_archive_student"] = not session.get("show_archive_student", False)
    return redirect(url_for("admin.student"))

# =======================
# Teacher (admin side)
# =======================
@admin_bp.route("/teacher")
@login_required
def teacher():
    show_archive = session.get("show_archive_teacher", False)
    search = request.args.get("search", "").strip()

    base_query = """
        SELECT 
            Users.id AS user_id,
            Users.first_name,
            Users.middle_name,
            Users.last_name,
            Users.email,
            Users.school_id,
            Users.is_verified,
            Users.status,
            TeacherProfile.id AS profile_id,
            EducationLevel.name AS education_level_name,
            Department.name AS department_name
        FROM Users
        JOIN TeacherProfile ON Users.id = TeacherProfile.user_id
        LEFT JOIN EducationLevel ON TeacherProfile.education_level_id = EducationLevel.id
        LEFT JOIN Department ON TeacherProfile.department_id = Department.id
        WHERE Users.role = 'teacher'
        AND Users.status = :status
    """

    params = {"status": 0 if show_archive else 1}

    # search filter
    if search:
        base_query += """
            AND (
                Users.first_name LIKE :search OR
                Users.middle_name LIKE :search OR
                Users.last_name LIKE :search OR
                Users.email LIKE :search OR
                Users.school_id LIKE :search
            )
        """
        params["search"] = f"%{search}%"

    base_query += " ORDER BY Users.last_name, Users.first_name"

    teachers = db.session.execute(text(base_query), params).mappings().all()

    return render_template(
        "admin/teacher/list.html",
        teachers=teachers,
        show_archive=show_archive,
        search=search
    )

# Teacher add
@admin_bp.route("/teacher/add", methods=["POST", "GET"])
@login_required
def teacher_add():
    if request.method == "POST":
        
        # USER form part
        first = request.form.get("first_name").capitalize()
        second = request.form.get("second_name").capitalize()
        last = request.form.get("last_name").capitalize()
        school_id = request.form.get("school_id")
        gender = request.form.get("gender").capitalize()
        # convert school id to email
        email = f"{school_id}@holycross.edu.ph"

        if first == None or last == None or school_id == None or gender == None:
            flash("Please fill up form.", "info")
            return redirect(url_for("admin.teacher_add"))
        
        try:
            school_id = int(school_id)
        except (TypeError, ValueError):
            flash("School ID must be an integer", "warning")
            return redirect(url_for('admin_teacher_add'))

            
        # Get existing course to avoid duplicate
        if is_exist(db, school_id, "school_id", "Users"):
            flash("The school id already exist.", "info")
            return redirect(url_for("admin.teacher_add"))
        
        # First, second, and last name is already existing
        if is_exist(db, first, "first_name", "Users") and is_exist(db, second, "middle_name", "Users") and is_exist(db, last, "last_name", "Users"):
            flash("The name already exist.", "info")
            return redirect(url_for("admin.teacher_add"))

        # Add user in db
        user = add_user(db, first, second, last, email, school_id, gender, "teacher")
        user_id = user["id"]

        # teacher profile form
        department_id = request.form.get("department_id")
        lvl_id = request.form.get("lvl_id")

        assign_teacher_profile(db, user_id, department_id, lvl_id)
        return redirect(url_for("admin.teacher_add"))

    else:
        departments = db.session.execute(text("SELECT * FROM Department")).mappings().all()
        lvls = db.session.execute(text("SELECT * FROM EducationLevel")).mappings().all()
        return render_template("admin/teacher/add_form.html", departments=departments, lvls=lvls)

# Teacher edit
@admin_bp.route("/teacher/edit/<string:school_id>", methods=["POST", "GET"])
@login_required
def teacher_edit(school_id):
    # Get teacher info
    teacher = db.session.execute(text("""
        SELECT 
            u.id AS user_id,
            u.first_name, u.middle_name, u.last_name,
            u.school_id, u.gender, u.email, u.is_verified,
            tp.department_id, tp.education_level_id
        FROM Users u
        JOIN TeacherProfile tp ON u.id = tp.user_id
        WHERE u.school_id = :school_id
    """), {"school_id": school_id}).mappings().first()

    if not teacher:
        flash("Teacher not found.", "warning")
        return redirect(url_for("admin.teacher"))

    if request.method == "POST":
        # Get form data
        first = request.form.get("first_name").capitalize()
        second = request.form.get("second_name").capitalize() if request.form.get("second_name") else None
        last = request.form.get("last_name").capitalize()
        gender = request.form.get("gender").capitalize()
        school_id_new = request.form.get("school_id")
        department_id = request.form.get("department_id")
        lvl_id = request.form.get("lvl_id")
        reset_account = request.form.get("reset_account") == "1"

        new_email = f"{school_id_new}@holycross.edu.ph"

        if not (first and last and gender and department_id and lvl_id):
            flash("Please complete all required fields.", "warning")
            return redirect(url_for("admin.teacher_edit", school_id=school_id))

        # Update Users table
        db.session.execute(text("""
            UPDATE Users
            SET first_name = :first,
                middle_name = :second,
                last_name = :last,
                gender = :gender,
                school_id = :new_school_id,
                email = :email
            WHERE id = :user_id
        """), {
            "first": first,
            "second": second,
            "last": last,
            "gender": gender,
            "new_school_id": school_id_new,
            "email": new_email,
            "user_id": teacher["user_id"]
        })

        # Update TeacherProfile
        db.session.execute(text("""
            UPDATE TeacherProfile
            SET department_id = :department_id,
                education_level_id = :lvl_id
            WHERE user_id = :user_id
        """), {
            "department_id": department_id,
            "lvl_id": lvl_id,
            "user_id": teacher["user_id"]
        })

        # Reset account if triggered
        if reset_account:
            db.session.execute(text("""
                UPDATE Users
                SET password = :default_password, is_verified = FALSE
                WHERE id = :user_id
            """), {"default_password": DEFAULT_PASSWORD, "user_id": teacher["user_id"]})
            flash("Teacher account has been reset.", "info")

        db.session.commit()
        flash("Teacher record updated successfully.", "success")
        return redirect(url_for("admin.teacher"))

    # GET mode - render form
    departments = db.session.execute(text("SELECT * FROM Department")).mappings().all()
    lvls = db.session.execute(text("SELECT * FROM EducationLevel")).mappings().all()

    return render_template(
        "admin/teacher/edit_form.html",
        teacher=teacher,
        departments=departments,
        lvls=lvls
    )

# Teacher archive
@admin_bp.route("/teacher/archive/<string:school_id>", methods=["POST", "GET"])
def teacher_archive(school_id):
    # Toggle status (example: 1 = active, 0 = archived)
    db.session.execute(
        text("""
            UPDATE Users
            SET status = CASE 
                WHEN status = 1 THEN 0
                ELSE 1
            END
            WHERE school_id = :school_id
        """),
        {"school_id": school_id}
    )
    db.session.commit()
    return redirect(url_for("admin.teacher"))

# Teacher toggle archive
@admin_bp.route("/teacher/archive")
@login_required
def teacher_archive_switch():
    session["show_archive_teacher"] = not session.get("show_archive_teacher", False)
    return redirect(url_for("admin.teacher"))

# =======================
# Section (admin side)
# =======================
@admin_bp.route("/section")
@login_required
def section():
    show_archive = session.get("show_archive_section", False)
    search = request.args.get("search", "").strip()

    base_query = """
        SELECT 
            Section.id AS section_id,
            Section.name AS section_name,
            Section.academic_year,
            Course.name AS course_name,
            YearLevel.name AS year_name,
            EducationLevel.name AS education_level_name,
            CONCAT(Users.first_name, ' ', IFNULL(Users.middle_name,''), ' ', Users.last_name) AS teacher_name
        FROM Section
        LEFT JOIN Course ON Section.course_id = Course.id
        LEFT JOIN YearLevel ON Section.year_id = YearLevel.id
        LEFT JOIN EducationLevel ON Course.education_level_id = EducationLevel.id
        LEFT JOIN TeacherProfile ON Section.teacher_id = TeacherProfile.id
        LEFT JOIN Users ON TeacherProfile.user_id = Users.id
        WHERE Section.status = :status
    """

    params = {"status": 0 if show_archive else 1}

    # Add search filter if keyword exists
    if search:
        base_query += """
            AND (
                Section.name LIKE :search
                OR Section.academic_year LIKE :search
                OR Course.name LIKE :search
                OR YearLevel.name LIKE :search
                OR EducationLevel.name LIKE :search
                OR CONCAT(Users.first_name, ' ', IFNULL(Users.middle_name,''), ' ', Users.last_name) LIKE :search
            )
        """
        params["search"] = f"%{search}%"

    base_query += " ORDER BY Section.name"

    sections = db.session.execute(text(base_query), params).mappings().all()

    return render_template(
        "admin/section/list.html",
        sections=sections,
        show_archive=show_archive,
        search=search
    )

# Section Add
@admin_bp.route("/section/add", methods=["POST", "GET"])
@login_required
def section_add():
    if request.method == "POST":
        name = request.form.get("name", "").strip().capitalize()
        academic_year = request.form.get("academic_year", "").strip()
        ed_lvl_id = request.form.get("education_lvl_id")
        course_id = request.form.get("course_id")
        year_id = request.form.get("year_id")
        teacher_name = request.form.get("teacher_name", "").strip()
        teacher_id = request.form.get("teacher.id")

        # Convert ed_lvl_id and course_id to int if possible
        try:
            ed_lvl_id = int(ed_lvl_id)
        except (TypeError, ValueError):
            ed_lvl_id = None

        try:
            course_id = int(course_id) if course_id else None
        except (TypeError, ValueError):
            course_id = None

        if not (name and academic_year and year_id and ed_lvl_id):
            flash("All fields are required!", "warning")
            return redirect(url_for("admin.section_add"))

        # For SHS and College, course is required
        if ed_lvl_id in [3, 4] and not course_id:
            flash("Course is required for Senior High and College.", "warning")
            return redirect(url_for("admin.section_add"))

        # For Elementary and Junior High, course should be None
        if ed_lvl_id in [1, 2]:
            course_id = None

        if not re.match(r"^\d{4}-\d{4}$", academic_year):
            flash("Invalid academic year format. Use YYYY-YYYY (e.g., 2025-2026).")
            return redirect(url_for("admin.section_add"))
        
        start, end = map(int, academic_year.split('-'))
        if end != start + 1:
            flash("Academic year must be consecutive (e.g., 2025-2026).")
            return redirect(url_for("admin.section_add"))

        # Check duplicate section name in academic year
        duplicate = db.session.execute(text("""
            SELECT 1 FROM Section
            WHERE name = :name AND academic_year = :academic_year AND year_id = :year_id AND course_id = :course_id
        """), {"name": name, "academic_year": academic_year, "year_id": year_id, "course_id":course_id}).first()

        if duplicate:
            flash("Section name already exists.", "info")
            return redirect(url_for("admin.section_add"))

        # if teacher_name: 
        #     teacher = db.session.execute(text("""
        #         SELECT tp.id FROM TeacherProfile tp
        #         JOIN Users u ON tp.user_id = u.id
        #         WHERE CONCAT(u.first_name, ' ', u.middle_name, ' ', u.last_name) = :full_name
        #         AND u.status = 1 AND u.role = 'teacher'
        #     """), {"full_name": teacher_name}).first()
        #     if teacher:
        #         teacher_id = teacher.id
        #     else:
        #         flash("Teacher not found. Section will be created without a teacher.", "info")
        #         return redirect(url_for("admin.section_add"))

        if teacher_id:
            flash("Teacher not found. Section will be created without a teacher.", "info")
            return redirect(url_for("admin.section_add"))

        # Insert into Section
        db.session.execute(text("""
            INSERT INTO Section (name, academic_year, course_id, year_id, teacher_id)
            VALUES (:name, :academic_year, :course_id, :year_id, :teacher_id)
        """), {
            "name": name,
            "academic_year": academic_year,
            "course_id": course_id,
            "year_id": year_id,
            "teacher_id": teacher_id
        })

        db.session.commit()
        flash("Section added successfully!", "success")
        return redirect(url_for("admin.section_add"))


    else:
        education_lvls = db.session.execute(text("SELECT * FROM EducationLevel")).mappings().all()
        courses = db.session.execute(text("SELECT * FROM Course")).mappings().all()
        years = db.session.execute(text("SELECT * FROM YearLevel")).mappings().all()
        teachers = db.session.execute(
        text("""
            SELECT TeacherProfile.id, Users.first_name, Users.middle_name, Users.last_name
            FROM TeacherProfile
            JOIN Users ON TeacherProfile.user_id = Users.id
            WHERE Users.status = 1 AND Users.role = 'teacher'
            ORDER BY Users.last_name, Users.first_name
        """)).mappings().all()
        
        return render_template("admin/section/add_form.html", courses=courses, years=years, education_lvls=education_lvls, teachers=teachers)

# Section Edit
@admin_bp.route("/section/edit/<int:section_id>", methods=["POST", "GET"])
@login_required
def section_edit(section_id):
    section = db.session.execute(text("""
        SELECT s.*, y.id AS year_id, y.name AS year_name, y.education_level_id, e.name AS education_level_name
        FROM Section s
        LEFT JOIN YearLevel y ON s.year_id = y.id
        LEFT JOIN EducationLevel e ON y.education_level_id = e.id
        WHERE s.id = :section_id
    """), {"section_id": section_id}).mappings().first()

    if not section:
        flash("Section not found.", "warning")
        return redirect(url_for("admin.section"))

    if request.method == "POST":
        name = request.form.get("name", "").strip().capitalize()
        academic_year = request.form.get("academic_year", "").strip()
        ed_lvl_id = request.form.get("education_lvl_id")
        course_id = request.form.get("course_id")
        year_id = request.form.get("year_id")
        teacher_name = request.form.get("teacher_name", None).strip()
        teacher_id = None

        # Convert ed_lvl_id and course_id to int if possible
        try:
            ed_lvl_id = int(ed_lvl_id)
        except (TypeError, ValueError):
            ed_lvl_id = None

        try:
            course_id = int(course_id) if course_id else None
        except (TypeError, ValueError):
            course_id = None

        # Validation
        if not (name and academic_year and year_id and ed_lvl_id):
            flash("All fields are required!", "warning")
            return redirect(url_for("admin.section_edit", section_id=section_id))

        if ed_lvl_id in [3, 4] and not course_id:
            flash("Course is required for Senior High and College.", "warning")
            return redirect(url_for("admin.section_edit", section_id=section_id))

        if ed_lvl_id in [1, 2]:
            course_id = None

        # Check duplicate name excluding current section
        duplicate = db.session.execute(text("""
                SELECT 1 FROM Section
                WHERE name = :name 
                AND academic_year = :academic_year
                AND id != :section_id
            """), {"name": name, "academic_year": academic_year, "section_id": section_id}).first()


        if duplicate:
            flash("Section name already exists.", "info")
            return redirect(url_for("admin.section_edit", section_id=section_id))
        
        if teacher_name: 
            teacher = db.session.execute(text("""
                SELECT tp.id FROM TeacherProfile tp
                JOIN Users u ON tp.user_id = u.id
                WHERE CONCAT(u.first_name, ' ', u.middle_name, ' ', u.last_name) = :full_name
                AND u.status = 1 AND u.role = 'teacher'
            """), {"full_name": teacher_name}).first()
        
            if teacher:
                teacher_id = teacher.id
            else:
                flash("Teacher not found. Section will be created without a teacher.", "info")
                return redirect(url_for("admin.section_add"))

        # Update section
        db.session.execute(text("""
            UPDATE Section
            SET name = :name,
                academic_year = :academic_year,
                course_id = :course_id,
                year_id = :year_id,
                teacher_id = :teacher_id
            WHERE id = :section_id
        """), {
            "name": name,
            "academic_year": academic_year,
            "course_id": course_id,
            "year_id": year_id,
            "section_id": section_id,
            "teacher_id": teacher_id
        })
        db.session.commit()
        flash("Section updated successfully!", "success")
        return redirect(url_for("admin.section"))
    else:
        education_lvls = db.session.execute(text("SELECT * FROM EducationLevel")).mappings().all()
        courses = db.session.execute(text("SELECT * FROM Course")).mappings().all()
        years = db.session.execute(text("""
            SELECT y.id, y.name, y.education_level_id, e.name AS education_level_name
            FROM YearLevel y
            LEFT JOIN EducationLevel e ON y.education_level_id = e.id
        """)).mappings().all()

        teachers = db.session.execute(
        text("""
            SELECT TeacherProfile.id, Users.first_name, Users.middle_name, Users.last_name
            FROM TeacherProfile
            JOIN Users ON TeacherProfile.user_id = Users.id
            WHERE Users.status = 1 AND Users.role = 'teacher'
            ORDER BY Users.last_name, Users.first_name
        """)).mappings().all()

        current_teacher_name = ""
        if section['teacher_id']:
            teacher = next((t for t in teachers if t['id'] == section['teacher_id']), None)
            if teacher:
                current_teacher_name = f"{teacher['first_name']} {teacher['middle_name']} {teacher['last_name']}"

        return render_template(
            "admin/section/edit_form.html",
            section=section,
            courses=courses,
            years=years,
            education_lvls=education_lvls,
            teachers=teachers,
            current_teacher_name=current_teacher_name
        )

# Section Archive
@admin_bp.route("/section/archive/<int:section_id>", methods=["POST", "GET"])
@login_required
def section_archive(section_id):
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
    return redirect(url_for("admin.section"))

# Section toggle archive
@admin_bp.route("/section/archive")
@login_required
def section_archive_switch():
    session["show_archive_section"] = not session.get("show_archive_section", False)
    return redirect(url_for("admin.section"))

# =======================
# Course (admin side)
# =======================
@admin_bp.route("/course")
@login_required
def course():
    show_archive = session.get("show_archive_course", False)
    search = request.args.get("search", "").strip()

    base_query = """
        SELECT
            Course.id AS course_id,
            Course.name AS course_name,
            EducationLevel.name AS education_level_name
        FROM Course
        LEFT JOIN EducationLevel ON Course.education_level_id = EducationLevel.id
        WHERE Course.status = :status
    """

    params = {"status": 0 if show_archive else 1}

    if search:
        base_query += """
            AND (
                Course.name LIKE :search
                OR EducationLevel.name LIKE :search
            )
        """
        params["search"] = f"%{search}%"

    base_query += " ORDER BY Course.name"

    courses = db.session.execute(text(base_query), params).mappings().all()

    return render_template(
        "admin/course/list.html",
        courses=courses,
        show_archive=show_archive,
        search=search
    )


# Course add
@admin_bp.route("/course/add", methods=["POST", "GET"])
@login_required
def course_add():
    if request.method == "POST":
        
        # Form getters
        course_name = request.form.get("name").capitalize().strip()
        lvl_id = request.form.get("lvl_id").capitalize().strip() 

        # If input is none
        if course_name == None and lvl_id == None:
            flash("Please fill up form.", "info")
            return redirect(url_for("admin.course_add"))


        # Get existing course to avoid duplicate
        if is_exist(db, course_name, "name", "Course"):
            flash("The course name already exist.", "info")
            return redirect(url_for("admin.course_add"))

        # Append to the courses
        add_course(db, course_name, lvl_id)

        flash("Successfully added.", "success")
        return redirect(url_for("admin.course_add"))
    else:
        ed_lvl = db.session.execute(text("SELECT * FROM EducationLevel")).mappings().all()
        valid_course = []
        for lvl in ed_lvl:
            if lvl["name"] in ["Senior High", "College"]:
                valid_course.append(int(lvl["id"]))
        return render_template("admin/course/add_form.html", lvls=ed_lvl,valid_course=valid_course)

# Course edit
@admin_bp.route("/course/edit/<int:id>", methods=["GET", "POST"])
@login_required
def course_edit(id):
    if request.method == "POST":
        name = request.form.get("name").capitalize().strip()
        lvl_id = request.form.get("lvl_id")

        query = text("UPDATE Course SET name = :name, education_level_id = :lvl_id WHERE id = :id")
        db.session.execute(query, {"name": name, "lvl_id": lvl_id, "id": id})
        db.session.commit()

        flash("Course updated successfully!", "success")
        return redirect(url_for("admin.course"))

    # Fetch existing course info
    query = text("""
        SELECT Course.id AS course_id, Course.name AS course_name, EducationLevel.id AS education_level_id
        FROM Course
        LEFT JOIN EducationLevel ON Course.education_level_id = EducationLevel.id
        WHERE Course.id = :id
    """)
    course = db.session.execute(query, {"id": id}).mappings().first()

    lvls = db.session.execute(text("SELECT * FROM EducationLevel")).mappings().all()
    ed_lvl = db.session.execute(text("SELECT * FROM EducationLevel")).mappings().all()
    valid_course = []
    for lvl in ed_lvl:
        if lvl["name"] in ["Senior High", "College"]:
            valid_course.append(int(lvl["id"]))

    return render_template("admin/course/edit_form.html", course=course, lvls=lvls, valid_course=valid_course)

# Course Archive
@admin_bp.route("/course/archive/<int:course_id>", methods=["POST", "GET"])
@login_required
def course_archive(course_id):
    db.session.execute(
        text("""
            UPDATE Course
            SET status = CASE
                WHEN status = 1 THEN 0
                ELSE 1
            END
            WHERE id = :course_id
        """),
        {"course_id": course_id}
    )
    db.session.commit()
    flash("Course archive status updated.", "success")
    return redirect(url_for("admin.course"))

# Section toggle archive
@admin_bp.route("/course/archive")
@login_required
def course_archive_switch():
    session["show_archive_course"] = not session.get("show_archive_course", False)
    return redirect(url_for("admin.course"))


# =======================
# Department (admin side)
# =======================
@admin_bp.route("/department")
@login_required
def department():
    # Retrieve archive visibility setting from session
    show_archive = session.get("show_archive_department", False)

    # Get search query from request args
    search = request.args.get("search", "").strip()

    # Base query with search and EducationLevel info
    query = """
        SELECT
            Department.id AS department_id,
            Department.name AS department_name,
            EducationLevel.name AS education_level_name
        FROM Department
        LEFT JOIN EducationLevel ON Department.education_level_id = EducationLevel.id
        WHERE Department.status = :status
    """

    params = {"status": 0 if show_archive else 1}

    # Add search condition if keyword is provided
    if search:
        query += " AND (Department.name LIKE :search OR EducationLevel.name LIKE :search)"
        params["search"] = f"%{search}%"

    query += " ORDER BY Department.name"

    # Execute query
    departments = db.session.execute(text(query), params).mappings().all()

    # Label for UI clarity
    page_state_label = (
        f"Search Results for '{search}'"
        if search
        else "Archived Departments" if show_archive
        else "Active Departments"
    )

    return render_template(
        "admin/department/list.html",
        departments=departments,
        show_archive=show_archive,
        page_state_label=page_state_label,
        search=search  # so we can keep the value in the input field
    )


# Department add
@admin_bp.route("/department/add", methods=["POST", "GET"])
@login_required
def department_add():
    if request.method == "POST":
        name = request.form.get("name").capitalize().strip()
        lvl_id = request.form.get("lvl_id").capitalize().strip()

        # Check if none
        if name == None or lvl_id == None:
            flash("Please fill up form.", "info")
            return redirect(url_for("admin.department_add"))

        # check if the name already exist
        if is_exist(db, name, "name", "Department"):
            flash("Department name alread exist", "info")
            return redirect(url_for("admin.department_add"))
        
        # Insert to the table
        tmp = add_department(db, name, lvl_id)

        return redirect(url_for("admin.department_add"))
        
    else:
        lvls = db.session.execute(text("SELECT * FROM EducationLevel")).mappings().all()
        return render_template("admin/department/add_form.html", lvls=lvls)

# Department edit
@admin_bp.route("/department/edit/<int:id>", methods=["POST", "GET"])
@login_required
def department_edit(id):
    if request.method == "POST":
        name = request.form.get("name").capitalize().strip()
        lvl_id = request.form.get("lvl_id")

        query = text("""
            UPDATE Department
            SET name = :name, education_level_id = :lvl_id
            WHERE id = :id
        """)
        db.session.execute(query, {"name": name, "lvl_id": lvl_id, "id": id})
        db.session.commit()

        flash("Department updated successfully!", "success")
        return redirect(url_for("admin.department"))

    # Fetch existing department info
    query = text("""
        SELECT 
            Department.id AS department_id, 
            Department.name AS department_name, 
            EducationLevel.id AS education_level_id
        FROM Department
        LEFT JOIN EducationLevel ON Department.education_level_id = EducationLevel.id
        WHERE Department.id = :id
    """)
    department = db.session.execute(query, {"id": id}).mappings().first()

    lvls = db.session.execute(text("SELECT * FROM EducationLevel")).mappings().all()

    return render_template("admin/department/edit_form.html", department=department, lvls=lvls)

# Department Archive
@admin_bp.route("/department/archive/<int:department_id>", methods=["POST", "GET"])
@login_required
def department_archive(department_id):
    db.session.execute(
        text("""
            UPDATE Department
            SET status = CASE
                WHEN status = 1 THEN 0
                ELSE 1
            END
            WHERE id = :department_id
        """),
        {"department_id": department_id}
    )
    db.session.commit()
    flash("Department archive status updated.", "success")
    return redirect(url_for("admin.department"))

# Section toggle archive
@admin_bp.route("/department/archive")
@login_required
def department_archive_switch():
    session["show_archive_department"] = not session.get("show_archive_department", False)
    return redirect(url_for("admin.department"))


# =======================
# Subjects (admin side)
# =======================
@admin_bp.route("/subject")
@login_required
def subject():
    show_archive = session.get("show_archive_subject", False)
    search = request.args.get("search", "").strip()

    # Base SQL
    query = """
        SELECT 
            Subject.id,
            Subject.name,
            Subject.status,
            EducationLevel.name AS education_level_name
        FROM Subject
        LEFT JOIN EducationLevel ON Subject.education_level_id = EducationLevel.id
        WHERE Subject.status = :status
    """

    params = {"status": int(not show_archive)}

    # Add search condition if provided
    if search:
        query += """
            AND (
                Subject.name LIKE :search OR
                EducationLevel.name LIKE :search
            )
        """
        params["search"] = f"%{search}%"

    query += " ORDER BY Subject.name"

    subjects = db.session.execute(text(query), params).mappings().all()

    return render_template(
        "admin/subject/list.html",
        subjects=subjects,
        show_archive=show_archive,
        search=search
    )

# Subject add
@admin_bp.route("/subject/add", methods=["POST", "GET"])
@login_required
def subject_add():
    if request.method == "POST":
        subject_name = request.form.get("name")
        lvl = request.form.get("level")

        if not subject_name or not lvl:
            flash("Please fill up the form.", "info")
            return redirect(url_for("admin.subject_add"))
        
        subject = db.session.execute(text("SELECT * FROM Subject WHERE name=:name and education_level_id=:lvl"), {"name":subject_name, "lvl":lvl}).fetchone()
        if subject:
            flash("The subject on that level already exist.", "info")
            return redirect(url_for("admin.subject_add"))

        db.session.execute(
            text("INSERT INTO Subject (name, education_level_id) VALUES (:name, :lvl)"),
            {"name": subject_name, "lvl": lvl}
        )
        db.session.commit()
        flash("Subject added successfully!", "success")
        return redirect(url_for("admin.subject_add"))
    else:
        lvls = db.session.execute(text("SELECT * FROM EducationLevel")).mappings().all()
        return render_template("admin/subject/add_form.html", lvls=lvls)

# Subject edit
@admin_bp.route("/subject/edit/<int:id>", methods=["POST", "GET"])
@login_required
def subject_edit(id):
    if request.method == "POST":
        name = request.form.get("name").strip().capitalize()
        lvl_id = request.form.get("lvl_id")

        if not name or not lvl_id:
            flash("Please fill up the form.", "info")
            return redirect(url_for("admin.subject_edit", id=id))

        # Update subject
        query = text("""
            UPDATE Subject
            SET name = :name, education_level_id = :lvl_id
            WHERE id = :id
        """)
        db.session.execute(query, {"name": name, "lvl_id": lvl_id, "id": id})
        db.session.commit()

        flash("Subject updated successfully!", "success")
        return redirect(url_for("admin.subject"))

    # Fetch current subject info
    query = text("""
        SELECT 
            Subject.id AS subject_id, 
            Subject.name AS subject_name, 
            EducationLevel.id AS education_level_id
        FROM Subject
        LEFT JOIN EducationLevel ON Subject.education_level_id = EducationLevel.id
        WHERE Subject.id = :id
    """)
    subject = db.session.execute(query, {"id": id}).mappings().first()

    lvls = db.session.execute(text("SELECT * FROM EducationLevel")).mappings().all()

    return render_template("admin/subject/edit_form.html", subject=subject, lvls=lvls)

# Subject archive
@admin_bp.route("/subject/archive/<int:subject_id>", methods=["POST", "GET"])
@login_required
def subject_archive(subject_id):
    # Toggle status (1 = active, 0 = archived)
    db.session.execute(
        text("""
            UPDATE Subject
            SET status = CASE 
                WHEN status = 1 THEN 0
                ELSE 1
            END
            WHERE id = :subject_id
        """),
        {"subject_id": subject_id}
    )
    db.session.commit()
    return redirect(url_for("admin.subject"))

# Subject Archive toggle
@admin_bp.route("/subject/archive")
@login_required
def subject_archive_switch():
    # Toggle visibility flag in session
    session["show_archive_subject"] = not session.get("show_archive_subject", False)
    return redirect(url_for("admin.subject"))

# =======================
# Class Management (Admin)
# =======================
@admin_bp.route("/class", methods=["GET", "POST"])
@login_required
def class_list():
    selected_status = request.args.get("status", "active") 
    search = request.args.get("search", "").strip()

    # Base SQL
    query = """
        SELECT 
            Class.id AS class_id, 
            Class.status, 
            Users.first_name, 
            Users.last_name, 
            Subject.name AS subject_name, 
            Section.name AS section_name,
            Section.academic_year AS academic_year
        FROM Class
        LEFT JOIN TeacherProfile ON Class.teacher_id = TeacherProfile.id
        LEFT JOIN Users ON TeacherProfile.user_id = Users.id
        LEFT JOIN Subject ON Class.subject_id = Subject.id
        LEFT JOIN Section ON Class.section_id = Section.id
        WHERE 1=1
    """

    params = {}

    # Filter by class status if not "all"
    if selected_status != "all":
        query += " AND Class.status = :status"
        params["status"] = selected_status

    # Apply search if provided
    if search:
        query += """
            AND (
                Subject.name LIKE :search OR
                Section.name LIKE :search OR
                CONCAT(Users.first_name, ' ', Users.last_name) LIKE :search
            )
        """
        params["search"] = f"%{search}%"

    query += " ORDER BY Section.name, Subject.name"

    classes = db.session.execute(text(query), params).mappings().all()

    return render_template(
        "admin/class/list.html",
        classes=classes,
        selected_status=selected_status,
        search=search
    )


# Add Class
@admin_bp.route("/class/add", methods=["POST", "GET"])
@login_required
def class_add():
    if request.method == "POST":
        teacher_id = request.form.get("teacher_id")
        subject_id = request.form.get("subject_id")
        section_id = request.form.get("section_id")

        if not teacher_id or not subject_id or not section_id:
            flash("Please fill all required fields.", "info")
            return redirect(url_for("admin.class_add"))

        # Prevent duplicate class (same teacher, subject, section)
        existing = db.session.execute(
            text("SELECT * FROM Class WHERE teacher_id=:teacher AND subject_id=:subject AND section_id=:section"),
            {"teacher": teacher_id, "subject": subject_id, "section": section_id}
        ).fetchone()

        if existing:
            flash("This class already exists.", "info")
            return redirect(url_for("admin.class_add"))

        db.session.execute(
            text("""
                INSERT INTO Class (teacher_id, subject_id, section_id)
                VALUES (:teacher, :subject, :section)
            """),
            {"teacher": teacher_id, "subject": subject_id, "section": section_id}
        )
        db.session.commit()
        flash("Class added successfully!", "success")
        return redirect(url_for("admin.class_list"))

    # GET request - fetch teachers, subjects, sections
    teachers = db.session.execute(text("SELECT TeacherProfile.id, Users.first_name, Users.last_name "   
                                       "FROM TeacherProfile "
                                       "LEFT JOIN Users ON TeacherProfile.user_id = Users.id")).mappings().all()
    subjects = db.session.execute(text("SELECT * FROM Subject WHERE status=1")).mappings().all()
    sections = db.session.execute(text("SELECT * FROM Section WHERE status=1")).mappings().all()
    return render_template("admin/class/add_form.html", teachers=teachers, subjects=subjects, sections=sections)

# Edit Class
@admin_bp.route("/class/edit/<int:id>", methods=["POST", "GET"])
@login_required
def class_edit(id):
    if request.method == "POST":
        teacher_id = request.form.get("teacher_id")
        subject_id = request.form.get("subject_id")
        section_id = request.form.get("section_id")
        status = request.form.get("status")

        if not teacher_id or not subject_id or not section_id:
            flash("Please fill all required fields.", "info")
            return redirect(url_for("admin.class_edit", id=id))

        db.session.execute(
            text("""
                UPDATE Class
                SET teacher_id=:teacher, subject_id=:subject, section_id=:section,
                    status=:status
                WHERE id=:id
            """),
            {"teacher": teacher_id, "subject": subject_id, "section": section_id,
             "status": status, "id": id}
        )
        db.session.commit()
        flash("Class updated successfully!", "success")
        return redirect(url_for("admin.class_list"))

    # GET - fetch class info
    cls = db.session.execute(
        text("SELECT * FROM Class WHERE id=:id"), {"id": id}
    ).mappings().first()

    teachers = db.session.execute(text("SELECT TeacherProfile.id, Users.first_name, Users.last_name "
                                       "FROM TeacherProfile "
                                       "LEFT JOIN Users ON TeacherProfile.user_id = Users.id")).mappings().all()
    subjects = db.session.execute(text("SELECT * FROM Subject WHERE status=1")).mappings().all()
    sections = db.session.execute(text("SELECT * FROM Section WHERE status=1")).mappings().all()

    return render_template("admin/class/edit_form.html", cls=cls, teachers=teachers, subjects=subjects, sections=sections)

# Update class status
@admin_bp.route("/class/status/<int:id>", methods=["POST"])
@login_required
def class_status_update(id):
    new_status = request.form.get("status")  # Expect: 'active', 'cancelled', 'completed'
    if new_status not in ["active", "cancelled", "completed"]:
        flash("Invalid status selected.", "error")
        return redirect(url_for("admin.class_list"))

    db.session.execute(
        text("""
            UPDATE Class
            SET status = :new_status
            WHERE id = :id
        """),
        {"new_status": new_status, "id": id}
    )
    db.session.commit()
    flash("Class status updated.", "success")
    return redirect(url_for("admin.class_list"))


# Toggle showing archived classes in session
@admin_bp.route("/class/archive")
@login_required
def class_archive_switch():
    session["show_archive_class"] = not session.get("show_archive_class", False)
    return redirect(url_for("admin.class_list"))