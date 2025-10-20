DROP DATABASE IF EXISTS lms_db;

-- Create database
CREATE DATABASE IF NOT EXISTS lms_db;
USE lms_db;

-- EducationLevel table
CREATE TABLE IF NOT EXISTS EducationLevel (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name ENUM('Elementary', 'Junior High', 'Senior High', 'College') NOT NULL
);

-- Course table
CREATE TABLE IF NOT EXISTS Course (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    education_level_id INT,
    FOREIGN KEY (education_level_id) REFERENCES EducationLevel(id)
        ON UPDATE CASCADE ON DELETE SET NULL
);

-- AcademicYear table
CREATE TABLE IF NOT EXISTS AcademicYear (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    education_level_id INT,
    FOREIGN KEY (education_level_id) REFERENCES EducationLevel(id)
        ON UPDATE CASCADE ON DELETE SET NULL
);

-- Section table
CREATE TABLE IF NOT EXISTS Section (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    education_level_id INT,
    course_id INT,
    FOREIGN KEY (education_level_id) REFERENCES EducationLevel(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (course_id) REFERENCES Course(id)
        ON UPDATE CASCADE ON DELETE SET NULL
);

-- department table
CREATE TABLE IF NOT EXISTS Department (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    education_level_id INT NULL,
    FOREIGN KEY (education_level_id) REFERENCES EducationLevel(id)
);

-- Subject table
CREATE TABLE IF NOT EXISTS Subject (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    education_level_id INT,
    FOREIGN KEY (education_level_id) REFERENCES EducationLevel(id)
        ON UPDATE CASCADE ON DELETE SET NULL
);

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
);

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
);

-- TeacherProfile table
CREATE TABLE IF NOT EXISTS TeacherProfile (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    department_id INT,
    education_level_id INT,
    FOREIGN KEY (user_id) REFERENCES Users(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (education_level_id) REFERENCES EducationLevel(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (department_id) REFERENCES Department(id)
        ON UPDATE CASCADE ON DELETE SET NULL
);

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
);

-- ClassStudent table
CREATE TABLE IF NOT EXISTS ClassStudent (
    id INT AUTO_INCREMENT PRIMARY KEY,
    class_id INT NOT NULL,
    student_id INT NOT NULL,
    FOREIGN KEY (class_id) REFERENCES Class(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES Users(id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

-- Insert default admin user
INSERT INTO Users 
    (first_name, middle_name, last_name, email, school_id, gender, password, role) 
VALUES 
    ('Admin', 'A', 'User', 'administrator@holycross.edu.ph', 'LMS001', 'Other', 'adminpassword', 'admin');

-- Education level, Year, Course

INSERT INTO EducationLevel (Name) VALUES
('Elementary'),
('Junior High'),
('Senior High'),
('College');

INSERT INTO Course (Name, education_level_id) VALUES
('None', 1), 
('None', 2),
('STEM', 3),
('ABM', 3),
('Bachelor of Science in Computer Science', 4),
('Associate in Computer Technology', 4),
('Bachelor of Science in Hotel Management', 4);

INSERT INTO Section (Name, education_level_id, course_id) VALUES
('rose', 1, 1),
('tree', 1, 1),
('cecilia', 2, 1),
('eagle', 2, 1),
('A', 3, 1),
('B', 3, 2),
('A', 4, 1),
('B', 4, 3),
('B', 4, 4);

INSERT INTO AcademicYear (name, education_level_id) VALUES
('Grade 1', 1),
('Grade 2', 1),
('Grade 7', 2),
('Grade 8', 2),
('Grade 11', 3),
('Grade 12', 3),
('1st Year', 4),
('2nd Year', 4);


INSERT INTO Subject (Name, education_level_id) VALUES
('Math', 1),
('English', 1),
('Science', 1),
('Math', 2),
('English', 2),
('Biology', 2),
('Math', 3),
('English', 3),
('Physics', 3),
('Programming', 4),
('Data Structures', 4);



-- Departments for Elementary and Junior High (basic subjects grouped)
INSERT INTO Department (name, education_level_id) VALUES
('General Education Department', 1),
('General Education Department', 2);

-- Departments for Senior High
INSERT INTO Department (name, education_level_id) VALUES
('STEM Department', 3),
('ABM Department', 3),
('Humanities and Social Sciences Department', 3),
('Technical-Vocational Department', 3);

-- Departments for College
INSERT INTO Department (name, education_level_id) VALUES
('Computer Science Department', 4),
('Information Technology Department', 4),
('Hotel Management Department', 4),
('Business Administration Department', 4),
('General Education Department', 4);

