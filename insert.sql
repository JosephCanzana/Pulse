-- ==========================================================
-- SEED DATA FOR LMS DATABASE (lms_db)
-- Includes all tables with valid relationships
-- ==========================================================
USE lms_db;

-- ==========================================================
-- EDUCATION LEVELS
-- ==========================================================
INSERT INTO EducationLevel (name) VALUES
('Elementary'),
('Junior High'),
('Senior High'),
('College');

-- ==========================================================
-- COURSES
-- ==========================================================
INSERT INTO Course (name, education_level_id) VALUES
('Bachelor of Science in Computer Science', 4),
('Bachelor of Science in Education', 4),
('Bachelor of Science in Business Administration', 4);

-- ==========================================================
-- YEAR LEVELS
-- ==========================================================
INSERT INTO YearLevel (name, education_level_id) VALUES
('1st Year', 4),
('2nd Year', 4),
('3rd Year', 4),
('4th Year', 4);

-- ==========================================================
-- DEPARTMENTS
-- ==========================================================
INSERT INTO Department (name, education_level_id) VALUES
('Computer Studies Department', 4),
('Education Department', 4),
('Business Department', 4);

-- ==========================================================
-- USERS
-- ==========================================================
INSERT INTO Users 
(first_name, middle_name, last_name, email, school_id, gender, password, role, is_verified, status) VALUES
-- Teachers
('David',   'J',  'Malan',     '42852005@holycross.edu.ph', '42852005', 'Male',   'mcmY_1946', 'teacher', 1, 1),
('Brian',   NULL, 'Yu',        '42852006@holycross.edu.ph', '42852006', 'Male',   'mcmY_1946', 'teacher', 1, 1),
('Carter',  NULL, 'Zenke',     '42852007@holycross.edu.ph', '42852007', 'Male',   'mcmY_1946', 'teacher', 1, 1),
('Maria',   NULL, 'Cruz',      '42852008@holycross.edu.ph', '42852008', 'Female', 'mcmY_1946', 'teacher', 1, 1),
('John',    NULL, 'Dela Cruz', '42852009@holycross.edu.ph', '42852009', 'Male',   'mcmY_1946', 'teacher', 1, 1),

-- Students
('Joseph',  'C',  'Canzana',   '14462018@holycross.edu.ph', '14462018', 'Male',   'mcmY_1946', 'student', 1, 1),
('Anthony', 'D',  'Dichoso',   '78722024@holycross.edu.ph', '78722024', 'Male',   'mcmY_1946', 'student', 0, 1),
('Tristan', 'H',  'Herrera',   '78542024@holycross.edu.ph', '78542024', 'Male',   'mcmY_1946', 'student', 0, 1),
('Mika',    'L',  'Santos',    '78542025@holycross.edu.ph', '78542025', 'Female', 'mcmY_1946', 'student', 1, 1),
('Ella',    'M',  'Reyes',     '78542026@holycross.edu.ph', '78542026', 'Female', 'mcmY_1946', 'student', 1, 1),
('Leo',     'C',  'Tan',       '78542027@holycross.edu.ph', '78542027', 'Male',   'mcmY_1946', 'student', 1, 1),
('Sarah',   NULL, 'Lim',       '78542028@holycross.edu.ph', '78542028', 'Female', 'mcmY_1946', 'student', 1, 1),
('Ethan',   NULL, 'Cruz',      '78542029@holycross.edu.ph', '78542029', 'Male',   'mcmY_1946', 'student', 1, 1),
('Eve',     NULL, 'Lopez',     '78542030@holycross.edu.ph', '78542030', 'Female', 'mcmY_1946', 'student', 0, 1),
('Noah',    NULL, 'Garcia',    '78542031@holycross.edu.ph', '78542031', 'Male',   'mcmY_1946', 'student', 1, 1);

-- ==========================================================
-- TEACHER PROFILES
-- ==========================================================
INSERT INTO TeacherProfile (user_id, department_id, education_level_id) VALUES
(2, 1, 4),  -- David Malan, CS Dept
(3, 1, 4),  -- Brian Yu
(4, 1, 4),  -- Carter Zenke
(5, 2, 4),  -- Maria Cruz
(6, 3, 4);  -- John Dela Cruz

-- ==========================================================
-- SECTION
-- ==========================================================
INSERT INTO Section (name, year_id, course_id, academic_year, teacher_id, status) VALUES
('BSCS-2A', 2, 1, '2025-2026', 1, 1);

-- ==========================================================
-- STUDENT PROFILES
-- ==========================================================
INSERT INTO StudentProfile (user_id, education_level_id, course_id, section_id, year_id, is_suspended) VALUES
(7,  4, 1, 1, 2, 0),  -- Joseph   - BSCS-2A
(8,  4, 1, 1, 2, 0),  -- Anthony  - BSCS-2A
(9,  4, 1, 1, 2, 0),  -- Tristan  - BSCS-2A
(10, 4, 1, 1, 1, 0),  -- Mika
(11, 4, 1, 1, 1, 0),  -- Ella
(12, 4, 1, 1, 1, 0),  -- Leo
(13, 4, 1, 1, 1, 0),  -- Sarah
(14, 4, 1, 1, 1, 0),  -- Ethan
(15, 4, 1, 1, 1, 0),  -- Eve
(16, 4, 1, 1, 1, 0);  -- Noah

-- ==========================================================
-- SUBJECTS
-- ==========================================================
INSERT INTO Subject (name, education_level_id) VALUES
('Programming Fundamentals', 4),
('Data Structures and Algorithms', 4),
('Database Systems', 4),
('Computer Networks', 4),
('Web Development', 4);

-- ==========================================================
-- CLASSES
-- (Link teachers with subjects and section BSCS-2A)
-- ==========================================================
INSERT INTO Class (teacher_id, subject_id, section_id, status) VALUES
(1, 1, 1, 'active'),   -- Malan teaches Programming Fundamentals
(1, 2, 1, 'active'),   -- Malan teaches DSA
(2, 3, 1, 'active'),   -- Yu teaches Database Systems
(3, 4, 1, 'active'),   -- Zenke teaches Networks
(4, 5, 1, 'active');   -- Maria teaches Web Development

-- ==========================================================
-- CLASS STUDENTS
-- Enroll all students in each class
-- ==========================================================
INSERT INTO ClassStudent (class_id, student_id, status) VALUES
-- Class 1 (Programming Fundamentals)
(1, 1, 'active'), (1, 2, 'active'), (1, 3, 'active'), (1, 4, 'active'), (1, 5, 'active'),
(1, 6, 'active'), (1, 7, 'active'), (1, 8, 'active'), (1, 9, 'active'), (1, 10, 'active'),

-- Class 2 (DSA)
(2, 1, 'active'), (2, 2, 'active'), (2, 3, 'active'),

-- Class 3 (Database Systems)
(3, 1, 'active'), (3, 2, 'active'),

-- Class 4 (Networks)
(4, 1, 'active'),

-- Class 5 (Web Development)
(5, 4, 'active'), (5, 5, 'active'), (5, 6, 'active');

-- ==========================================================
-- LESSONS
-- ==========================================================
INSERT INTO Lesson (class_id, lesson_number, title, description) VALUES
(1, 1, 'Introduction to Programming', 'Overview of programming basics and syntax.'),
(1, 2, 'Control Structures', 'Using conditions and loops.'),
(2, 1, 'Arrays and Linked Lists', 'Introduction to fundamental data structures.'),
(3, 1, 'Introduction to Databases', 'Understanding relational databases.'),
(4, 1, 'Network Fundamentals', 'Basics of computer networking.'),
(5, 1, 'HTML & CSS Basics', 'Introduction to front-end web development.');

-- ==========================================================
-- LESSON FILES
-- ==========================================================
INSERT INTO LessonFile (lesson_id, file_name, file_path, file_type) VALUES
(1, 'intro.pdf', '/uploads/lessons/intro.pdf', 'application/pdf'),
(2, 'loops.pptx', '/uploads/lessons/loops.pptx', 'application/vnd.ms-powerpoint'),
(3, 'arrays.docx', '/uploads/lessons/arrays.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
(4, 'databases.pdf', '/uploads/lessons/databases.pdf', 'application/pdf'),
(5, 'networks.pdf', '/uploads/lessons/networks.pdf', 'application/pdf'),
(6, 'html_basics.zip', '/uploads/lessons/html_basics.zip', 'application/zip');

-- ==========================================================
-- STUDENT LESSON PROGRESS
-- (Simulate progress for Joseph and Anthony)
-- ==========================================================
INSERT INTO StudentLessonProgress (class_id, lesson_id, student_id, status, completed_at) VALUES
(1, 1, 1, 'completed', NOW()),
(1, 2, 1, 'in_progress', NULL),
(1, 1, 2, 'completed', NOW()),
(2, 1, 1, 'not_started', NULL),
(3, 1, 1, 'not_started', NULL);
