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

-- YearLevel table
CREATE TABLE IF NOT EXISTS YearLevel (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    education_level_id INT,
    FOREIGN KEY (education_level_id) REFERENCES EducationLevel(id)
        ON UPDATE CASCADE ON DELETE SET NULL
);


-- department table
CREATE TABLE IF NOT EXISTS Department (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    education_level_id INT NULL,
    FOREIGN KEY (education_level_id) REFERENCES EducationLevel(id)
);

-- Users table
CREATE TABLE IF NOT EXISTS Users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    middle_name VARCHAR(50),
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    school_id VARCHAR(50),
    status BOOLEAN NOT NULL DEFAULT TRUE,
    gender ENUM('Male','Female','Other'),
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    password VARCHAR(255) NOT NULL DEFAULT 'mcmY_1946',
    role ENUM('admin','teacher','student') NOT NULL
);


-- TeacherProfile table
CREATE TABLE IF NOT EXISTS TeacherProfile (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    department_id INT NULL,
    education_level_id INT,
    FOREIGN KEY (user_id) REFERENCES Users(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (education_level_id) REFERENCES EducationLevel(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (department_id) REFERENCES Department(id)
        ON UPDATE CASCADE ON DELETE SET NULL
);

-- Section table
CREATE TABLE IF NOT EXISTS Section (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    year_id INT,
    course_id INT,
    academic_year VARCHAR(20), 
    teacher_id INT NULL,
    status BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (year_id) REFERENCES YearLevel(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (course_id) REFERENCES Course(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (teacher_id) REFERENCES TeacherProfile(id)
    ON DELETE SET NULL ON UPDATE CASCADE
);

-- Subject table
CREATE TABLE IF NOT EXISTS Subject (
    id INT AUTO_INCREMENT PRIMARY KEY,
    status BOOLEAN NOT NULL DEFAULT TRUE,
    name VARCHAR(100) NOT NULL,
    education_level_id INT,
    FOREIGN KEY (education_level_id) REFERENCES EducationLevel(id)
        ON UPDATE CASCADE ON DELETE SET NULL
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
    FOREIGN KEY (year_id) REFERENCES YearLevel(id)
        ON UPDATE CASCADE ON DELETE SET NULL
);

-- Class table
CREATE TABLE IF NOT EXISTS Class (
    id INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id INT NOT NULL COMMENT 'Class teacher, not section adviser',
    subject_id INT NOT NULL COMMENT 'Subject being taught',
    section_id INT NOT NULL COMMENT 'Section of students',
    status ENUM('active','cancelled','completed') DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES TeacherProfile(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES Subject(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (section_id) REFERENCES Section(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    UNIQUE KEY unique_class(subject_id, teacher_id, section_id)
);

-- ClassStudent table
CREATE TABLE IF NOT EXISTS ClassStudent (
    id INT AUTO_INCREMENT PRIMARY KEY,
    class_id INT NOT NULL,
    student_id INT NOT NULL,
    status ENUM('active','dropped','completed') DEFAULT 'active',
    enrolled_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (class_id) REFERENCES Class(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES StudentProfile(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    UNIQUE KEY unique_enrollment(class_id, student_id) 
);

-- Lesson table
CREATE TABLE IF NOT EXISTS Lesson (
    id INT AUTO_INCREMENT PRIMARY KEY,              
    class_id INT NOT NULL COMMENT 'Class this lesson belongs to',                          
    lesson_number INT NOT NULL COMMENT 'Order of lesson in the class',                     
    title VARCHAR(255) NOT NULL COMMENT 'Lesson title',                    
    description TEXT COMMENT 'Optional lesson details',                               
    file_attachment VARCHAR(255) COMMENT 'File path or URL',                   
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,  
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (class_id) REFERENCES Class(id)    
        ON UPDATE CASCADE ON DELETE CASCADE
);

-- INSERT Education Levels
INSERT INTO EducationLevel (name) VALUES
('Elementary'),
('Junior High'),
('Senior High'),
('College');

-- INSERT Courses
INSERT INTO Course (name, education_level_id) VALUES
('Bachelor Of Science In Computer Science', 4),
('Bachelor Of Science In Hotel Management', 4),
('Senior High School - STEM', 3),
('Senior High School - ABM', 3);

-- INSERT Year Levels
INSERT INTO YearLevel (name, education_level_id) VALUES
-- Elementary
('Grade 1', 1),
('Grade 2', 1),
('Grade 3', 1),
('Grade 4', 1),
('Grade 5', 1),
('Grade 6', 1),
-- Junior High
('Grade 7', 2),
('Grade 8', 2),
('Grade 9', 2),
('Grade 10', 2),
-- Senior High
('Grade 11', 3),
('Grade 12', 3),
-- College
('1st Year', 4),
('2nd Year', 4),
('3rd Year', 4),
('4th Year', 4);

-- INSERT Departments
INSERT INTO Department (name, education_level_id) VALUES
('Elementary Department', 1),
('Junior High Department', 2),
('Senior High Department', 3),
('Computer Science', 4),
('Hotel Management', 4);

-- INSERT Users
INSERT INTO Users (first_name, middle_name, last_name, email, school_id, gender, password, role, is_verified, status) VALUES
('Admin', 'A', 'User', 'administrator@HOLYCROSS.EDU.PH', 'LMS001', 'Other', 'adminpassword', 'admin', 1, 1),
('Joseph', 'C', 'Canzana', '14462018@holycross.edu.ph', '14462018', 'Male', 'mcmY_1946', 'student', 1, 1),
('David', 'H', 'Malan', '42852005@holycross.edu.ph', '42852005', 'Male', 'mcmY_1946', 'teacher', 1, 1);

-- INSERT TeacherProfile
INSERT INTO TeacherProfile (user_id, department_id, education_level_id) VALUES
(3, 4, 4); -- David Malan

-- INSERT Sections
INSERT INTO Section (name, year_id, course_id, academic_year, status, teacher_id) VALUES
-- Elementary
('Elem 1-A', 1, NULL, '2025-2026', 1, NULL),
('Elem 2-A', 2, NULL, '2025-2026', 1, NULL),
-- Junior High
('JH 7-A', 7, NULL, '2025-2026', 1, NULL),
('JH 8-A', 8, NULL, '2025-2026', 1, NULL),
-- Senior High
('STEM 11-A', 11, 3, '2025-2026', 1, NULL),
('ABM 12-B', 12, 4, '2025-2026', 1, NULL),
-- College
('CS1-A', 13, 1, '2025-2026', 1, 1), -- assign David Malan as teacher
('CS2-B', 14, 1, '2025-2026', 1, 1),
('HM1-A', 13, 2, '2025-2026', 1, NULL);

-- INSERT Subjects
INSERT INTO Subject (name, education_level_id) VALUES
-- Elementary
('English', 1),
('Mathematics', 1),
('Science', 1),
('Filipino', 1),
('Araling Panlipunan', 1),
-- Junior High
('English', 2),
('Mathematics', 2),
('Science', 2),
('Filipino', 2),
('Social Studies', 2),
-- Senior High
('Physics', 3),
('Biology', 3),
('Accounting', 3),
('Business Math', 3),
-- College
('Programming 1', 4),
('Programming 2', 4),
('Data Structures', 4),
('Algorithms', 4),
('Database Systems', 4);

-- INSERT StudentProfile
INSERT INTO StudentProfile (user_id, education_level_id, course_id, section_id, year_id) VALUES
(2, 4, 1, 7, 13); -- Joseph Canzana in CS1-A

-- INSERT Classes
INSERT INTO Class (teacher_id, subject_id, section_id, status) VALUES
(1, 16, 7, 'active'), -- Programming 1 class for CS1-A
(1, 17, 7, 'active'); -- Programming 2 class for CS1-A

-- INSERT ClassStudent
INSERT INTO ClassStudent (class_id, student_id, status) VALUES
(1, 1, 'active'),
(2, 1, 'active');
