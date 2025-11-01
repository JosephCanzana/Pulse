# utilities
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_login import LoginManager, login_user, login_required, logout_user
from sqlalchemy import text

# Own created helpers/mini-framework
from helpers import *
from database import db
from models import load_user

# Blueprints
from admin_routes import admin_bp


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
DEFAULT_PASSWORD = "mcmY_1946"

# TEST
@app.route("/testdb")
def testdb():
    tables = db.session.execute(text("SHOW TABLES")).fetchall()
    return {"tables": [t[0] for t in tables]}


# ==== ADMIN BLUEPRINT =====
app.register_blueprint(admin_bp)

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
            return redirect(url_for("admin.admin"))
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
            flash("Default password is not vaid", "error")
            return redirect(url_for("account_activation",  school_id=school_id))
        
        if new_pwd != c_pwd:
            flash("Your password don't match", "error")
            return redirect(url_for("account_activation",  school_id=school_id))
        
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
