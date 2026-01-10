# decorators.py
from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user, login_required

def role_required(role):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.role != role:
                flash("Unauthorized access!")
                return redirect(url_for("index"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
