USE lms_db;
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
('Bachelor Of Science In Education', 4),
('STEM', 3),
('TVL', 3),
('ABM', 3);

-- INSERT Year Levels
INSERT INTO YearLevel (name, education_level_id) VALUES
('Grade 1', 1),
('Grade 2', 1),
('Grade 3', 1),
('Grade 4', 1),
('Grade 5', 1),
('Grade 6', 1),
('Grade 7', 2),
('Grade 8', 2),
('Grade 9', 2),
('Grade 10', 2),
('Grade 11', 3),
('Grade 12', 3),
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

-- =====================================
-- USERS
-- =====================================
INSERT INTO Users (first_name, middle_name, last_name, email, school_id, gender, password, role, is_verified, status) VALUES
('Admin', 'A', 'User', 'administrator@holycross.edu.ph', 'LMS001', 'Other', 'adminpassword', 'admin', 1, 1),

-- Students
('Joseph', 'C', 'Canzana', '14462018@holycross.edu.ph', '14462018', 'Male', 'mcmY_1946', 'student', 1, 1),
('Anthony', 'D', 'Dichoso', '78722024@holycross.edu.ph', '78722024', 'Male', 'mcmY_1946', 'student', 0, 1),
('Tristan', 'H', 'Herrera', '78542024@holycross.edu.ph', '78542024', 'Male', 'mcmY_1946', 'student', 0, 1),
('Mika', 'L', 'Santos', '78542025@holycross.edu.ph', '78542025', 'Female', 'mcmY_1946', 'student', 1, 1),
('Ella', 'M', 'Reyes', '78542026@holycross.edu.ph', '78542026', 'Female', 'mcmY_1946', 'student', 1, 1),
('Leo', 'C', 'Tan', '78542027@holycross.edu.ph', '78542027', 'Male', 'mcmY_1946', 'student', 1, 1),
('Sarah', '', 'Lim', '78542028@holycross.edu.ph', '78542028', 'Female', 'mcmY_1946', 'student', 1, 1),
('Ethan', '', 'Cruz', '78542029@holycross.edu.ph', '78542029', 'Male', 'mcmY_1946', 'student', 1, 1),
('Eve', '', 'Lopez', '78542030@holycross.edu.ph', '78542030', 'Female', 'mcmY_1946', 'student', 0, 1),
('Noah', '', 'Garcia', '78542031@holycross.edu.ph', '78542031', 'Male', 'mcmY_1946', 'student', 1, 1),

-- Teachers
('David', 'J', 'Malan', '42852005@holycross.edu.ph', '42852005', 'Male', 'mcmY_1946', 'teacher', 1, 1),
('Brian', '', 'Yu', '42852006@holycross.edu.ph', '42852006', 'Male', 'mcmY_1946', 'teacher', 1, 1),
('Carter', '', 'Zenke', '42852007@holycross.edu.ph', '42852007', 'Male', 'mcmY_1946', 'teacher', 1, 1),
('Maria', '', 'Cruz', '42852008@holycross.edu.ph', '42852008', 'Female', 'mcmY_1946', 'teacher', 1, 1),
('John', '', 'Dela Cruz', '42852009@holycross.edu.ph', '42852009', 'Male', 'mcmY_1946', 'teacher', 1, 1),
('Ana', '', 'Santos', '42852010@holycross.edu.ph', '42852010', 'Female', 'mcmY_1946', 'teacher', 1, 1);

-- =====================================
-- TEACHER PROFILE
-- =====================================
INSERT INTO TeacherProfile (user_id, department_id, education_level_id) VALUES
(12, 4, 4), -- David Malan
(13, 4, 4), -- Brian Yu
(14, 3, 3), -- Carter Zenke
(15, 2, 2), -- Maria Cruz
(16, 1, 1), -- John Dela Cruz
(17, 5, 4); -- Ana Santos

-- =====================================
-- SECTIONS
-- =====================================
INSERT INTO Section (name, year_id, course_id, academic_year, status, teacher_id) VALUES
-- =========================
-- Elementary
-- =========================
('Rose', 1, NULL, '2025-2026', 1, 5),
('Sunflower', 1, NULL, '2025-2026', 1, 5),
('Tree', 2, NULL, '2025-2026', 1, 5),
('Bamboo', 2, NULL, '2025-2026', 1, 5),
('Tulip', 3, NULL, '2025-2026', 1, 5),
('Daisy', 4, NULL, '2025-2026', 1, 5),
('Iris', 5, NULL, '2025-2026', 1, 5),
('Lily', 6, NULL, '2025-2026', 1, 5),

-- =========================
-- Junior High
-- =========================
('Cecilia', 7, NULL, '2025-2026', 1, 4),
('Luke', 7, NULL, '2025-2026', 1, 4),
('Mathew', 8, NULL, '2025-2026', 1, 4),
('John', 8, NULL, '2025-2026', 1, 4),
('Mark', 9, NULL, '2025-2026', 1, 4),
('Paul', 9, NULL, '2025-2026', 1, 4),
('Peter', 10, NULL, '2025-2026', 1, 4),
('James', 10, NULL, '2025-2026', 1, 4),

-- =========================
-- Senior High
-- =========================
('Stem-11A', 11, 4, '2025-2026', 1, 3),
('Stem-11B', 11, 4, '2025-2026', 1, 3),
('Tvl-11A', 11, 5, '2025-2026', 1, 3),
('Abm-12A', 12, 6, '2025-2026', 1, 3),
('Abm-12B', 12, 6, '2025-2026', 1, 3),
('Stem-12A', 12, 4, '2025-2026', 1, 3),

-- =========================
-- College
-- =========================
('Bscs-1A', 13, 1, '2025-2026', 1, 1),
('Bscs-1B', 13, 1, '2025-2026', 1, 1),
('Bscs-2A', 14, 1, '2025-2026', 1, 2),
('Bscs-2B', 14, 1, '2025-2026', 1, 2),
('Bscs-3A', 15, 1, '2025-2026', 1, 2),
('Bscs-4A', 16, 1, '2025-2026', 1, 2),
('Bshm-1A', 13, 2, '2025-2026', 1, 6),
('Bshm-1B', 13, 2, '2025-2026', 1, 6),
('Bshm-2A', 14, 2, '2025-2026', 1, 6),
('Bsed-1A', 13, 3, '2025-2026', 1, 6),
('Bsed-2A', 14, 3, '2025-2026', 1, 6);

-- =====================================
-- SUBJECTS
-- =====================================
INSERT INTO Subject (name, education_level_id) VALUES
('English', 1),
('Mathematics', 1),
('Science', 1),
('Filipino', 1),
('Araling Panlipunan', 1),
('English', 2),
('Mathematics', 2),
('Science', 2),
('Filipino', 2),
('Social Studies', 2),
('Physics', 3),
('Biology', 3),
('Accounting', 3),
('Business Math', 3),
('Programming 1', 4),
('Programming 2', 4),
('Data Structures', 4),
('Algorithms', 4),
('Database Systems', 4);

-- =====================================
-- STUDENT PROFILE
-- =====================================
INSERT INTO StudentProfile (user_id, education_level_id, course_id, section_id, year_id) VALUES
(2, 4, 1, 7, 13),
(3, 4, 1, 7, 13),
(4, 4, 1, 7, 13),
(5, 3, 4, 5, 11),
(6, 3, 6, 6, 12),
(7, 1, NULL, 1, 1),
(8, 1, NULL, 2, 2),
(9, 2, NULL, 3, 7),
(10, 2, NULL, 4, 8),
(11, 4, 2, 9, 13);

-- =====================================
-- CLASSES
-- =====================================
INSERT INTO Class (teacher_id, subject_id, section_id, status) VALUES
-- =======================
-- Elementary (Teacher 5)
-- =======================
(5, 1, 1, 'active'),  -- Rose - English
(5, 2, 1, 'active'),  -- Rose - Math
(5, 3, 2, 'active'),  -- Tree - Science
(5, 4, 2, 'active'),  -- Tree - Filipino
(5, 5, 3, 'active'),  -- Tulip - Araling Panlipunan

-- =======================
-- Junior High (Teacher 4)
-- =======================
(4, 6, 9, 'active'),  -- Cecilia - English
(4, 7, 9, 'active'),  -- Cecilia - Math
(4, 8, 10, 'active'), -- Luke - Science
(4, 9, 10, 'active'), -- Luke - Filipino
(4, 10, 11, 'active'),-- Mathew - Social Studies

-- =======================
-- Senior High (Teacher 3)
-- =======================
(3, 11, 17, 'active'), -- Stem-11A - Physics
(3, 12, 17, 'active'), -- Stem-11A - Biology
(3, 13, 18, 'active'), -- Stem-11B - Accounting
(3, 14, 19, 'active'), -- Tvl-11A - Business Math
(3, 11, 20, 'active'), -- Abm-12A - Physics
(3, 13, 21, 'active'), -- Abm-12B - Accounting

-- =======================
-- College (Teachers 1, 2, 6)
-- =======================
-- BSCS - David Malan (1)
(1, 15, 22, 'active'), -- Bscs-1A - Programming 1
(1, 16, 22, 'active'), -- Bscs-1A - Programming 2
(1, 17, 22, 'active'), -- Bscs-1A - Data Structures
-- BSCS - Brian Yu (2)
(2, 18, 24, 'active'), -- Bscs-2A - Algorithms
(2, 19, 24, 'active'), -- Bscs-2A - Database Systems
-- BSHM - Ana Santos (6)
(6, 1, 28, 'active'),  -- Bshm-1A - English
(6, 2, 28, 'active'),  -- Bshm-1A - Math
(6, 3, 29, 'active'),  -- Bshm-1B - Science
-- BSED - Ana Santos (6)
(6, 1, 31, 'active'),  -- Bsed-1A - English
(6, 2, 32, 'active');  -- Bsed-2A - Math


-- =====================================
-- LESSONS
-- =====================================
INSERT INTO Lesson (class_id, lesson_number, title, description) VALUES
-- =======================
-- Elementary
-- =======================
(1, 1, 'Learning the Alphabet', 'Recognizing and pronouncing letters A–Z.'),
(1, 2, 'Basic Words and Sentences', 'Combining letters to form simple words.'),
(2, 1, 'Counting Numbers 1–100', 'Understanding number patterns and basic addition.'),
(3, 1, 'Introduction to Plants and Animals', 'Identifying living and nonliving things.'),
(4, 1, 'Pagkilala sa Alpabetong Filipino', 'Pag-aaral ng mga titik ng alpabetong Filipino.'),
(5, 1, 'Mga Bayani ng Pilipinas', 'Pagkilala sa mga pambansang bayani at kanilang ambag.'),

-- =======================
-- Junior High
-- =======================
(6, 1, 'Grammar Basics', 'Understanding sentence structure and parts of speech.'),
(6, 2, 'Creative Writing', 'Composing simple essays and short stories.'),
(7, 1, 'Introduction to Algebra', 'Learning variables, constants, and expressions.'),
(8, 1, 'Matter and Its Properties', 'Exploring solids, liquids, and gases.'),
(9, 1, 'Wikang Pambansa', 'Pag-unawa sa gamit ng Wikang Filipino sa pang-araw-araw na buhay.'),
(10, 1, 'History of the Philippines', 'Learning about key historical events and figures.'),

-- =======================
-- Senior High
-- =======================
(11, 1, 'Physics Fundamentals', 'Introduction to motion, force, and energy.'),
(11, 2, 'Work and Power', 'Understanding relationships between force, work, and energy.'),
(12, 1, 'Introduction to Biology', 'Studying cells, tissues, and organisms.'),
(13, 1, 'Accounting Principles', 'Understanding the basics of bookkeeping and ledgers.'),
(14, 1, 'Business Math Basics', 'Applying math in business transactions and finance.'),
(15, 1, 'Advanced Physics Concepts', 'Analyzing real-world applications of motion and energy.'),
(16, 1, 'Financial Accounting', 'Deeper understanding of assets, liabilities, and equity.'),

-- =======================
-- College (BSCS)
-- =======================
(17, 1, 'Introduction to Programming', 'Overview of programming concepts and syntax.'),
(17, 2, 'Variables and Data Types', 'Understanding primitive types and variable usage.'),
(18, 1, 'Functions and Loops', 'Exploring control flow and reusable code.'),
(19, 1, 'Data Structures Intro', 'Understanding arrays, stacks, and queues.'),
(20, 1, 'Algorithm Basics', 'Learning sorting and searching algorithms.'),
(21, 1, 'Database Fundamentals', 'Designing relational databases and ER diagrams.'),

-- =======================
-- College (BSHM)
-- =======================
(22, 1, 'Effective Communication', 'Improving English communication skills for hospitality.'),
(23, 1, 'Basic Mathematics for Hospitality', 'Learning practical math for business operations.'),
(24, 1, 'Science in the Kitchen', 'Understanding scientific principles in food preparation.'),

-- =======================
-- College (BSED)
-- =======================
(25, 1, 'Teaching Strategies', 'Learning effective methods of classroom teaching.'),
(26, 1, 'Mathematical Concepts for Educators', 'Applying mathematical reasoning in teaching.');


-- =====================================
-- LESSON FILES
-- =====================================
INSERT INTO LessonFile (lesson_id, file_name, file_path, file_type) VALUES
((SELECT id FROM Lesson WHERE title='Learning the Alphabet' LIMIT 1),
 'alphabet.pdf', '/uploads/lessons/alphabet.pdf', 'application/pdf'),

((SELECT id FROM Lesson WHERE title='Basic Words and Sentences' LIMIT 1),
 'basic_words.pptx', '/uploads/lessons/basic_words.pptx', 'application/vnd.ms-powerpoint'),

((SELECT id FROM Lesson WHERE title='Counting Numbers 1–100' LIMIT 1),
 'counting_numbers.pdf', '/uploads/lessons/counting_numbers.pdf', 'application/pdf'),

((SELECT id FROM Lesson WHERE title='Introduction to Plants and Animals' LIMIT 1),
 'plants_animals.pptx', '/uploads/lessons/plants_animals.pptx', 'application/vnd.ms-powerpoint'),

((SELECT id FROM Lesson WHERE title='Grammar Basics' LIMIT 1),
 'grammar_basics.pdf', '/uploads/lessons/grammar_basics.pdf', 'application/pdf'),

((SELECT id FROM Lesson WHERE title='Creative Writing' LIMIT 1),
 'creative_writing.docx', '/uploads/lessons/creative_writing.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),

((SELECT id FROM Lesson WHERE title='Introduction to Programming' LIMIT 1),
 'intro_programming.pdf', '/uploads/lessons/intro_programming.pdf', 'application/pdf'),

((SELECT id FROM Lesson WHERE title='Variables and Data Types' LIMIT 1),
 'variables_data_types.pptx', '/uploads/lessons/variables_data_types.pptx', 'application/vnd.ms-powerpoint'),

((SELECT id FROM Lesson WHERE title='Functions and Loops' LIMIT 1),
 'functions_loops.pdf', '/uploads/lessons/functions_loops.pdf', 'application/pdf'),

((SELECT id FROM Lesson WHERE title='Data Structures Intro' LIMIT 1),
 'data_structures.pdf', '/uploads/lessons/data_structures.pdf', 'application/pdf'),

((SELECT id FROM Lesson WHERE title='Algorithm Basics' LIMIT 1),
 'algorithms.pdf', '/uploads/lessons/algorithms.pdf', 'application/pdf'),

((SELECT id FROM Lesson WHERE title='Database Fundamentals' LIMIT 1),
 'database_fundamentals.pdf', '/uploads/lessons/database_fundamentals.pdf', 'application/pdf');

-- =====================================
-- STUDENT LESSON PROGRESS
-- =====================================
INSERT INTO StudentLessonProgress (class_id, lesson_id, student_id, status) VALUES
(1, 1, 1, 'completed'),
(1, 1, 2, 'in_progress'),
(2, 3, 1, 'not_started');
