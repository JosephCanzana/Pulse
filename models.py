from flask_login import UserMixin
from sqlalchemy import text
from database import db

# ==== User Model ====

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


# ==== Flask-Login user loader ====
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
