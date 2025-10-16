CREATE DATABASE IF NOT EXISTS lms_db;
USE lms_db;

-- ====================
-- USERS
-- ====================

CREATE TABLE IF NOT EXISTS User (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'teacher', 'student') NOT NULL
);

-- ====================
-- ACADEMIC STRUCTURE
-- ====================

CREATE TABLE IF NOT EXISTS Course (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS Year (
    id INT AUTO_INCREMENT PRIMARY KEY,
    year_name VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS Section (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS Subjects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

-- ====================
-- PROFILES
-- ====================

CREATE TABLE IF NOT EXISTS StudentProfile (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    course_id INT,
    section_id INT,
    year_id INT,
    FOREIGN KEY (user_id) REFERENCES User(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES Course(id),
    FOREIGN KEY (section_id) REFERENCES Section(id),
    FOREIGN KEY (year_id) REFERENCES Year(id)
);

CREATE TABLE IF NOT EXISTS TeacherProfile (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    department VARCHAR(100),
    FOREIGN KEY (user_id) REFERENCES User(id) ON DELETE CASCADE
);


-- ====================
-- CLASSES & ENROLLMENT
-- ====================

CREATE TABLE IF NOT EXISTS Class (
    id INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id INT NOT NULL,
    subject_id INT NOT NULL,
    course_id INT NOT NULL,
    section_id INT NOT NULL,
    year_id INT NOT NULL,
    FOREIGN KEY (teacher_id) REFERENCES TeacherProfile(id),
    FOREIGN KEY (subject_id) REFERENCES Subjects(id),
    FOREIGN KEY (course_id) REFERENCES Course(id),
    FOREIGN KEY (section_id) REFERENCES Section(id),
    FOREIGN KEY (year_id) REFERENCES Year(id)
);

CREATE TABLE IF NOT EXISTS ClassStudent (
    id INT AUTO_INCREMENT PRIMARY KEY,
    class_id INT NOT NULL,
    student_id INT NOT NULL,
    FOREIGN KEY (class_id) REFERENCES Class(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES StudentProfile(id) ON DELETE CASCADE
);
