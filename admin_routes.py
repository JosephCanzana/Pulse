from flask import Flask, render_template, request, redirect, url_for, session, flash, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy import text, func
from helpers import *
from database import db

# ==== GLOBAL VARIABLES ====
DEFAULT_PASSWORD = "mcmY_1946"
ADMIN_DELETABLE_ROWS = ("Users", "Subject", "Course", "Department", "Section")

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route("/")
@login_required
def dashboard():
    # --- Summary Counts ---
    total_students = db.session.execute(
        text("SELECT COUNT(*) AS count FROM Users WHERE role='student' AND status=1")
    ).scalar()

    archived_students = db.session.execute(
        text("SELECT COUNT(*) AS count FROM Users WHERE role='student' AND status=0")
    ).scalar()

    total_teachers = db.session.execute(
        text("SELECT COUNT(*) AS count FROM Users WHERE role='teacher' AND status=1")
    ).scalar()

    archived_teachers = db.session.execute(
        text("SELECT COUNT(*) AS count FROM Users WHERE role='teacher' AND status=0")
    ).scalar()

    total_courses = db.session.execute(
        text("SELECT COUNT(*) AS count FROM Course")
    ).scalar()

    total_departments = db.session.execute(
        text("SELECT COUNT(*) AS count FROM Department")
    ).scalar()

    total_subjects = db.session.execute(
        text("SELECT COUNT(*) AS count FROM Subject")
    ).scalar()

    # --- Recent Activity ---
    recent_students = db.session.execute(
        text("""
            SELECT first_name, middle_name, last_name, school_id 
            FROM Users 
            WHERE role='student' 
            ORDER BY id DESC LIMIT 5
        """)
    ).mappings().all()

    recent_teachers = db.session.execute(
        text("""
            SELECT first_name, middle_name, last_name, school_id 
            FROM Users 
            WHERE role='teacher' 
            ORDER BY id DESC LIMIT 5
        """)
    ).mappings().all()

    # --- Data for Charts ---
    # Students per Course
    students_per_course = db.session.execute(
        text("""
            SELECT c.name AS course_name, COUNT(s.id) AS student_count
            FROM StudentProfile s
            LEFT JOIN Course c ON s.course_id = c.id
            GROUP BY c.name
            ORDER BY student_count DESC
        """)
    ).mappings().all()

    # Teachers per Department
    teachers_per_dept = db.session.execute(
        text("""
            SELECT d.name AS department_name, COUNT(t.id) AS teacher_count
            FROM TeacherProfile t
            LEFT JOIN Department d ON t.department_id = d.id
            GROUP BY d.name
            ORDER BY teacher_count DESC
        """)
    ).mappings().all()

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

# =======================
# Student (admin side)
# =======================
@admin_bp.route("/student")
@login_required
def student():
    show_archive = session.get("show_archive_student", False)
    
    query = text("""
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
    ORDER BY Users.last_name, Users.first_name
""")

    students = db.session.execute(query, {"status": 0 if show_archive else 1}).mappings().all() 
    return render_template("admin/student/list.html", students=students, show_archive=show_archive)

# Student add
@admin_bp.route("/student/add", methods=["POST", "GET"])
@login_required
def student_add():
    if request.method == "POST":
        # Form getters

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
            return redirect(url_for("admin.student_add"))
        

        if len(school_id) != 8:
            flash("The school id must be 8 digit.", "info")
            return redirect(url_for("admin.student_add"))
        
        try:
            school_id = int(school_id)
        except (TypeError, ValueError):
            flash("School ID must be an integer", "warning")
            return redirect(url_for("admin.student_add"))


        # Get existing student id to avoid duplicate
        if is_exist(db, school_id, "school_id", "Users"):
            flash("The school id already exist", "info")
            return redirect(url_for("admin.student_add"))


        # First, second, and last name is already existing
        if is_exist(db, first, "first_name", "Users") and is_exist(db, second, "middle_name", "Users") and is_exist(db, last, "last_name", "Users"):
            flash("Something went wrong", "info")
            return redirect(url_for("admin.student_add"))
        
        # Add user in db
        user = add_user(db, first, second, last, email, school_id, gender, "student")
        user_id = user["id"]

        # Student Profile form part
        education_lvl = request.form.get("education_lvl")
        course_id = request.form.get("course")
        section_id = request.form.get("section")
        year_id = request.form.get("year")

        if not (education_lvl and course_id and section_id and year_id):
            flash("Some fields are missing!", "warning")
            return redirect(url_for("admin.student_add"))


        assign_student_profile(db,user_id,education_lvl,course_id,section_id, year_id)

        return redirect(url_for("admin.student_add"))

    else: 
        education_lvls = db.session.execute(text("SELECT * FROM EducationLevel")).mappings().all()
        courses = db.session.execute(text("SELECT * FROM Course")).mappings().all()
        sections = db.session.execute(text("SELECT * FROM Section")).mappings().all()
        years = db.session.execute(text("SELECT * FROM YearLevel")).mappings().all()

        return render_template("admin/student/add_form.html", education_lvls=education_lvls, courses=courses, sections=sections, years=years)

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
        year_id = request.form.get("year")

        # Email auto-update
        new_email = f"{school_id_new}@holycross.edu.ph"

        if not (first and last and gender and education_lvl and course_id and section_id and year_id):
            flash("Some parameters are missing.", "warning")
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
    query = text(f"""
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
        AND Users.status = {0 if show_archive else 1}
        ORDER BY Users.last_name, Users.first_name
    """)

    teachers = db.session.execute(query).mappings().all()

    return render_template("admin/teacher/list.html", teachers=teachers, show_archive=show_archive)

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

    query = text("""
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
    ORDER BY Section.name
""")


    status = 0 if show_archive else 1  # 0 = archived, 1 = active
    sections = db.session.execute(query, {"status": status}).mappings().all()
    
    return render_template(
        "admin/section/list.html",
        sections=sections,
        show_archive=show_archive
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


        # Check duplicate section name in academic year
        duplicate = db.session.execute(text("""
            SELECT 1 FROM Section
            WHERE name = :name AND academic_year = :academic_year 
        """), {"name": name, "academic_year": academic_year}).first()

        if duplicate:
            flash("Section name already exists.", "info")
            return redirect(url_for("admin.section_add"))

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
    query = text("""
        SELECT
            Course.id AS course_id,
            Course.name AS course_name,
            EducationLevel.name AS education_level_name
        FROM Course
        LEFT JOIN EducationLevel ON Course.education_level_id = EducationLevel.id
        ORDER BY Course.name
    """)

    courses = db.session.execute(query).mappings().all()
    return render_template("admin/course/list.html", courses=courses)

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


# =======================
# Department (admin side)
# =======================
@admin_bp.route("/department")
@login_required
def department():
    query = text("""
        SELECT
            Department.id AS department_id,
            Department.name AS department_name,
            EducationLevel.name AS education_level_name
        FROM Department
        LEFT JOIN EducationLevel ON Department.education_level_id = EducationLevel.id
        ORDER BY Department.name
    """)

    departments = db.session.execute(query).mappings().all()
    return render_template("admin/department/list.html", departments=departments)

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


# =======================
# Subjects (admin side)
# TODO: Teacher assign
# =======================
@admin_bp.route("/subject")
@login_required
def subject():
    show_archive = session.get("show_archive_subject", False)
    query = text("""
        SELECT 
            Subject.id,
            Subject.name,
            Subject.status,
            EducationLevel.name AS education_level_name
        FROM Subject
        LEFT JOIN EducationLevel ON Subject.education_level_id = EducationLevel.id
        WHERE Subject.status = :status
        ORDER BY Subject.name
    """)
    
    subjects = db.session.execute(query, {"status": int(not show_archive)}).fetchall()
    return render_template("admin/subject/list.html", subjects=subjects, show_archive=show_archive)

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