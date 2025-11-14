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
    status BOOLEAN NOT NULL DEFAULT TRUE,
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
    status BOOLEAN NOT NULL DEFAULT TRUE,
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
    password VARCHAR(255) NOT NULL DEFAULT 'scrypt:32768:8:1$zQ90TifUV57h28Bl$f4b4c07b635d072c608d5191a3cabf224f5aaae76c8ef657712ee5263305a4e550a857aeb682d3ba6f619c8793c1cd16edfad820900bf93a532d59259d5b8664',
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
    education_lvl_id INT,
    name VARCHAR(50) NOT NULL,
    year_id INT,
    course_id INT,
    academic_year VARCHAR(20),
    teacher_id INT NULL,
    status BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (education_lvl_id) REFERENCES EducationLevel(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
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
    is_suspended BOOLEAN NOT NULL DEFAULT FALSE,
    points INT NOT NULL DEFAULT 0,
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
    color VARCHAR(20) DEFAULT NULL COMMENT 'Theme color for the class',
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
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (class_id) REFERENCES Class(id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS LessonFile (
    id INT AUTO_INCREMENT PRIMARY KEY,
    lesson_id INT NOT NULL COMMENT 'Linked lesson ID',
    file_name VARCHAR(255) NOT NULL COMMENT 'Original file name',
    file_path VARCHAR(255) NOT NULL COMMENT 'Server path or URL',
    file_type VARCHAR(100) COMMENT 'MIME type, e.g. application/pdf',
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lesson_id) REFERENCES Lesson(id)
        ON UPDATE CASCADE ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS StudentLessonProgress (
    id INT AUTO_INCREMENT PRIMARY KEY,
    class_id INT NOT NULL,
    lesson_id INT NOT NULL,
    student_id INT NOT NULL,
    status ENUM('not_started', 'in_progress', 'completed') DEFAULT 'not_started',
    started_at DATETIME NULL,
    completed_at DATETIME NULL,
    FOREIGN KEY (class_id) REFERENCES Class(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (lesson_id) REFERENCES Lesson(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES StudentProfile(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    UNIQUE KEY unique_progress(class_id, lesson_id, student_id)
);

CREATE TABLE IF NOT EXISTS IdCounter (
    year INT PRIMARY KEY,
    counter INT NOT NULL
);

CREATE TABLE IF NOT EXISTS TrophyLevel (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    required_points INT NOT NULL
);

CREATE TABLE IF NOT EXISTS Activity (
    id INT AUTO_INCREMENT PRIMARY KEY,
    class_id INT NOT NULL,
    lesson_id INT NULL,
    title VARCHAR(255) NOT NULL,
    instructions TEXT,
    type ENUM('assignment','quiz','task') DEFAULT 'assignment',
    due_date DATETIME NULL,
    max_score INT DEFAULT 100,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (class_id) REFERENCES Class(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (lesson_id) REFERENCES Lesson(id) ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS ActivityFile (
    id INT AUTO_INCREMENT PRIMARY KEY,
    activity_id INT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (activity_id) REFERENCES Activity(id) ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ActivitySubmission (
    id INT AUTO_INCREMENT PRIMARY KEY,
    activity_id INT NOT NULL,
    student_id INT NOT NULL,
    file_path VARCHAR(255) NULL,
    file_name VARCHAR(255) NULL,
    text_answer TEXT NULL,
    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    score INT NULL,
    feedback TEXT NULL,
    graded_at DATETIME NULL,
    FOREIGN KEY (activity_id) REFERENCES Activity(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES StudentProfile(id) ON UPDATE CASCADE ON DELETE CASCADE,
    UNIQUE KEY unique_submission(activity_id, student_id)
);

INSERT INTO TrophyLevel (name, required_points) VALUES
('Novice Explorer', 1),
('Apprentice Learner', 2),
('Curious Mind', 3),
('Knowledge Seeker', 5),
('Rising Scholar', 8),
('Bright Student', 13),
('Star Pupil', 21),
('Ace Learner', 34),
('Mastermind', 55),
('Legendary Scholar', 89);



INSERT INTO Users (first_name, middle_name, last_name, email, school_id, gender, password, role, is_verified, status) VALUES
('Admin', 'A', 'User', 'administrator@holycross.edu.ph', 'LMS001', 'Other', 'scrypt:32768:8:1$QwMDSjGCa4LlIVnC$7bc8add45125f055440e7ae652b28304382837f083e9a455f0ed29d32e3503b638702e7d0d6f8a8d91a7ac030d6ff5c913e61129515d277f8980a34adfde551e',
 'admin', 1, 1); 

INSERT INTO IdCounter (year, counter) VALUES (2025, 1000);

-- ==========================================================
-- EDUCATION LEVELS
-- ==========================================================
INSERT INTO EducationLevel (name) VALUES
('Elementary'),
('Junior High'),
('Senior High'),
('College');

INSERT INTO YearLevel (name, education_level_id) VALUES
('Grade 1', 1),
('Grade 2', 1),
('Grade 3', 1),
('Grade 4', 1),
('Grade 5', 1),
('Grade 6', 1);
INSERT INTO YearLevel (name, education_level_id) VALUES
('Grade 7', 2),
('Grade 8', 2),
('Grade 9', 2),
('Grade 10', 2);
INSERT INTO YearLevel (name, education_level_id) VALUES
('Grade 11', 3),
('Grade 12', 3);
INSERT INTO YearLevel (name, education_level_id) VALUES
('1st Year', 4),
('2nd Year', 4),
('3rd Year', 4),
('4th Year', 4);

INSERT INTO TrophyLevel (name, required_points) VALUES
('Rising Star', 25),
('Shining Scholar', 75),
('Knowledge Seeker', 150),
('Master Learner', 300),
('Academic Achiever', 500),
('Legendary Scholar', 800),
('Elite Mind', 1200),
('Champion of Knowledge', 1800),
('Luminary', 2500),
('Sage of Wisdom', 4000);

