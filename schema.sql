DROP TABLE IF EXISTS Students;
DROP TABLE IF EXISTS Quizzes;
DROP TABLE IF EXISTS Student_Results;

CREATE TABLE Students (
    id INTEGER PRIMARY KEY,
	first_name TEXT,
    last_name TEXT
);

CREATE TABLE Quizzes (
	id INTEGER PRIMARY KEY,
	subject TEXT,
    num_of_questions INTEGER,
    date DATE
);

CREATE TABLE Student_Results (
	student_id INTEGER,
    quiz_id INTEGER,
	result REAL
);

INSERT INTO Students
(id, first_name, last_name)
VALUES
(1, "John", "Smith");


INSERT INTO Quizzes
(id, subject, num_of_questions, date)
VALUES
(1, "Python Basics", 5, "2015-02-05");


INSERT INTO Student_Results
(student_id, quiz_id, result)
VALUES
(1, 1, 85);