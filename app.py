# utilities
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from sqlalchemy import text
from datetime import date, datetime
import re

# Own created helpers/mini-framework
from helpers import *
from database import db
from models import load_user

# Blueprints
from admin_routes import admin_bp
from teacher_routes import teacher_bp
from student_routes import student_bp

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.secret_key = "tmpsecretkey"

# ==== DATABASE CONFIG ====
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/lms_db'
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 280,
    'pool_pre_ping': True
}

# ==== Initialize extensions ====
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Connect Flask-Login to our user loader
login_manager.user_loader(load_user)

# GLOBAL VARIABLES
DEFAULT_PASSWORD = generate_password_hash("mcmY_1946")
# Password regex
HARD_PASS_RE = "^(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$"
MID_PASS_RE = "^(?=.*[A-Z])(?=.*\d).{8,}$"


@app.template_filter('datetimeformat')
def datetimeformat(value, format='%I:%M %p'):
    """
    Formats a datetime string or object into a given format.
    Default: 'h:mm AM/PM' (12-hour)
    """
    if not value:
        return ''
    
    # Convert string to datetime if needed
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return value  # return as-is if not parseable

    return value.strftime(format)

# AJAX
@app.route("/api/student-hierarchy")
def student_hierarchy():
    query_type = request.args.get("type")
    level_id = request.args.get("education_level_id")
    course_id = request.args.get("course_id")
    year_id = request.args.get("year_id")

    if query_type == "courses" and level_id:
        result = db.session.execute(
            text("SELECT id, name FROM Course WHERE education_level_id = :level_id AND status = 1"),
            {"level_id": level_id}
        ).mappings().all()
        return jsonify([dict(r) for r in result])

    if query_type == "year_levels" and level_id:
        result = db.session.execute(
            text("SELECT id, name FROM YearLevel WHERE education_level_id = :level_id"),
            {"level_id": level_id}
        ).mappings().all()
        return jsonify([dict(r) for r in result])

    if query_type == "sections" and course_id and year_id:
        result = db.session.execute(
            text("SELECT id, name, academic_year FROM Section WHERE course_id = :course_id AND year_id = :year_id AND status = 1"),
            {"course_id": course_id, "year_id": year_id}
        ).mappings().all()
        return jsonify([dict(r) for r in result])

    return jsonify([])

@app.route("/api/teacher-hierarchy")
def teacher_hierarchy():
    """
    AJAX endpoint for populating teacher-related dropdowns.
    Example: Education Level -> Departments
    """
    query_type = request.args.get("type")
    level_id = request.args.get("education_level_id")

    if query_type == "departments" and level_id:
        result = db.session.execute(
            text("SELECT id, name FROM Department WHERE education_level_id = :level_id AND status = 1"),
            {"level_id": level_id}
        ).mappings().all()
        return jsonify([dict(r) for r in result])

    return jsonify([])

@app.route("/api/class-hierarchy")
def class_hierarchy():
    """
    AJAX endpoint for Class form:
    - teacher -> subjects
    - teacher -> education level -> sections
    (Any section under the same education level as the teacher)
    """
    query_type = request.args.get("type")
    teacher_id = request.args.get("teacher_id")

    if not teacher_id:
        return jsonify([])

    # Get teacher's education level
    teacher_info = db.session.execute(
        text("SELECT education_level_id FROM TeacherProfile WHERE id = :teacher_id"),
        {"teacher_id": teacher_id}
    ).mappings().first()

    if not teacher_info:
        return jsonify([])

    education_level_id = teacher_info["education_level_id"]

    if query_type == "subjects":
        # Subjects the teacher can teach
        result = db.session.execute(
            text("""
                SELECT s.id, s.name
                FROM Subject s
                WHERE s.education_level_id = :education_level_id
                  AND s.status = 1
            """),
            {"education_level_id": education_level_id}
        ).mappings().all()
        return jsonify([dict(r) for r in result])

    if query_type == "sections":
        # Sections under the teacher's education level
        result = db.session.execute(
            text("""
                SELECT sec.id, sec.name, sec.academic_year
                FROM Section sec
                LEFT JOIN Course co ON sec.course_id = co.id
                LEFT JOIN YearLevel yl ON sec.year_id = yl.id
                LEFT JOIN EducationLevel el_course ON co.education_level_id = el_course.id
                LEFT JOIN EducationLevel el_year ON yl.education_level_id = el_year.id
                WHERE (COALESCE(el_course.id, el_year.id) = :education_level_id)
                  AND sec.status = 1
            """),
            {"education_level_id": education_level_id}
        ).mappings().all()
        return jsonify([dict(r) for r in result])

    return jsonify([])


# Daily Random Quotes
last_checked_date = None

@app.before_request
def ensure_daily_inspiration():
    global last_checked_date
    today = date.today()

    if last_checked_date != today:
        last_checked_date = today

        daily = db.session.execute(
            text("SELECT * FROM daily_inspirations WHERE date = :today"),
            {"today": today}
        ).mappings().first()

        if not daily:
            quote_id = db.session.execute(text("SELECT id FROM motivational_quotes ORDER BY RAND() LIMIT 1")).scalar()
            verse_id = db.session.execute(text("SELECT id FROM bible_verses ORDER BY RAND() LIMIT 1")).scalar()
            message_id = db.session.execute(text("SELECT id FROM grateful_peace_messages ORDER BY RAND() LIMIT 1")).scalar()

            db.session.execute(text("""
                INSERT INTO daily_inspirations (quote_id, verse_id, message_id, date)
                VALUES (:q, :v, :m, :d)
            """), {"q": quote_id, "v": verse_id, "m": message_id, "d": today})
            db.session.commit()


UPLOAD_FOLDER = "uploads/lessons"

@app.route('/uploads/<filename>')
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

# ==== BLUEPRINT =====
app.register_blueprint(admin_bp)
app.register_blueprint(teacher_bp)
app.register_blueprint(student_bp)

# ==== GENERAL PAGES ====
# LANDING PAGE
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user_id = current_user.id
    role = session.get("role")

    # Fetch current user info
    user_query = text("SELECT * FROM Users WHERE id = :id")
    user = db.session.execute(user_query, {"id": user_id}).mappings().first()

    # Fetch extra profile info based on role
    extra_profile = None
    if role == "student":
        extra_query = text("""
            SELECT sp.*, c.name AS course_name, s.name AS section_name, el.name AS education_level_name
            FROM StudentProfile sp
            LEFT JOIN Course c ON sp.course_id = c.id
            LEFT JOIN Section s ON sp.section_id = s.id
            LEFT JOIN EducationLevel el ON sp.education_level_id = el.id
            WHERE sp.user_id = :id
        """)
        extra_profile = db.session.execute(extra_query, {"id": user_id}).mappings().first()
    elif role == "teacher":
        extra_query = text("""
            SELECT tp.*, d.name AS department_name, el.name AS education_level_name
            FROM TeacherProfile tp
            LEFT JOIN Department d ON tp.department_id = d.id
            LEFT JOIN EducationLevel el ON tp.education_level_id = el.id
            WHERE tp.user_id = :id
        """)
        extra_profile = db.session.execute(extra_query, {"id": user_id}).mappings().first()

    # Handle admin updating their own profile
    if request.method == "POST" and role == "admin":
        first_name = request.form.get("first_name")
        middle_name = request.form.get("middle_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        
        # Password change fields
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if not re.match(HARD_PASS_RE, new_password):
            flash("Password must be at least 8 characters long and include an uppercase letter, number, and special character.", "error")
            return redirect("/profile")
        elif not re.match(MID_PASS_RE, new_password):
            flash("Add atleast one character", "error")
            return redirect("/profile")
        
        # Verify current password before updating
        if current_password or new_password or confirm_password:
            if not current_password or not new_password or not confirm_password:
                flash("All password fields are required to change password.", "error")
                return redirect(url_for("profile"))

            # Check current password
            if not check_password(current_password, user["password"]):
                flash("Current password is incorrect.", "error")
                return redirect(url_for("profile"))
            
            # Check new password confirmation
            if new_password != confirm_password:
                flash("New passwords do not match.", "error")
                return redirect(url_for("profile"))

            # Hash new password
            password = encrypt_password(new_password)
        else:
            password = None  # no change

        # Update user info
        update_query = text("""
            UPDATE Users SET
                first_name = :first_name,
                middle_name = :middle_name,
                last_name = :last_name,
                email = :email
                {password_clause}
            WHERE id = :id
        """.format(password_clause=", password = :password" if password else ""))

        params = {
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
            "email": email,
            "id": user_id
        }
        if password:
            params["password"] = password

        db.session.execute(update_query, params)
        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("profile"))

    return render_template("profile.html", user=user, extra_profile=extra_profile, role=role)


# LOGIN
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

        if user["status"] != 1:
            flash("Your account is archived, contact admin to resolve this issue", "warning")
            return redirect(url_for("login"))

        # Create Flask-Login user object
        user_obj = load_user(user["id"])

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
            return redirect(url_for("admin.dashboard"))
        elif role == "teacher":
            return redirect(url_for("teacher.dashboard"))
        else:
            # Execute the query
            result = db.session.execute(
                text("SELECT is_suspended FROM StudentProfile WHERE user_id = :user_id"),
                {"user_id": user["id"]}
            ).fetchone()  
            if result[0]: 
                flash("You are currently suspended.", "warning")
                logout_user()
                return redirect(url_for("index"))
            return redirect(url_for("student.dashboard"))

    return render_template("auth/login.html")

# ACCOUNT ACTIVATION ROUTE!
@app.route("/login/account_activation/<string:school_id>", methods=["GET", "POST"])
@login_required
def account_activation(school_id):
    if request.method == "POST":
        f_name = request.form.get("first_name").capitalize().strip() 
        l_name = request.form.get("last_name").capitalize().strip()
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
            flash("Default password is not valid", "error")
            return redirect(url_for("account_activation",  school_id=school_id))
        
        if new_pwd != c_pwd:
            flash("Your password don't match", "error")
            return redirect(url_for("account_activation",  school_id=school_id))
        
        if not re.match(HARD_PASS_RE, new_pwd):
            flash("Password must be at least 8 characters long and include an uppercase letter, number, and special character.", "error")
            return redirect("account_activation")
        elif not re.match(MID_PASS_RE, new_pwd):
            flash("Add atleast one character", "error")
            return redirect("/profile")
        

        hashed_pwd = encrypt_password(new_pwd)

        # Update password and set account as verified
        db.session.execute(
            text("UPDATE Users SET password = :password, is_verified = 1 WHERE school_id = :school_id"),
            {"password": hashed_pwd, "school_id": school_id}
        )
        db.session.commit() 

        user_obj = load_user(user["id"])

        # Normal login
        login_user(user_obj)
        session.update({
            "first_name": user["first_name"],
            "middle_name": user["middle_name"],
            "last_name": user["last_name"],
            "role": user["role"]
        })

        if session["role"] == "admin":
            return redirect(url_for("admin.dashboard")) 
        elif session["role"] == "teacher":
            return redirect(url_for("teacher.dashboard")) 
        else:
            return redirect(url_for("student.dashboard"))

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


if __name__ == "__main__": 
    app.run(debug=True)
