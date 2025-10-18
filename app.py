from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from helpers import encrypt_password, check_password, add_user, assign_student_profile

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
    
    students = db.session.execute(query).mappings().all()
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
        education_lvls = db.session.execute(text("SELECT * FROM EducationLevel"))
        courses = db.session.execute(text("SELECT * FROM Course"))
        sections = db.session.execute(text("SELECT * FROM Section"))
        years = db.session.execute(text("SELECT * FROM AcademicYear"))

        return render_template("admin/student/add_form.html", education_lvls=education_lvls, courses=courses, sections=sections, years=years)

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
