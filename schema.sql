DROP DATABASE IF EXISTS lms_db;

-- Create database
CREATE DATABASE IF NOT EXISTS lms_db;
USE lms_db;

-- EducationLevel table
CREATE TABLE IF NOT EXISTS EducationLevel (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name ENUM('Elementary', 'Junior High', 'Senior High', 'College') NOT NULL
) ENGINE=InnoDB;

-- Course table
CREATE TABLE IF NOT EXISTS Course (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    education_level_id INT,
    FOREIGN KEY (education_level_id) REFERENCES EducationLevel(id)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;

-- AcademicYear table
CREATE TABLE IF NOT EXISTS AcademicYear (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    education_level_id INT,
    FOREIGN KEY (education_level_id) REFERENCES EducationLevel(id)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;

-- Section table
CREATE TABLE IF NOT EXISTS Section (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    education_level_id INT,
    FOREIGN KEY (education_level_id) REFERENCES EducationLevel(id)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;

-- Subject table
CREATE TABLE IF NOT EXISTS Subject (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    education_level_id INT,
    FOREIGN KEY (education_level_id) REFERENCES EducationLevel(id)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;

-- Users table
CREATE TABLE IF NOT EXISTS Users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    middle_name VARCHAR(50),
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    school_id VARCHAR(50),
    gender ENUM('Male','Female','Other'),
    password VARCHAR(255) NOT NULL DEFAULT 'mcmY_1946',
    role ENUM('admin','teacher','student') NOT NULL
) ENGINE=InnoDB;

-- StudentProfile table
CREATE TABLE IF NOT EXISTS StudentProfile (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    education_level_id INT,
    course_id INT,
    section_id INT,
    year_id INT,
    FOREIGN KEY (user_id) REFERENCES Users(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (education_level_id) REFERENCES EducationLevel(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (course_id) REFERENCES Course(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (section_id) REFERENCES Section(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (year_id) REFERENCES AcademicYear(id)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;

-- TeacherProfile table
CREATE TABLE IF NOT EXISTS TeacherProfile (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    department VARCHAR(100),
    FOREIGN KEY (user_id) REFERENCES Users(id)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB;

-- Class table
CREATE TABLE IF NOT EXISTS Class (
    id INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id INT,
    subject_id INT,
    course_id INT,
    section_id INT,
    year_id INT,
    FOREIGN KEY (teacher_id) REFERENCES Users(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (subject_id) REFERENCES Subject(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (course_id) REFERENCES Course(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (section_id) REFERENCES Section(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (year_id) REFERENCES AcademicYear(id)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;

-- ClassStudent table
CREATE TABLE IF NOT EXISTS ClassStudent (
    id INT AUTO_INCREMENT PRIMARY KEY,
    class_id INT NOT NULL,
    student_id INT NOT NULL,
    FOREIGN KEY (class_id) REFERENCES Class(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES Users(id)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB;

-- Insert default admin user
INSERT INTO Users 
    (first_name, middle_name, last_name, email, school_id, gender, password, role) 
VALUES 
    ('Admin', 'A', 'User', 'administrator@holycross.edu.ph', 'LMS001', 'Other', 'adminpassword', 'admin');
