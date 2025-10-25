from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
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
            return apology(404, "User doesn't exist.")

        if not check_password(password, user["password"]):
            flash(("error", "Password is incorrect."))
            return redirect(url_for("login"))

        # Create Flask-Login user object
        user_obj = User(
            user["id"], user["email"], user["first_name"],
            user["middle_name"], user["last_name"],
            user["role"], user["school_id"], user["is_verified"]
        )

        # Check if activation is required
        if not user["is_verified"] or user["password"] == DEFAULT_PASSWORD:
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
        new_pwd = request.form.get("password")

        user = db.session.execute(
            text("SELECT * FROM Users WHERE school_id = :school_id"),
            {"school_id": school_id}
        ).mappings().first()

        if user is None:
            return apology(404, "User not found.")

        # Compare name inputs to stored data
        if not (
            user["first_name"] == f_name
            and user["last_name"] == l_name
        ):
            return apology(409, "It seems like your name is wrong!")
        
        if new_pwd == DEFAULT_PASSWORD:
            return apology(409, "Default password is not valid!")
        
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
    return render_template("admin/dashboard.html", name=session["first_name"])


# Student(admin side)
@app.route("/admin/student")
@login_required
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

        # Get existing student id to avoid duplicate
        if is_exist(db, school_id, "school_id", "Users"):
            return apology(409, "The school id already exist.")

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

# Teacher (admin side)
@app.route("/admin/teacher")
@login_required
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
    teachers = db.session.execute(query).mappings().all()
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
        if is_exist(db, school_id, "school_id", "Users"):
            return apology(409,"The school id already exist")
        
        # First, second, and last name is already existing
        if is_exist(db, first, "first_name", "Users") and is_exist(db, second, "middle_name", "Users") and is_exist(db, last, "last_name", "Users"):
            return apology(409, "The name already exist.")


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


# course (Admin side)
@app.route("/admin/course")
@login_required
def admin_course():
    courses = db.session.execute(text("SELECT * FROM Course")).mappings().all()
    return render_template("admin/course/list.html", courses=courses)

@app.route("/admin/course/add", methods=["POST", "GET"])
@login_required
def admin_course_add():
    if request.method == "POST":
        
        # Form getters
        course_name = request.form.get("name").title().strip()
        lvl_id = request.form.get("lvl_id").title().strip() 

        # Get existing course to avoid duplicate
        if is_exist(db, course_name, "name", "Course"):
            return apology(409, "The course name already exist.")

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


# Department (admin side)
@app.route("/admin/department")
@login_required
def admin_department():
    departments = db.session.execute(text("SELECT * FROM Department")).mappings().all()
    return render_template("admin/department/list.html", departments=departments)

@app.route("/admin/department/add", methods=["POST", "GET"])
@login_required
def admin_department_add():
    if request.method == "POST":
        name = request.form.get("name").title().strip()
        lvl_id = request.form.get("lvl_id").title().strip()

        # check if the name already exist
        if is_exist(db, name, "name", "Department"):
            return apology(409, "Department name already exist.")
        
        # Insert to the table
        tmp = add_department(db, name, lvl_id)

        return redirect(url_for("admin_department_add"))
        
    else:
        lvls = db.session.execute(text("SELECT * FROM EducationLevel")).mappings().all()
        return render_template("admin/department/add_form.html", lvls=lvls)


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
