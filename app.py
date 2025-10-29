from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy import text, func
from helpers import *

# ==== APP SETUP ====
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
# To be replaced with random cookies
app.secret_key = "tmpsecretkey"

# ==== DATABASE CONFIG ====
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/lms_db'
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 280,
    'pool_pre_ping': True
}

db = SQLAlchemy(app)


# ==== LOGIN SETUP ====
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# ==== User class ====
class User(UserMixin):
    def __init__(self, id, email, first_name, middle_name, last_name, role, school_id, is_verified):
        self.id = id
        self.email = email
        self.first_name = first_name
        self.middle_name = middle_name
        self.last_name = last_name
        self.role = role
        self.school_id = school_id
        self.is_verified = is_verified

    @property
    def activated(self):
        return self.is_verified
    
    def get_id(self):
        return str(self.id)


@login_manager.user_loader
def load_user(user_id):
    user = db.session.execute(
        text("SELECT * FROM Users WHERE id = :id"),
        {"id": user_id}
    ).mappings().first()
    
    if user:
        return User(
            user["id"], user["email"], user["first_name"],
            user["middle_name"], user["last_name"],
            user["role"], user["school_id"], user["is_verified"]
        )
    return None

# ==== GLOBAL VARIABLES ====
DEFAULT_PASSWORD = "mcmY_1946"
ADMIN_DELETABLE_ROWS = ("Users", "Subject", "Course", "Department")

# TEST
@app.route("/testdb")
def testdb():
    tables = db.session.execute(text("SHOW TABLES")).fetchall()
    return {"tables": [t[0] for t in tables]}

# ==== GENERAL PAGES ====

# LANDING PAGE
@app.route("/")
def index():
    return render_template("index.html")

# ==== LOGIN ====
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # Query user by email
        user = db.session.execute(
            text("SELECT * FROM Users WHERE email = :email"),
            {"email": email}
        ).mappings().first()

        if user is None:
            flash("User doesn't exist.", "Error")
            return redirect(url_for("login"))

        if not check_password(password, user["password"]):
            flash("Password is incorrect.", "Error")
            return redirect(url_for("login"))

        # Create Flask-Login user object
        user_obj = User(
            user["id"], user["email"], user["first_name"],
            user["middle_name"], user["last_name"],
            user["role"], user["school_id"], user["is_verified"]
        )

        # Check if activation is required
        if not user["is_verified"]:
            login_user(user_obj)
            session.update({
                "school_id": user["school_id"],
                "role": user["role"]
            })
            return redirect(url_for("account_activation", school_id=user["school_id"]))

        # Normal login
        login_user(user_obj)
        session.update({
            "first_name": user["first_name"],
            "middle_name": user["middle_name"],
            "last_name": user["last_name"],
            "role": user["role"]
        })

        # Redirect by role
        role = session.get("role")
        if role == "admin":
            return redirect(url_for("admin"))
        elif role == "teacher":
            return redirect(url_for("teacher"))
        else:
            return redirect(url_for("student"))

    return render_template("auth/login.html")


# ACCOUNT ACTIVATION ROUTE!
@app.route("/login/account_activation/<string:school_id>", methods=["GET", "POST"])
@login_required
def account_activation(school_id):
    if request.method == "POST":
        f_name = request.form.get("first_name").title().strip() 
        l_name = request.form.get("last_name").title().strip()
        new_pwd = request.form.get("new_password")
        c_pwd = request.form.get("confirm_password")

        # Get the user info
        user = db.session.execute(
            text("SELECT * FROM Users WHERE school_id = :school_id"),
            {"school_id": school_id}
        ).mappings().first()

        if user is None:
            flash("User not found.", "error")
            return redirect(url_for("account_activation",  school_id=school_id))

        # Compare name inputs to stored data
        if not (
            user["first_name"] == f_name
            and user["last_name"] == l_name
        ):
            flash("Name doesn't match.", "error")
            return redirect(url_for("account_activation",  school_id=school_id))

        # default password comparison
        if new_pwd == DEFAULT_PASSWORD:
            flash("Default password is not vaid", "error")
            return redirect(url_for("account_activation",  school_id=school_id))
        
        if new_pwd != c_pwd:
            return apology(404, f"{new_pwd} - {c_pwd}")
            flash("Your password don't match", "error")
            return redirect(url_for("account_activation",  school_id=school_id))
        
        hashed_pwd = encrypt_password(new_pwd)

        # Update password and set account as verified
        db.session.execute(
            text("UPDATE Users SET password = :password, is_verified = 1 WHERE school_id = :school_id"),
            {"password": hashed_pwd, "school_id": school_id}
        )
        db.session.commit() 

        user_obj = User(
            user["id"], user["email"], user["first_name"],
            user["middle_name"], user["last_name"],
            user["role"], user["school_id"], user["is_verified"]
        )

        # Normal login
        login_user(user_obj)
        session.update({
            "first_name": user["first_name"],
            "middle_name": user["middle_name"],
            "last_name": user["last_name"],
            "role": user["role"]
        })

        if session["role"] == "admin":
            return redirect(url_for("admin")) 
        elif session["role"] == "teacher":
            return redirect(url_for("teacher")) 
        else:
            return redirect(url_for("student"))

    else:
        return render_template("auth/account_activation.html")

# ABOUT
@app.route("/about")
def about():
    return render_template("about.html")

# LOGOUT
@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for("index"))

@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for("login"))


# ==== ADMIN PAGES =====

@app.route("/admin")
@login_required
def admin():
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



# Student(admin side)
@app.route("/admin/student")
@login_required
def admin_student():
    show_archive = session.get("show_archive_student", False)
    query = text(f"""
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
        AcademicYear.name AS academic_year_name
    FROM Users
    JOIN StudentProfile ON Users.id = StudentProfile.user_id
    LEFT JOIN EducationLevel ON StudentProfile.education_level_id = EducationLevel.id
    LEFT JOIN Course ON StudentProfile.course_id = Course.id
    LEFT JOIN Section ON StudentProfile.section_id = Section.id
    LEFT JOIN AcademicYear ON StudentProfile.year_id = AcademicYear.id
    WHERE Users.role = 'student' {'AND Users.status = 1' if show_archive else ''}
    ORDER BY Users.last_name, Users.first_name
    """)    

    students = db.session.execute(query).mappings().all()
    return render_template("admin/student/list.html", students=students)


@app.route("/admin/student/add", methods=["POST", "GET"])
@login_required
def admin_student_add():
    if request.method == "POST":
        # Form getters

        # USER form part
        first = request.form.get("first_name").title()
        second = request.form.get("second_name").title()
        last = request.form.get("last_name").title()
        school_id = request.form.get("school_id")
        gender = request.form.get("gender").title()
        # convert school id to email
        email = f"{school_id}@holycross.edu.ph"

        if first == None or last == None or school_id == None or gender == None:
            flash("Please fill up form.", "info")
            return redirect(url_for(admin_student_add))

        # Get existing student id to avoid duplicate
        if is_exist(db, school_id, "school_id", "Users"):
            flash("The school id already exist", "info")
            return redirect(url_for("admin_student_add"))


        # First, second, and last name is already existing
        if is_exist(db, first, "first_name", "Users") and is_exist(db, second, "middle_name", "Users") and is_exist(db, last, "last_name", "Users"):
            flash("Something went wrong", "info")
            return redirect(url_for("admin_student_add"))
        
        # Add user in db
        user = add_user(db, first, second, last, email, school_id, gender, "student")
        user_id = user["id"]

        # Student Profile form part
        education_lvl = request.form.get("education_lvl")
        course_id = request.form.get("course")
        section_id = request.form.get("section")
        year_id = request.form.get("year")

        assign_student_profile(db,user_id,education_lvl,course_id,section_id, year_id)

        return redirect(url_for("admin_student_add"))

    else: 
        education_lvls = db.session.execute(text("SELECT * FROM EducationLevel")).mappings().all()
        courses = db.session.execute(text("SELECT * FROM Course")).mappings().all()
        sections = db.session.execute(text("SELECT * FROM Section")).mappings().all()
        years = db.session.execute(text("SELECT * FROM AcademicYear")).mappings().all()

        return render_template("admin/student/add_form.html", education_lvls=education_lvls, courses=courses, sections=sections, years=years)


@app.route("/admin/student/edit/<string:school_id>", methods=["POST", "GET"])
@login_required
def admin_student_edit(school_id):
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
        return redirect(url_for("admin_student"))  

    if request.method == "POST":
        # Form data
        first = request.form.get("first_name").title()
        second = request.form.get("second_name").title()
        last = request.form.get("last_name").title()
        gender = request.form.get("gender").title()
        school_id_new = request.form.get("school_id")
        education_lvl = request.form.get("education_lvl")
        course_id = request.form.get("course")
        section_id = request.form.get("section")
        year_id = request.form.get("year")

        # Email auto-update
        new_email = f"{school_id_new}@holycross.edu.ph"

        if not (first and last and gender and education_lvl and course_id and section_id and year_id):
            flash("Some parameters are missing.", "warning")
            return redirect(url_for("admin_student_edit", school_id=school_id))

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
        return redirect(url_for("admin_student", school_id=school_id))

    else:
        # GET all needed information
        education_lvls = db.session.execute(text("SELECT * FROM EducationLevel")).mappings().all()
        courses = db.session.execute(text("SELECT * FROM Course")).mappings().all()
        sections = db.session.execute(text("SELECT * FROM Section")).mappings().all()
        years = db.session.execute(text("SELECT * FROM AcademicYear")).mappings().all()

        return render_template(
            "admin/student/edit_form.html",
            student=student,
            education_lvls=education_lvls,
            courses=courses,
            sections=sections,
            years=years
        )
    
@app.route("/admin/student/archive")
@login_required
def student_archive_switch():
    # Toggle the archive visibility stored in session
    session["show_archive_student"] = not session.get("show_archive_student", False)
    return redirect(url_for("admin_student"))


# Teacher (admin side)
@app.route("/admin/teacher")
@login_required
def admin_teacher():
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
    WHERE Users.role = 'teacher' {'and Users.status = 1' if show_archive else ''}
    ORDER BY Users.last_name, Users.first_name
    """)

    teachers = db.session.execute(query).mappings().all()
    return render_template("admin/teacher/list.html", teachers=teachers)

@app.route("/admin/teacher/add", methods=["POST", "GET"])
@login_required
def admin_teacher_add():
    if request.method == "POST":
        
        # USER form part
        first = request.form.get("first_name").title()
        second = request.form.get("second_name").title()
        last = request.form.get("last_name").title()
        school_id = request.form.get("school_id")
        gender = request.form.get("gender").title()
        # convert school id to email
        email = f"{school_id}@holycross.edu.ph"

        if first == None or last == None or school_id == None or gender == None:
            flash("Please fill up form.", "info")
            return redirect(url_for(admin_teacher_add))
        
        # Get existing course to avoid duplicate
        if is_exist(db, school_id, "school_id", "Users"):
            flash("The school id already exist.", "info")
            return redirect(url_for(admin_teacher_add))
        
        # First, second, and last name is already existing
        if is_exist(db, first, "first_name", "Users") and is_exist(db, second, "middle_name", "Users") and is_exist(db, last, "last_name", "Users"):
            flash("The name already exist.", "info")
            return redirect(url_for(admin_teacher_add))

        # Add user in db
        user = add_user(db, first, second, last, email, school_id, gender, "teacher")
        user_id = user["id"]

        # teacher profile form
        department_id = request.form.get("department_id")
        lvl_id = request.form.get("lvl_id")

        assign_teacher_profile(db, user_id, department_id, lvl_id)
        return redirect(url_for("admin_teacher_add"))

    else:
        departments = db.session.execute(text("SELECT * FROM Department")).mappings().all()
        lvls = db.session.execute(text("SELECT * FROM EducationLevel")).mappings().all()
        return render_template("admin/teacher/add_form.html", departments=departments, lvls=lvls)


@app.route("/admin/teacher/edit/<string:school_id>", methods=["POST", "GET"])
@login_required
def admin_teacher_edit(school_id):
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
        return redirect(url_for("admin_teacher"))

    if request.method == "POST":
        # Get form data
        first = request.form.get("first_name").title()
        second = request.form.get("second_name").title() if request.form.get("second_name") else None
        last = request.form.get("last_name").title()
        gender = request.form.get("gender").title()
        school_id_new = request.form.get("school_id")
        department_id = request.form.get("department_id")
        lvl_id = request.form.get("lvl_id")
        reset_account = request.form.get("reset_account") == "1"

        new_email = f"{school_id_new}@holycross.edu.ph"

        if not (first and last and gender and department_id and lvl_id):
            flash("Please complete all required fields.", "warning")
            return redirect(url_for("admin_teacher_edit", school_id=school_id))

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
        return redirect(url_for("admin_teacher"))

    # GET mode - render form
    departments = db.session.execute(text("SELECT * FROM Department")).mappings().all()
    lvls = db.session.execute(text("SELECT * FROM EducationLevel")).mappings().all()

    return render_template(
        "admin/teacher/edit_form.html",
        teacher=teacher,
        departments=departments,
        lvls=lvls
    )

@app.route("/admin/teacher/archive")
@login_required
def teacher_archive_switch():
    session["show_archive_teacher"] = not session.get("show_archive_teacher", False)
    return redirect(url_for("admin_teacher"))

# course (Admin side)
@app.route("/admin/course")
@login_required
def admin_course():
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


@app.route("/admin/course/add", methods=["POST", "GET"])
@login_required
def admin_course_add():
    if request.method == "POST":
        
        # Form getters
        course_name = request.form.get("name").title().strip()
        lvl_id = request.form.get("lvl_id").title().strip() 

        # If input is none
        if course_name == None and lvl_id == None:
            flash("Please fill up form.", "info")
            return redirect(url_for("admin_course_add"))


        # Get existing course to avoid duplicate
        if is_exist(db, course_name, "name", "Course"):
            flash("The course name already exist.", "info")
            return redirect(url_for(admin_course_add))

        # Append to the courses
        add_course(db, course_name, lvl_id)

        return redirect(url_for("admin_course_add"))
    else:
        ed_lvl = db.session.execute(text("SELECT * FROM EducationLevel")).mappings().all()
        valid_course = []
        for lvl in ed_lvl:
            if lvl["name"] in ["Senior High", "College"]:
                valid_course.append(int(lvl["id"]))
        return render_template("admin/course/add_form.html", lvls=ed_lvl,valid_course=valid_course)

@app.route("/admin/course/edit/<int:id>", methods=["GET", "POST"])
@login_required
def admin_course_edit(id):
    if request.method == "POST":
        name = request.form.get("name").title().strip()
        lvl_id = request.form.get("lvl_id")

        query = text("UPDATE Course SET name = :name, education_level_id = :lvl_id WHERE id = :id")
        db.session.execute(query, {"name": name, "lvl_id": lvl_id, "id": id})
        db.session.commit()

        flash("Course updated successfully!", "success")
        return redirect(url_for("admin_course"))

    # Fetch existing course info
    query = text("""
        SELECT Course.id AS course_id, Course.name AS course_name, EducationLevel.id AS education_level_id
        FROM Course
        LEFT JOIN EducationLevel ON Course.education_level_id = EducationLevel.id
        WHERE Course.id = :id
    """)
    course = db.session.execute(query, {"id": id}).mappings().first()

    lvls = db.session.execute(text("SELECT * FROM EducationLevel")).mappings().all()

    return render_template("admin/course/edit_form.html", course=course, lvls=lvls)


# Department (admin side)
@app.route("/admin/department")
@login_required
def admin_department():
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


@app.route("/admin/department/add", methods=["POST", "GET"])
@login_required
def admin_department_add():
    if request.method == "POST":
        name = request.form.get("name").title().strip()
        lvl_id = request.form.get("lvl_id").title().strip()

        # Check if none
        if name == None or lvl_id == None:
            flash("Please fill up form.", "info")
            return redirect(url_for("admin_department_add"))

        # check if the name already exist
        if is_exist(db, name, "name", "Department"):
            flash("Department name alread exist", "info")
            return redirect(url_for("admin_department_add"))
        
        # Insert to the table
        tmp = add_department(db, name, lvl_id)

        return redirect(url_for("admin_department_add"))
        
    else:
        lvls = db.session.execute(text("SELECT * FROM EducationLevel")).mappings().all()
        return render_template("admin/department/add_form.html", lvls=lvls)

@app.route("/admin/department/edit/<int:id>", methods=["POST", "GET"])
@login_required
def admin_department_edit(id):
    if request.method == "POST":
        name = request.form.get("name").title().strip()
        lvl_id = request.form.get("lvl_id")

        query = text("""
            UPDATE Department
            SET name = :name, education_level_id = :lvl_id
            WHERE id = :id
        """)
        db.session.execute(query, {"name": name, "lvl_id": lvl_id, "id": id})
        db.session.commit()

        flash("Department updated successfully!", "success")
        return redirect(url_for("admin_department"))

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


# Subjects (admin side)
@app.route("/admin/subject")
@login_required
def admin_subject():
    query = text("""
        SELECT
            Subject.id AS subject_id,
            Subject.name AS subject_name,
            EducationLevel.name AS education_level_name
        FROM Subject
        LEFT JOIN EducationLevel ON Subject.education_level_id = EducationLevel.id
        ORDER BY Subject.name
    """)

    subjects = db.session.execute(query).mappings().all()
    return render_template("admin/subject/list.html", subjects=subjects)

@app.route("/admin/subject/add", methods=["POST", "GET"])
@login_required
def admin_subject_add():
    if request.method == "POST":
        subject_name = request.form.get("name")
        lvl = request.form.get("level")

        if not subject_name or not lvl:
            flash("Please fill up the form.", "info")
            return redirect(url_for("admin_subject_add"))
        
        subject = db.session.execute(text("SELECT * FROM Subject WHERE name=:name and education_level_id=:lvl"), {"name":subject_name, "lvl":lvl}).fetchone()
        if subject:
            flash("The subject on that level already exist.", "info")
            return redirect(url_for("admin_subject_add"))

        db.session.execute(
            text("INSERT INTO Subject (name, education_level_id) VALUES (:name, :lvl)"),
            {"name": subject_name, "lvl": lvl}
        )
        db.session.commit()
        flash("Subject added successfully!", "success")
        return redirect(url_for("admin_subject_add"))
    else:
        lvls = db.session.execute(text("SELECT * FROM EducationLevel")).mappings().all()
        flash("Successfully Added.", "Success")
        return render_template("admin/subject/add_form.html", lvls=lvls)

@app.route("/admin/subject/edit/<int:id>", methods=["POST", "GET"])
@login_required
def admin_subject_edit(id):
    if request.method == "POST":
        name = request.form.get("name").strip().title()
        lvl_id = request.form.get("lvl_id")

        if not name or not lvl_id:
            flash("Please fill up the form.", "info")
            return redirect(url_for("admin_subject_edit", id=id))

        # Update subject
        query = text("""
            UPDATE Subject
            SET name = :name, education_level_id = :lvl_id
            WHERE id = :id
        """)
        db.session.execute(query, {"name": name, "lvl_id": lvl_id, "id": id})
        db.session.commit()

        flash("Subject updated successfully!", "success")
        return redirect(url_for("admin_subject"))

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

@app.route("/admin/delete", methods=["POST"])
@login_required
def admin_delete():
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

@app.route("/admin/reset", methods=["POST"])
@login_required
def admin_reset():
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


# ==== TEACHER PAGES =====

@app.route("/teacher")
@login_required
def teacher():
    return render_template("teacher/dashboard.html", name=session["first_name"])


# ==== STUDENT PAGES =====

@app.route("/student")
@login_required
def student():
    return render_template("student/dashboard.html", name=session["first_name"])


if __name__ == "__main__": 
    app.run(debug=True)
