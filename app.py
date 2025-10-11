from flask import Flask, render_template, request, redirect, url_for, session


# ==== SETUP ====
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
# To be replaced with random cookies
app.secret_key = "tmpsecretkey"


# ==== STARTING PAGES ====

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

        # confirm email exist and get id
        # is the password same as the id.password
        
        # temporary id -> to be updated when db is confirmed
        tmp = "tmp-id"
        session["user_id"] = tmp
        return redirect(url_for("dashboard"))
    else:
        return render_template("login.html")
# REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        first_name = request.form.get("first-name")
        last_name = request.form.get("last-name")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm-password")

        # Email same as the school email
        # Password and confirm password same 
        # Password requirements
        # Append to the Database

        return redirect(url_for("login"))
    else:
        return render_template("register.html")


# ==== NAVIGATION BAR PAGES =====

# DASHBOARD
@app.route("/dashboard")
def dashboard():
    return render_template("navbar/dashboard.html", name="test")
# LEADERBOARD
@app.route("/leaderboard")
def leaderboard():
    return render_template("navbar/leaderboard.html")
# TIMELINE
@app.route("/timeline")
def timeline():
    return render_template("navbar/timeline.html")


# ==== SIDE BAR PAGES =====

# COURSE
@app.route("/course")
def course():
    return render_template("sidebar/course.html")
# ABOUT
@app.route("/about")
def about():
    return render_template("sidebar/about.html")
# ACHIEVEMENTS
@app.route("/achievements")
def achievements():
    return render_template("sidebar/achievements.html")
# PROJECTS
@app.route("/projects")
def projects():
    return render_template("sidebar/projects.html")



# LOGOUT
@app.route("/logout", methods=["POST"])
def logout():
    session["user_id"] = None
    return redirect(url_for("index"))

if __name__ == "__main__": 
    app.run(debug=True)
