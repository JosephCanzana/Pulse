from flask import render_template
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import text


def apology(num=400, message="Error occur"):
    return render_template("apology.html", message=message, error_code=num)


def encrypt_password(password):
    # TODO: UNCOMMENT BEFORE FINALIZATION
    # return generate_password_hash(password, method='scrypt', salt_length=16)
    return password

def check_password(p_1, p_2):
    # TODO: UNCOMMENT BEFORE FINALIZATION
    # return check_password_hash(p_1, p_2)
    return p_1 == p_2


def is_exist(db, find_value, table_value, table):
    query = text(f"SELECT 1 FROM {table} WHERE {table_value} = :value LIMIT 1")
    duplicate = db.session.execute(query, {"value": find_value}).fetchone() 
    if duplicate:
        return True
    return False


def add_user(db,f_name, s_name, l_name, 
            email, school_id,
            gender, role):

    db.session.execute(
    text("""
        INSERT INTO Users (first_name, middle_name, last_name, email, school_id, gender, role)
        VALUES (:f, :s, :l, :email, :school_id, :gender, :role)
    """),
    {
        "f": f_name,
        "s": s_name,
        "l": l_name,
        "email": email,
        "school_id": school_id,
        "gender": gender,
        "role": role
    })
    db.session.commit()

    return db.session.execute(text("SELECT id FROM Users WHERE school_id = :school_id LIMIT 1"), {"school_id" : school_id}).mappings().first()

def assign_student_profile(db, user_id, ed_lvl, course_id, section_id, year_id):
    db.session.execute(text
        ("""
        INSERT INTO StudentProfile (user_id, education_level_id, course_id, year_id, section_id)
        VALUES (:user_id, :ed_lvl, :course_id, :year_id, :section_id)
        """),
        {
            "user_id" : user_id,
            "ed_lvl" : ed_lvl,
            "course_id" : course_id,
            "section_id" : section_id,
            "year_id" : year_id
        }
    )
    db.session.commit()
    return db.session.execute(text("SELECT * FROM StudentProfile WHERE user_id = :user_id LIMIT 1"), {"user_id" : user_id}).mappings().first()
    

def assign_teacher_profile(db, user_id, department_id, lvl_id):
    db.session.execute(text(
        """
        INSERT INTO TeacherProfile (user_id, department_id, education_level_id)
        VALUES (:user_id, :department_id, :lvl_id) 
        """),
        {
            "user_id" : user_id,
            "department_id" : department_id,
            "lvl_id" : lvl_id,
        }
    )

    db.session.commit()
    return db.session.execute(text("SELECT 8 FROM StudentProfile WHERE user_id = :user_id"), {"user_id": user_id}).mappings().first()

def add_course(db, name, lvl_id):
    db.session.execute(text("""INSERT INTO Course (name, education_level_id) 
                            VALUES (:name, :lvl_id)
                            """), 
                            {"name": name, 
                            "lvl_id": lvl_id
                            })
    db.session.commit()
    return db.session.execute(text("SELECT id FROM Course WHERE education_level_id = :id"), {"id": lvl_id}).mappings().first()

def add_department(db, name, lvl_id):
    db.session.execute(text("""INSERT INTO Department (name, education_level_id) 
                            VALUES (:name, :lvl_id)"""),
                            {"name": name,
                            "lvl_id": lvl_id})
    
    db.session.commit()
    return db.session.execute(text("SELECT id FROM Department WHERE name = :name"), {"name": name}).mappings().first()