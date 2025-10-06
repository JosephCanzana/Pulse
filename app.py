from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
# To be replaced with random cookies
app.secret_key = "tmpsecretkey"

@app.route("/")
def index():
    return render_template("index.html")

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

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", name="test")

@app.route("/logout", methods=["POST"])
def logout():
    session["user_id"] = None
    return redirect(url_for("index"))

if __name__ == "__main__": 
    app.run(debug=True)
