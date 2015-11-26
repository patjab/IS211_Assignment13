from flask import Flask
from flask import session
from flask import redirect
from flask import request
from flask import render_template
import sqlite3
import re
import datetime

__author__ = "Patrick Abejar"
app = Flask(__name__)
status_message = ""


class Student:
    """Allows for the easy storage of all data associated with a student. Par-
    ticularly useful when gathering raw data from the database and placing it
    in a list for later calling in am HTML template."""

    def __init__(self, id, first_name, last_name):
        self.id = int(id)
        self.first_name = first_name
        self.last_name = last_name


class Quiz:
    """Allows for the easy storage of all data associated with a quiz. Par-
    ticularly useful when gathering raw data from the database and placing it
    in a list for later calling in an HTML template."""

    def __init__(self, id, subject, num_of_questions, date):
        self.id = int(id)
        self.subject = subject
        self.num_of_questions = int(num_of_questions)
        self.date = date


class Result:
    """Allows for the easy storage of all data associated with a quiz result.
    Particularly useful when gathering raw data from the database and placing
    it in a list for later calling in an HTML template."""

    def __init__(self, quiz_id, grade, date=None, subject=None):
        self.quiz_id = quiz_id
        self.grade = grade
        self.date = date
        self.subject = subject


@app.route('/')
def index():
    """Redirects to the dashboard"""
    return redirect("/dashboard")


@app.route('/login', methods=['GET', 'POST'])
def login():
    """HTML rendered template contains a form that prompts users who have not
    logged in according to cookies to log in. Checks are done in order to
    verify that the inputted username and password are the same of that
    listed in the correct_credentials variable. Returns status messages to be
    displayed in the case of a login failure to the HTML template viewer. This
    is the controller users are directed to if at any time cookies fail to
    indicate a valid user."""
    global status_message

    credentials_filled = 'username' in request.form and \
                         'password' in request.form

    # Must check if credentials are not null, otherwise this boolean storage of
    # correct_credentials will throw an error
    if credentials_filled:
        correct_credentials = request.form['username'] == 'admin' and \
                              request.form['password'] == 'password'

    # Goes to the dashboard if credentials are correct. If a wrong entry is
    # inputted, then an error message will be displayed.
    if credentials_filled and correct_credentials:
        # Adds username to cookies when valid credentials are present
        session['username'] = request.form['username']
        return redirect('/dashboard')
    elif credentials_filled and not correct_credentials:
        status_message = "ERROR: No password matches that username."
    elif not credentials_filled:
        status_message = ""

    return render_template('login.html', status_message=status_message)


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    """Arranges a student roaster and a list of quizzes to be displayed to the
    user by acting as the intermediary between the database and the HTML temp-
    late viewer. This is done with help of the previously declared objects of
    Student and Quiz. Objects are constructed with data from the connected
    database below. Lists produced are then rendered to the HTML viewer."""

    # Prevents non-logged in users from accessing any further material
    if 'username' not in session:
        return redirect('/login')

    conn = sqlite3.connect("hw13.db")

    # These select statements retrieve all relevant data in the form of a list
    # for both students and quizzes as follows:
    # student[0] ==> Student's ID number
    # student[1] ==> Student's First Name
    # student[2] ==> Student's Last Name
    # quiz[0] ==> Quiz ID
    # quiz[1] ==> Subject of Quiz
    # quiz[2] ==> Number of Questions on Quiz
    # quiz[3] ==> Date Quiz was given
    student_list = conn.execute("SELECT * FROM Students ORDER BY id ASC")
    quiz_list = conn.execute("SELECT * FROM Quizzes ORDER BY id ASC")

    # Fills in the lists to be rendered to the HTML template
    student_roaster = []
    for student in student_list.fetchall():
        student_roaster.append(Student(student[0], student[1], student[2]))
    list_of_quizzes = []
    for quiz in quiz_list.fetchall():
        list_of_quizzes.append(Quiz(quiz[0], quiz[1], quiz[2], quiz[3]))

    conn.commit()
    conn.close()

    # Passes student and quiz data to be displayed in an HTML table along with
    # a the name of the current user.
    username = session['username']
    return render_template('dashboard.html', student_roaster=student_roaster,
                           list_of_quizzes=list_of_quizzes, username=username)


@app.route('/student/add', methods=['GET','POST'])
def add_student():
    """Acts as the intermediary between the inputting student data in an HTML
    form, which will be added to the database table of students. Validation
    checks are the main controls that ensure only valid student names are
    being added to the database. The validation checks make sure that only
    alphabetical characters are placed as the student's first and last name
    and that none of these fields are left blank.
    """

    # Prevents non-logged in users from accessing any further material
    if 'username' not in session:
        return redirect('/login')

    global status_message

    first_name = ""
    last_name = ""

    # Pattern provides comparison to the data inputted that only alphabetical
    # characters are being passed through.
    pattern = "^[a-zA-Z]+$"

    # A user is sent in this first clause of the if statement upon 1st arrival
    # into the /student/add controller.
    if not ('fname' in request.form and 'lname' in request.form):
        status_message = ""
        return render_template('addStudent.html',
                               status_message=status_message)
    # Non 1st times of progression through the /student/add controller will be
    # met with the validation checks mentioned above in the function des-
    # cription.
    elif 'fname' in request.form and 'lname' in request.form:
        # First name and last name must have at least one alphabetic character
        if re.search(pattern, request.form['fname']) and \
                re.search(pattern, request.form['lname']):
            first_name = request.form['fname']
            last_name = request.form['lname']
        else:
            status_message="ERROR: You must enter proper first and last" \
                           "names. (Letters only)"
            return render_template('addStudent.html',
                                   status_message=status_message)
    status_message = ""

    # After all validation checks pass then data will be added as follows via
    # SQL insert statements.
    conn = sqlite3.connect("hw13.db")
    add_statement = '''INSERT INTO Students
                       (id, first_name, last_name)
                       VALUES
                       (NULL, "%s", "%s");''' % (first_name, last_name)
    conn.execute(add_statement)
    conn.commit()
    conn.close()

    return redirect('/dashboard')


@app.route('/student/delete', methods=['GET','POST'])
def delete_student():
    """This control is simple in implementation as it just deletes student
    information with respect to the unique student ID provided. There are
    no controls involved other than the regular login cookie check."""

    # Prevents non-logged in users from accessing any further material
    if 'username' not in session:
        return redirect('/login')

    delete_statement = """DELETE FROM Students
                          WHERE id=%s""" % request.form['student_id']
    # Students must also be deleted from their grades table in the database
    delete_assoc_results = """DELETE FROM Student_Results
                              WHERE student_id=%s""" \
                           % request.form['student_id']

    conn = sqlite3.connect("hw13.db")
    conn.execute(delete_statement)
    conn.execute(delete_assoc_results)
    conn.commit()
    conn.close()

    return redirect("/dashboard")


@app.route('/quiz/add', methods=['GET','POST'])
def add_quiz():
    """Adds a quiz to the database contingent on criteria tested below. Quiz
    subject has no validation check other than it must be filled. Number of
    questions information must always be a positive integer. Date of quiz is
    easily validated by trying to construct a datetime object and catching
    an exception if it occurs."""

    # Prevents non-logged in users from accessing any further material
    if 'username' not in session:
        return redirect('/login')

    global status_message

    if 'username' not in session:
        return redirect('/login')

    # Integer numbers only pattern for comparison
    number_only_pattern = "^[0-9]+$"

    all_fields_filled = 'subject' in request.form and \
                        'numOfQuestions' in request.form and \
                        'day' in request.form and \
                        'month' in request.form and \
                        'year' in request.form

    # Checks for existence must occur or server will crash
    if not all_fields_filled:
        status_message = ""
        return render_template('addQuiz.html',
                               status_message=status_message)
    elif all_fields_filled:
        # No validation test is required for subject other than it must exist
        valid_subject = request.form['subject']

        # Validation test checking that numOfQuestions is a number
        if re.search(number_only_pattern, request.form['numOfQuestions']):
            valid_num_of_questions = request.form['numOfQuestions']
        else:
            status_message = "ERROR: Number of questions must be a number."
            return render_template('addQuiz.html',
                                   status_message=status_message)

        # Validation test checking that date is valid utilizing datetime object
        try:
            valid_date = datetime.date(int(request.form['year']),
                                       int(request.form['month']),
                                       int(request.form['day']))
        except ValueError:
            status_message = "ERROR: The date is not valid."
            return render_template('addQuiz.html',
                                   status_message=status_message)

    status_message = ""

    # Arrival at this point means that all data has passed validation and will
    # be inserted into the database.
    conn = sqlite3.connect("hw13.db")
    add_statement = '''INSERT INTO Quizzes
                       (id, subject, num_of_questions, date)
                       VALUES
                       (NULL, "%s", "%s", "%s");'''\
                    % (valid_subject, valid_num_of_questions, valid_date)
    conn.execute(add_statement)
    conn.commit()
    conn.close()

    return redirect('/dashboard')


@app.route('/quiz/delete', methods=['GET','POST'])
def delete_quiz():
    """This control is simple in implementation as it just deletes quiz
    information with respect to the unique quiz ID provided. There are
    no controls involved other than the regular login cookie check."""

    # Prevents non-logged in users from accessing any further material
    if 'username' not in session:
        return redirect('/login')

    delete_statement = """DELETE FROM Quizzes
                          WHERE id=%s;""" % request.form['quiz_id']
    # Quizzes must also be deleted from their corresponding graded entries
    # in Student_Results table
    delete_assoc_result_statement = """DELETE FROM Student_Results
                                       WHERE quiz_id=%s;""" \
                                    % request.form['quiz_id']

    conn = sqlite3.connect("hw13.db")
    conn.execute(delete_statement)
    conn.execute(delete_assoc_result_statement)
    conn.commit()
    conn.close()

    return redirect("/dashboard")


@app.route('/quiz/<id>/results', methods=['GET','POST'])
def anonymous_view(id):
    """Organizes quiz metadata and score information to be displayed without
    associated student names, but student IDs only. Information is retrieved
    databases and then placed in lists within lists to be rendered to an HTML
    viewer."""

    # NO LOGIN CONTROL: THIS CONTROLLER DOES NOT HAVE A LOGIN CHECK ON PURPOSE

    # After executing this statement, data will be ordered as follows:
    # Index 0 ==> Student ID
    # Index 1 ==> (SAME FOR ALL) Date quiz given
    # Index 2 ==> (SAME FOR ALL) Subject of quiz
    # Index 3 ==> Student grade on quiz
    # Index 4 ==> (SAME FOR ALL) Number of questions on the quiz
    # Index 5 ==> (SAME FOR ALL) ID of the quiz
    anonymous_statement = """SELECT Student_Results.student_id, Quizzes.date,
                                Quizzes.subject, Student_Results.result,
                                Quizzes.num_of_questions, Quizzes.id
                             FROM Student_Results
                             LEFT JOIN Quizzes
                             ON Student_Results.quiz_id = Quizzes.id
                             WHERE quiz_id == %s
                             ORDER BY Student_Results.result DESC""" % id

    # Retrieves the current valid quiz id numbers
    quiz_id_list_statement = """SELECT id
                                FROM Quizzes"""

    conn = sqlite3.connect("hw13.db")

    # Gathers information from the database for table display of anonymous
    # quiz results
    grade_data_med = conn.execute(anonymous_statement)
    grade_data = grade_data_med.fetchall()

    # Gathers information from the database to see which quiz IDs are valid
    # in order to let the HTML viewer know what links to display to which
    # quizzes.
    quiz_id_list_med = conn.execute(quiz_id_list_statement)
    quiz_id_list = quiz_id_list_med.fetchall()

    conn.commit()
    conn.close()

    valid_quizzes = []
    for quiz_id in quiz_id_list:
        valid_quizzes.append(quiz_id[0])

    # Lets the user know when to expect quiz data or not, which will allow for
    # the display of table cells or "No results"
    if len(grade_data) == 0:
        has_results = False
    else:
        has_results = True

    return render_template('anonView.html', list_of_quizzes=grade_data,
                           has_results=has_results,
                           valid_quizzes=valid_quizzes)


@app.route('/student/<id>', methods=['GET','POST'])
def student_quiz_details(id):
    """Organizes information by means of an SQL join on the database, which
    will be passed to the rendering method and dispalyed on an HTML viewer."""

    # Prevents non-logged in users from accessing any further material
    if 'username' not in session:
        return redirect('/login')

    # Obtains associated student's full name to be displayed on the top of
    # the page
    student_name_statement = """SELECT first_name, last_name
                                FROM Students
                                WHERE id == %s;
                             """ % id

    # Displays quiz metadata along with student's grade on that quiz by means
    # of a LEFT JOIN on Quizzes with Student_Results modeling in relational
    # format. Filters out information for only that student by his or her stu-
    # dent ID.
    joined_quiz_statement = """SELECT Student_Results.quiz_id,
                                  Quizzes.date, Quizzes.subject,
                                  Student_Results.result
                               FROM Student_Results
                               LEFT JOIN Quizzes
                               ON Student_Results.quiz_id = Quizzes.id
                               WHERE student_id == %s
                               ORDER BY Student_Results.quiz_id ASC;
                            """ % id

    conn = sqlite3.connect("hw13.db")

    student_whole_name = conn.execute(student_name_statement).fetchone()
    student_name = "%s %s" % (student_whole_name[0], student_whole_name[1])

    # Contains a list of all the associated student's quizzes according to the
    # database.
    quiz_results = conn.execute(joined_quiz_statement)

    list_of_grades = []

    # quiz[0] = Quiz ID
    # quiz[1] = Quiz Date
    # quiz[2] = Quiz Subject
    # quiz[3] = Quiz Grade
    # Info is rendered in the order above and will be used to create an object
    # that will allow for the easy access of information at the HTML viewer as
    # it is labeled with descriptive variable names.
    for quiz in quiz_results.fetchall():
        list_of_grades.append(Result(quiz[0], quiz[3], quiz[1], quiz[2]))
    conn.commit()
    conn.close()

    # Provides a means for which the HTML viewer can display "No results" or a
    # HTML table without crashing the server.
    has_results = True
    if len(list_of_grades) == 0:
        has_results = False

    return render_template('quizDetails.html', id=id,
                           student_name=student_name,
                           list_of_grades=list_of_grades,
                           has_results=has_results)


@app.route('/results/add', methods=['GET','POST'])
def add_result():
    """Adds a quiz result to the database contingent on criteria tested below.
    Student and quizzes lists are sent to the HTML viewer to be displayed for
    the user to select which of the two he or she wishes to associate to-
    gether. Grade values must be able to be passed into the float() function
    otherwise an error will be raised stopping the passing of information to
    the database."""

    # Prevents non-logged in users from accessing any further material
    if 'username' not in session:
        return redirect('/login')

    # Checks for existence to determine if this is the user's 1st time in
    # this controller.
    if 'student' in request.form and 'quiz' in request.form and\
                    'grade' in request.form:
        all_values_filled = True
    else:
        all_values_filled = False

    conn = sqlite3.connect("hw13.db")
    # Gets all users' whole name to be displayed and its associated unique ID
    # for behind the scenes student validation
    student_list_statement = """SELECT first_name || " " || last_name, id
                                FROM Students;"""
    # Gets all quizzes' name and id to be displayed and associated unique ID
    # for behind the scenes quiz validation
    quizzes_list_statement = """SELECT id || ". " || subject, id
                                FROM Quizzes
                                ORDER BY id ASC;"""
    student_list = conn.execute(student_list_statement)
    quizzes_list = conn.execute(quizzes_list_statement)

    if not all_values_filled:
        # 1st visitors to this controller will end up here with no error msg
        error_message = ""
        return render_template('addResult.html',
                               list_of_students=student_list.fetchall(),
                               list_of_quizzes=quizzes_list.fetchall(),
                               error_message=error_message)
    else:
        # Validation tests described above
        if request.form['student'] == "not_allowed":
            error_message = "ERROR: You must choose a student."
            return render_template('addResult.html',
                                   list_of_students=student_list.fetchall(),
                                   list_of_quizzes=quizzes_list.fetchall(),
                                   error_message=error_message)
        elif request.form['quiz'] == "not_allowed":
            error_message = "ERROR: You must choose a quiz."
            return render_template('addResult.html',
                                   list_of_students=student_list.fetchall(),
                                   list_of_quizzes=quizzes_list.fetchall(),
                                   error_message=error_message)
        try:
            grade = float(request.form['grade'])
        except ValueError:
            error_message = "ERROR: Please enter a valid number for the grade."
            return render_template('addResult.html',
                                   list_of_students=student_list.fetchall(),
                                   list_of_quizzes=quizzes_list.fetchall(),
                                   error_message=error_message)

    # After all validation tests have passed information is added to the
    # database
    add_grade_statement = """INSERT INTO Student_Results
                             (student_id, quiz_id, result)
                             VALUES
                             (%s, %s, %s);""" % (request.form['student'],
                                                 request.form['quiz'],
                                                 str(grade))
    conn.execute(add_grade_statement)
    conn.commit()
    conn.close()

    return redirect('/dashboard')


@app.route('/results/delete', methods=['GET','POST'])
def delete_result():
    """Delete associated grade information through SQL delete statements."""

    # Prevents non-logged in users from accessing any further material
    if 'username' not in session:
        return redirect('/login')

    delete_statement = """DELETE FROM Student_results
                          WHERE student_id=%s AND quiz_id=%s AND result=%s
                          LIMIT 1;""" % (request.form['student_id'],
                                         request.form['quiz_id'],
                                         request.form['grade'])
    # Grades are not reflected in any other database tables. That's why there
    # is only one delete statement executed in order to delete a grade.

    conn = sqlite3.connect("hw13.db")
    conn.execute(delete_statement)
    conn.commit()
    conn.close()

    return redirect("/student/%s" % request.form['student_id'])


@app.route('/logout')
def logout():
    """Logs out users"""
    # Prevents non-logged in users from accessing any further material
    if 'username' not in session:
        return redirect('/login')

    # Logs out by updating cookies through session object
    session.pop('username', None)
    return redirect('/')

# Secret key for session object
app.secret_key = '\x90\xed:\xd9\xc6#\xcb\x87O\xb6\xe6\xb8\xb4Rm_\xc7\x92' \
                 '\xd9)\x9c+b\xea'

if __name__ == "__main__":
    # RUNS ON PORT 5000 ON 127.0.0.1, SINCE PORT 80 REQUIRES SUDO
    app.run()
