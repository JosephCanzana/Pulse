from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
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
# ==== GLOBAL VARIABLES ====

# TEST
@app.route("/testdb")
def testdb():
    tables = db.session.execute(text("SHOW TABLES"))
    return {"tables": tables}

# ==== GENERAL PAGES ====

# LANDING PAGE
@app.route("/")
def index():
    return render_template("index.html")

# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        
        user = db.session.execute(text("SELECT * FROM Users WHERE email = :email"), {"email": email}).mappings().first()
        if user is None:
            # For debug
            return render_template("apology.html", message=user)
        
        # is the password same as the id.password
        if password != user["password"]:
            # For debug
            return render_template("apology.html", message=user)
        
        # assign it to the current session
        session["user_id"] = user["id"]
        session["first_name"] = user["first_name"]
        session["middle_name"] = user["middle_name"]
        session["last_name"] = user["last_name"]
        session["role"] = user["role"]

        # Redirect to the user's role
        match session["role"]:
            case "admin":
                return redirect(url_for("admin"))
            case "teacher":
                return redirect(url_for("teacher"))
            case "student":
                return redirect(url_for("student"))
            case _:
                return redirect(url_for("auth/login.html"))   
            
        cur.close()
    
    else:   
        return render_template("auth/login.html")

# ABOUT
@app.route("/about")
def about():
    return render_template("about.html")

# LOGOUT
@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("index"))

# ==== ADMIN PAGES =====

@app.route("/admin")
def admin():
    return render_template("admin/dashboard.html", name=session["first_name"])


# ADMIN STUDENT LIST
@app.route("/admin/student")
def admin_student():
    query = text("""
        SELECT 
            Users.id AS user_id,
            Users.first_name,
            Users.last_name,
            Users.email,
            Users.school_id,
            StudentProfile.id AS profile_id,
            StudentProfile.course_id,
            StudentProfile.section_id,
            StudentProfile.year_id
        FROM Users
        JOIN StudentProfile ON Users.id = StudentProfile.user_id
        WHERE Users.role = 'student'
    """)
    
    students = db.session.execute(query).fetchall()
    return render_template("admin/student/list.html", students=students)


@app.route("/admin/student/add", methods=["POST", "GET"])
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

        # Get existing course to avoid duplicate
        if is_exist(db, school_id, "school_id", "StudentProfile"):
            return apology(message="It exist")

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
        education_lvls = db.session.execute(text("SELECT * FROM EducationLevel")).fetchall()
        courses = db.session.execute(text("SELECT * FROM Course")).fetchall()
        sections = db.session.execute(text("SELECT * FROM Section")).fetchall()
        years = db.session.execute(text("SELECT * FROM AcademicYear")).fetchall()

        return render_template("admin/student/add_form.html", education_lvls=education_lvls, courses=courses, sections=sections, years=years)

# ADMIN TEACHER LIST
@app.route("/admin/teacher")
def admin_teacher():
    query = text("""
        SELECT 
            Users.id AS user_id,
            Users.first_name,
            Users.last_name,
            Users.email,
            Users.school_id,
            TeacherProfile.id AS profile_id,
            TeacherProfile.education_level_id,
            TeacherProfile.department_id
        FROM Users
        JOIN TeacherProfile ON Users.id = TeacherProfile.user_id
    """)
    teachers = db.session.execute(query).fetchall()
    return render_template("admin/teacher/list.html", teachers=teachers)

@app.route("/admin/teacher/add", methods=["POST", "GET"])
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


        # Get existing course to avoid duplicate
        if is_exist(db, school_id, "school_id", "TeacherProfile"):
            return apology(message="It exist")

        # Add user in db
        user = add_user(db, first, second, last, email, school_id, gender, "student")
        user_id = user["id"]

        # teacher profile form
        department_id = request.form.get("department_id")
        lvl_id = request.form.get("lvl_id")

        assign_teacher_profile(db, user_id, department_id, lvl_id)
        return redirect(url_for("admin_teacher_add"))

    else:
        departments = db.session.execute(text("SELECT * FROM Department")).fetchall()
        lvls = db.session.execute(text("SELECT * FROM EducationLevel")).fetchall()
        return render_template("admin/teacher/add_form.html", departments=departments, lvls=lvls)


@app.route("/admin/course")
def admin_course():
    courses = db.session.execute(text("SELECT * FROM Course")).mappings().all()
    return render_template("admin/course/list.html", courses=courses)

@app.route("/admin/course/add", methods=["POST", "GET"])
def admin_course_add():
    if request.method == "POST":
        
        # Form getters
        course_name = request.form.get("name").title().strip()
        lvl_id = request.form.get("lvl_id").title().strip() 

        # Get existing course to avoid duplicate
        if is_exist(db, course_name, "name", "Course"):
            return apology(message="It exist")

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


# ==== TEACHER PAGES =====

@app.route("/teacher")
def teacher():
    return render_template("teacher/dashboard.html", name=session["first_name"])


# ==== STUDENT PAGES =====

@app.route("/student")
def student():
    return render_template("student/dashboard.html", name=session["first_name"])


if __name__ == "__main__": 
    app.run(debug=True)
