from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import text


def encrypt_password(password):
    # TODO: UNCOMMENT BEFORE FINALIZATION
    # return generate_password_hash(password, method='scrypt', salt_length=16)
    return password

def check_password(p_1, p_2):
    # TODO: UNCOMMENT BEFORE FINALIZATION
    # return check_password_hash(p_1, p_2)
    return p_1 == p_2

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

    return db.session.execute(text("SELECT id FROM Users WHERE school_id = :school_id"), {"school_id" : school_id}).mappings().first()

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
    return db.session.execute(text("SELECT * FROM StudentProfile WHERE user_id = :user_id"), {"user_id" : user_id}).mappings().first()
    