from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///school.db'  # Ensure this path is correct
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'  # For using flash messages

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Define the Course model
class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(10), nullable=False, unique=True)
    course_title = db.Column(db.String(100), nullable=False)
    course_type = db.Column(db.String(50), nullable=False)
    year_level = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f'<Course {self.course_code}>'


# Define the Student model
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(10), nullable=False, unique=True)
    student_name = db.Column(db.String(100), nullable=False)
    course_code = db.Column(db.String(10), db.ForeignKey('course.course_code'), nullable=False)
    block_name = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), default='enrolled')

    def __repr__(self):
        return f'<Student {self.student_name}>'


# Define the Block model
class Block(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    block_name = db.Column(db.String(10), nullable=False)
    course_code = db.Column(db.String(10), db.ForeignKey('course.course_code'), nullable=False)

    def __repr__(self):
        return f'<Block {self.block_name}>'


# Initialize the database and create tables
with app.app_context():
    db.create_all()  # This will create the tables based on the defined models

# Route to render the login page
@app.route('/')
def login():
    return render_template('login.html')


# Route to handle login form submission
@app.route('/login', methods=['POST'])
def login_post():
    username = request.form['username']
    password = request.form['password']
    
    # Simulate login success (replace with actual authentication logic)
    if username == 'admin' and password == 'admin123':
        flash('Login successful', 'success')
        return redirect(url_for('dashboard'))  # Redirect to the dashboard if successful
    else:
        flash('Incorrect username or password', 'danger')
        return render_template('login.html')

# Route to render the dashboard page
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


# Route for the "Courses" page with buttons for "Add Course" and "View Courses"
@app.route('/courses')
def courses_page():
    return render_template('courses.html')


# Route for the "Add Course" page
@app.route('/add-course', methods=['GET', 'POST'])
def add_course():
    if request.method == 'POST':
        course_code = request.form['courseCode']
        course_title = request.form['courseTitle']
        course_type = request.form['courseType']
        year_level = request.form['yearLevel']
        
        # Add course to the database
        new_course = Course(course_code=course_code, course_title=course_title, course_type=course_type, year_level=year_level)
        db.session.add(new_course)
        db.session.commit()
        
        flash(f'Course {course_code} added successfully', 'success')
        return redirect(url_for('courses_page'))  # After adding, redirect to courses page
    return render_template('add-course.html')


# Route for viewing courses
@app.route('/view-courses')
def view_courses():
    # Retrieve all courses from the database
    courses = Course.query.all()
    lecture_courses = [course for course in courses if course.course_type == 'Lecture']
    lab_courses = [course for course in courses if course.course_type == 'Laboratory']
    lecture_lab_courses = [course for course in courses if course.course_type == 'Lecture/Laboratory']

    return render_template('view-courses.html', 
                           lecture_courses=lecture_courses, 
                           lab_courses=lab_courses, 
                           lecture_lab_courses=lecture_lab_courses)


# Route to display grading system for a specific course
@app.route('/course/<course_code>')
def course_details(course_code):
    # Find the course with the matching course_code
    course = Course.query.filter_by(course_code=course_code).first()
    if course:
        return render_template('course-details.html', course=course)
    else:
        return "Course not found", 404


# Route for the "Student Management" page
@app.route('/student-management')
def student_management():
    return render_template('student-management.html')


# Route to create a new block and select a course
@app.route('/create-block', methods=['GET', 'POST'])
def create_block():
    if request.method == 'POST':
        block_name = request.form['blockName']
        return redirect(url_for('select_course', block_name=block_name))
    return render_template('create-block.html')


# Route to select a course for the block
@app.route('/select-course/<block_name>', methods=['GET', 'POST'])
def select_course(block_name):
    if request.method == 'POST':
        course_code = request.form['courseCode']
        new_block = Block(block_name=block_name, course_code=course_code)
        db.session.add(new_block)
        db.session.commit()
        flash(f'Block {block_name} created for course {course_code}', 'success')
        return redirect(url_for('view_blocks'))
    courses = Course.query.all()
    return render_template('select-course.html', courses=courses, block_name=block_name)


# Route to view all courses with their blocks
@app.route('/view-blocks')
def view_blocks():
    courses = Course.query.all()
    blocks = Block.query.all()
    return render_template('view-blocks.html', courses=courses, blocks=blocks)


# Route to show block details and add students
@app.route('/block/<course_code>/<block_name>', methods=['GET', 'POST'])
def block_details(course_code, block_name):
    course = Course.query.filter_by(course_code=course_code).first()
    
    # Fetch the students already in this block
    students_in_block = Student.query.filter_by(course_code=course_code, block_name=block_name).all()

    if request.method == 'POST':
        # Check if the block has reached its maximum capacity of 60 students
        if len(students_in_block) >= 60:
            error_message = "This block has reached its maximum capacity of 60 students."
            return render_template('add-student.html', course_code=course_code, block_name=block_name, error_message=error_message)
        
        # If there is space in the block, add the new student
        student_id = request.form['studentId']
        student_name = request.form['studentName']
        new_student = Student(student_id=student_id, student_name=student_name, course_code=course_code, block_name=block_name)
        db.session.add(new_student)
        db.session.commit()
        
        flash(f'Student {student_name} added to {block_name}', 'success')
        return redirect(url_for('block_details', course_code=course_code, block_name=block_name))

    # If it's a GET request, show the list of students in this block
    students = Student.query.filter_by(course_code=course_code, block_name=block_name).all()
    
    return render_template('block-details.html', course=course, block_name=block_name, students=students)


@app.route('/add-student', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        student_id = request.form['studentId']
        student_name = request.form['studentName']
        course_code = request.form['courseCode']
        block_name = request.form['blockName']
        
        # Ensure block and course exist
        course = Course.query.filter_by(course_code=course_code).first()
        if not course:
            flash(f"Course {course_code} not found", 'danger')
            return redirect(url_for('add_student'))
        
        block = Block.query.filter_by(block_name=block_name, course_code=course_code).first()
        if not block:
            flash(f"Block {block_name} not found for course {course_code}", 'danger')
            return redirect(url_for('add_student'))

        # Add student to the database
        new_student = Student(student_id=student_id, student_name=student_name, course_code=course_code, block_name=block_name)
        db.session.add(new_student)
        db.session.commit()
        
        flash(f'Student {student_name} added to block {block_name}', 'success')
        return redirect(url_for('block_details', course_code=course_code, block_name=block_name))  # After adding, redirect to block details
    return render_template('add-student.html')



# Route to update a student
@app.route('/update-student/<int:id>', methods=['GET', 'POST'])
def update_student(id):
    student = Student.query.get_or_404(id)
    if request.method == 'POST':
        student.student_name = request.form['studentName']
        student.course_code = request.form['courseCode']
        student.block_name = request.form['blockName']
        student.status = request.form['status']
        db.session.commit()
        flash(f'Student {student.student_name} updated successfully', 'success')
        return redirect(url_for('block_details', course_code=student.course_code, block_name=student.block_name))
    return render_template('update-student.html', student=student)


# Route to delete a student
@app.route('/delete-student/<int:id>', methods=['POST'])
def delete_student(id):
    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    flash(f'Student {student.student_name} deleted', 'success')
    return redirect(url_for('block_details', course_code=student.course_code, block_name=student.block_name))


# Route to delete a block
@app.route('/delete-block/<int:id>', methods=['POST'])
def delete_block(id):
    block = Block.query.get_or_404(id)
    db.session.delete(block)
    db.session.commit()
    flash(f'Block {block.block_name} deleted', 'success')
    return redirect(url_for('view_blocks'))


# Route to delete a course
@app.route('/delete-course/<int:id>', methods=['POST'])
def delete_course(id):
    course = Course.query.get_or_404(id)
    db.session.delete(course)
    db.session.commit()
    flash(f'Course {course.course_code} deleted', 'success')
    return redirect(url_for('view_courses'))


@app.route('/view-enrolled-students/<course_code>/<block_name>')
def view_enrolled_students(course_code, block_name):
    # Retrieve students enrolled in the specified course and block
    students = Student.query.filter_by(course_code=course_code, block_name=block_name).all()
    
    # Retrieve the course details for the header
    course = Course.query.filter_by(course_code=course_code).first()
    
    if not students:
        flash(f"No students enrolled in block {block_name} for course {course_code}", 'info')
    
    return render_template('view-enrolled-students.html', course=course, block_name=block_name, students=students)

#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# Route to view all courses with their blocks for viewing student enrollment
@app.route('/view-student-enroll')
def view_student_enroll():
    courses = Course.query.all()
    blocks = Block.query.all()
    return render_template('view-student-enroll.html', courses=courses, blocks=blocks)


@app.route('/view-students/<course_code>/<block_name>')
def view_students_in_block(course_code, block_name):
    # Retrieve the course and students
    course = Course.query.filter_by(course_code=course_code).first_or_404()
    students = Student.query.filter_by(course_code=course_code, block_name=block_name).all()
    
    # Determine which template to render based on course type
    if course.course_type == "Laboratory":
        template = 'students-enrolled-laboratory.html'
    elif course.course_type == "Lecture":
        template = 'students-enrolled-lecture.html'
    elif course.course_type == "Lecture/Laboratory":
        template = 'students-enrolled-lecture-lab.html'
    else:
        template = 'students-enrolled-laboratory.html'  # Default to laboratory if undefined

    # Render the appropriate template
    return render_template(template, course=course, block_name=block_name, students=students)


@app.route('/compute-grade', methods=['GET', 'POST'])
def compute_grade():
    courses = Course.query.all()
    blocks = Block.query.all()
    
    if request.method == 'POST':
        # Retrieve the user input for HPS values
        course_code = request.form.get('courseCode')
        block_name = request.form.get('blockName')
        
        # Get number of quizzes, seatworks, and lab reports from the form
        num_quizzes = int(request.form.get('num_quizzes', 0))
        num_seatworks = int(request.form.get('num_seatworks', 0))
        num_lab_reports = int(request.form.get('num_lab_reports', 0))
        
        # Retrieve HPS inputs for quizzes and seatworks
        hps_quizzes = [float(request.form.get(f"hps_quiz_{i+1}", 0)) for i in range(num_quizzes)]
        hps_seatworks = [float(request.form.get(f"hps_seatwork_{i+1}", 0)) for i in range(num_seatworks)]
        
        # Get the list of students for the specific course and block
        students = Student.query.filter_by(course_code=course_code, block_name=block_name).all()
        
        # Render the template and pass these values
        return render_template(
            'students-enrolled-dynamic.html', 
            students=students, 
            course_code=course_code, 
            block_name=block_name, 
            num_quizzes=num_quizzes, 
            num_seatworks=num_seatworks, 
            num_lab_reports=num_lab_reports, 
            hps_quizzes=hps_quizzes,
            hps_seatworks=hps_seatworks
        )
    
    return render_template('student-grade-calculation.html', courses=courses, blocks=blocks)

@app.route('/final-term/<course_code>/<block_name>')
def final_term(course_code, block_name):
    course = Course.query.filter_by(course_code=course_code).first_or_404()
    students = Student.query.filter_by(course_code=course_code, block_name=block_name).all()
    
    # Determine which template to render based on course type for final term
    if course.course_type == "Laboratory":
        template = 'final-term-laboratory.html'
    elif course.course_type == "Lecture":
        template = 'final-term-lecture.html'
    elif course.course_type == "Lecture/Laboratory":
        template = 'final-term-lecture-lab.html'
    else:
        template = 'final-term-laboratory.html'  # Default to laboratory if undefined

    return render_template(template, course=course, block_name=block_name, students=students)

@app.route('/compute_final_grade', methods=['POST'])
def compute_final_grade():
    # Logic to compute and save final grades
    # Retrieve form data and process final grades
    # Redirect to a confirmation or another page
    pass


@app.route('/process_grades', methods=['POST'])
def process_grades():
    term = request.form.get('term')  # Get term (midterm or final)
    students = []  # Replace with your actual student data fetching logic
    
    for student in students:
        # Fetch quiz, seatwork, attendance, and exam scores for each student
        quiz1 = float(request.form.get(f'quiz_{student.id}_1', 0))
        quiz2 = float(request.form.get(f'quiz_{student.id}_2', 0))
        quiz3 = float(request.form.get(f'quiz_{student.id}_3', 0))

        quiz_hps1 = float(request.form.get(f'quiz_hps_1', 0))
        quiz_hps2 = float(request.form.get(f'quiz_hps_2', 0))
        quiz_hps3 = float(request.form.get(f'quiz_hps_3', 0))
        
        quiz_total = (quiz1 + quiz2 + quiz3) / (quiz_hps1 + quiz_hps2 + quiz_hps3) * 100
        
        # Attendance and Compilation
        attendance = float(request.form.get(f'attendance_{student.id}', 0))
        hppd = float(request.form.get('hppd', 0))
        attendance_score = attendance / hppd * 100
        
        compilation = float(request.form.get(f'compilation_{student.id}', 0))
        hps = float(request.form.get('hps', 0))
        compilation_score = compilation / hps * 100
        
        # Midterm Grade calculation
        if term == 'midterm':
            midterm_exam = float(request.form.get(f'midterm_exam_{student.id}', 0))
            midterm_hps = float(request.form.get('midterm_hps', 0))
            midterm_exam_score = midterm_exam / midterm_hps * 100
            midterm_grade = (quiz_total * 0.30) + (attendance_score * 0.10) + \
                            (compilation_score * 0.05) + (midterm_exam_score * 0.40)
            student['midterm_grade'] = round(midterm_grade, 2)
        
        # Final Term Grade calculation
        elif term == 'final':
            final_exam = float(request.form.get(f'final_exam_{student.id}', 0))
            fte_hps = float(request.form.get('fte_hps', 0))
            final_exam_score = final_exam / fte_hps * 100
            final_grade = (quiz_total * 0.30) + (attendance_score * 0.10) + \
                          (compilation_score * 0.05) + (final_exam_score * 0.40)
            student['final_grade'] = round(final_grade, 2)

    # Return the template with updated students' grades
    return render_template('grades_template.html', students=students)


@app.route('/compute_semestral_grade', methods=['POST'])
def compute_semestral_grade():
    # Get the final term grade (assuming it is passed from the form)
    final_term_grade = float(request.form['final_term_grade'])
    
    # For example, let's assume the semestral grade is a weighted average of:
    # Final term grade and midterm grade, with final term having a 60% weight and midterm 40%.
    midterm_grade = float(request.form['midterm_grade'])  # Ensure you collect midterm grade from the form

    # Calculate the semestral grade
    semestral_grade = (final_term_grade * 0.6) + (midterm_grade * 0.4)
    
    # Render the semestral grade result page with the calculated semestral grade
    return render_template('semestral_grade_result.html', semestral_grade=semestral_grade)

@app.route('/semestral-grade/<course_code>/<block_name>')
def semestral_grade(course_code, block_name):
    # Fetch the course details by course_code
    course = Course.query.filter_by(course_code=course_code).first_or_404()
    
    # Fetch students for the given course_code and block_name
    students = Student.query.filter_by(course_code=course_code, block_name=block_name).all()
    
    # Determine which template to render based on course type for semestral grade calculation
    if course.course_type == "Laboratory":
        template = 'semestral-grade-laboratory.html'
    elif course.course_type == "Lecture":
        template = 'semestral-grade-lecture.html'
    elif course.course_type == "Lecture/Laboratory":
        template = 'semestral-grade-lecture-lab.html'
    else:
        template = 'semestral-grade-laboratory.html'  # Default to laboratory if undefined

    # Render the appropriate template with the students' data
    return render_template(template, course=course, block_name=block_name, students=students)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)