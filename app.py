from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL

# ==== APP SETUP ====
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
# To be replaced with random cookies
app.secret_key = "tmpsecretkey"

# ==== DATABASE CONFIG ====
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''  # replace this with password if you have one
app.config['MYSQL_DB'] = 'lms_db'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# TEST
@app.route("/testdb")
def testdb():
    cur = mysql.connection.cursor()
    cur.execute("SHOW TABLES;")
    tables = cur.fetchall()
    cur.close()

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

        # connect to db
        cur = mysql.connection.cursor()

        # confirm email exist
        cur.execute("SELECT * FROM User WHERE email = %s", (email,))
        user = cur.fetchone()
        if user is None:
            return render_template("apology.html", message=user)
        
        # is the password same as the id.password
        if password != user["password"]:
            return render_template("apology.html", message=user)
        
        # assign it to the current session
        session["user_id"] = user["id"]
        session["first_name"] = user["first_name"]
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
