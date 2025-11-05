from flask import render_template, session, Blueprint, flash, request,url_for, redirect
from flask_login import login_required, current_user
from sqlalchemy import text
from helpers import *
from database import db
import os
from werkzeug.utils import secure_filename

student_bp = Blueprint('student', __name__, url_prefix='/student')


@student_bp.route("/")
@login_required
def dashboard():
    return render_template("student/dashboard.html", name=session["first_name"])
