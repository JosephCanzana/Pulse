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
    is_suspended BOOLEAN NOT NULL DEFAULT FALSE,
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
    completed_at DATETIME NULL,
    FOREIGN KEY (class_id) REFERENCES Class(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (lesson_id) REFERENCES Lesson(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES StudentProfile(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    UNIQUE KEY unique_progress(class_id, lesson_id, student_id)
);

INSERT INTO Users (first_name, middle_name, last_name, email, school_id, gender, password, role, is_verified, status) VALUES
('Admin', 'A', 'User', 'administrator@holycross.edu.ph', 'LMS001', 'Other', 'adminpassword', 'admin', 1, 1);
