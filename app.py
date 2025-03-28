from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import pytz

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Admin credentials (in a real application, these should be stored securely)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'teacher', or 'student'
    submissions = db.relationship('Submission', backref='student', lazy=True)

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)
    questions = db.relationship('Question', backref='quiz', lazy=True)
    submissions = db.relationship('Submission', backref='quiz', lazy=True)
    teacher = db.relationship('User', backref='quizzes')

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    question_text = db.Column(db.String(500), nullable=False)
    option_a = db.Column(db.String(200), nullable=False)
    option_b = db.Column(db.String(200), nullable=False)
    option_c = db.Column(db.String(200), nullable=False)
    option_d = db.Column(db.String(200), nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    submission_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            admin_user = User.query.filter_by(username=username).first()
            if not admin_user:
                admin_user = User(username=username, password=password, role='admin')
                db.session.add(admin_user)
                db.session.commit()
            login_user(admin_user)
            return redirect(url_for('admin_dashboard'))
        
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            if user.role == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    users = User.query.filter(User.role != 'admin').all()
    return render_template('admin_dashboard.html', users=users)

@app.route('/admin/add_user', methods=['POST'])
@login_required
def add_user():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')
    
    if User.query.filter_by(username=username).first():
        flash('Username already exists.')
        return redirect(url_for('admin_dashboard'))
    
    new_user = User(username=username, password=password, role=role)
    db.session.add(new_user)
    db.session.commit()
    flash('User added successfully.')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_user/<int:user_id>')
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        flash('Cannot delete admin user.')
        return redirect(url_for('admin_dashboard'))
    
    # If the user is a teacher, delete their quizzes first
    if user.role == 'teacher':
        # Get all quizzes created by this teacher
        quizzes = Quiz.query.filter_by(teacher_id=user.id).all()
        for quiz in quizzes:
            # Delete all questions associated with the quiz
            Question.query.filter_by(quiz_id=quiz.id).delete()
            # Delete all submissions associated with the quiz
            Submission.query.filter_by(quiz_id=quiz.id).delete()
            # Delete the quiz
            db.session.delete(quiz)
    
    # If the user is a student, delete their submissions
    if user.role == 'student':
        Submission.query.filter_by(student_id=user.id).delete()
    
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully.')
    return redirect(url_for('admin_dashboard'))

@app.route('/teacher/dashboard')
@login_required
def teacher_dashboard():
    if current_user.role != 'teacher':
        flash('Access denied. Teacher privileges required.')
        return redirect(url_for('index'))
    quizzes = Quiz.query.filter_by(teacher_id=current_user.id).all()
    return render_template('teacher_dashboard.html', quizzes=quizzes)

@app.route('/teacher/create_quiz', methods=['GET', 'POST'])
@login_required
def create_quiz():
    if current_user.role != 'teacher':
        flash('Access denied. Teacher privileges required.')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        subject = request.form.get('subject')
        deadline = datetime.strptime(request.form.get('deadline'), '%Y-%m-%dT%H:%M')
        deadline = pytz.timezone('Asia/Kolkata').localize(deadline)
        
        quiz = Quiz(subject=subject, teacher_id=current_user.id, deadline=deadline)
        db.session.add(quiz)
        db.session.commit()
        
        # Add 10 questions
        for i in range(10):
            question = Question(
                quiz_id=quiz.id,
                question_text=request.form.get(f'question_{i+1}'),
                option_a=request.form.get(f'option_a_{i+1}'),
                option_b=request.form.get(f'option_b_{i+1}'),
                option_c=request.form.get(f'option_c_{i+1}'),
                option_d=request.form.get(f'option_d_{i+1}'),
                correct_answer=request.form.get(f'correct_answer_{i+1}')
            )
            db.session.add(question)
        
        db.session.commit()
        flash('Quiz created successfully.')
        return redirect(url_for('teacher_dashboard'))
    
    return render_template('create_quiz.html')

@app.route('/teacher/quiz/<int:quiz_id>/results')
@login_required
def quiz_results(quiz_id):
    if current_user.role != 'teacher':
        flash('Access denied. Teacher privileges required.')
        return redirect(url_for('index'))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.teacher_id != current_user.id:
        flash('Access denied. This quiz belongs to another teacher.')
        return redirect(url_for('teacher_dashboard'))
    
    submissions = Submission.query.filter_by(quiz_id=quiz_id).all()
    total_students = len(submissions)
    average_score = sum(sub.score for sub in submissions) / total_students if total_students > 0 else 0
    
    return render_template('quiz_results.html', quiz=quiz, submissions=submissions, 
                         total_students=total_students, average_score=average_score)

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        flash('Access denied. Student privileges required.')
        return redirect(url_for('index'))
    
    # Get all quizzes that haven't passed their deadline
    current_time = datetime.now(pytz.timezone('Asia/Kolkata'))
    upcoming_quizzes = Quiz.query.filter(Quiz.deadline > current_time).all()
    
    # Ensure all quiz deadlines are timezone-aware
    for quiz in upcoming_quizzes:
        if quiz.deadline.tzinfo is None:
            quiz.deadline = pytz.timezone('Asia/Kolkata').localize(quiz.deadline)
    
    # Get all submissions by the current student
    submissions = Submission.query.filter_by(student_id=current_user.id).all()
    
    return render_template('student_dashboard.html', upcoming_quizzes=upcoming_quizzes, submissions=submissions)

@app.route('/student/quiz/<int:quiz_id>')
@login_required
def take_quiz(quiz_id):
    if current_user.role != 'student':
        flash('Access denied. Student privileges required.')
        return redirect(url_for('index'))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    current_time = datetime.now(pytz.timezone('Asia/Kolkata'))
    
    # Ensure quiz.deadline is timezone-aware
    if quiz.deadline.tzinfo is None:
        quiz.deadline = pytz.timezone('Asia/Kolkata').localize(quiz.deadline)
    
    if current_time > quiz.deadline:
        flash('This quiz has passed its deadline.')
        return redirect(url_for('student_dashboard'))
    
    # Check if student has already submitted
    existing_submission = Submission.query.filter_by(
        quiz_id=quiz_id, student_id=current_user.id
    ).first()
    
    if existing_submission:
        flash('You have already submitted this quiz.')
        return redirect(url_for('student_dashboard'))
    
    return render_template('take_quiz.html', quiz=quiz)

@app.route('/student/quiz/<int:quiz_id>/submit', methods=['POST'])
@login_required
def submit_quiz(quiz_id):
    if current_user.role != 'student':
        flash('Access denied. Student privileges required.')
        return redirect(url_for('index'))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    current_time = datetime.now(pytz.timezone('Asia/Kolkata'))
    
    # Ensure quiz.deadline is timezone-aware
    if quiz.deadline.tzinfo is None:
        quiz.deadline = pytz.timezone('Asia/Kolkata').localize(quiz.deadline)
    
    if current_time > quiz.deadline:
        flash('This quiz has passed its deadline.')
        return redirect(url_for('student_dashboard'))
    
    # Check if student has already submitted
    existing_submission = Submission.query.filter_by(
        quiz_id=quiz_id, student_id=current_user.id
    ).first()
    
    if existing_submission:
        flash('You have already submitted this quiz.')
        return redirect(url_for('student_dashboard'))
    
    # Calculate score
    score = 0
    for question in quiz.questions:
        answer = request.form.get(f'answer_{question.id}')
        if answer == question.correct_answer:
            score += 1
    
    # Create submission
    submission = Submission(
        quiz_id=quiz_id,
        student_id=current_user.id,
        score=score
    )
    db.session.add(submission)
    db.session.commit()
    
    flash(f'Quiz submitted successfully. Your score: {score}/10')
    return redirect(url_for('student_dashboard'))

# Create database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True) 