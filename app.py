from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from functools import wraps
import uuid
import os
import csv

app = Flask(__name__)
app.secret_key = 'super_secret_dev_key_change_me_in_prod'

# -------------------------------------------------------------------
#  DATA PERSISTENCE (CSV)
# -------------------------------------------------------------------

DATA_DIR = 'data'
FILES = {
    'users': os.path.join(DATA_DIR, 'users.csv'),
    'subjects': os.path.join(DATA_DIR, 'subjects.csv'),
    'marks': os.path.join(DATA_DIR, 'marks.csv'),
    'config': os.path.join(DATA_DIR, 'config.csv')
}

# Global Runtime Store (Loaded from CSV)
USERS = {}
SUBJECTS = {}
MARKS = {}
CONFIG = {'results_published': False}

def init_db():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    # Initialize files with headers if they don't exist
    if not os.path.exists(FILES['users']):
        with open(FILES['users'], 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['username', 'password', 'role', 'name'])
            # Default Admin
            writer.writerow(['admin', '123', 'admin', 'System Administrator'])

    if not os.path.exists(FILES['subjects']):
        with open(FILES['subjects'], 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name', 'teacher_id'])

    if not os.path.exists(FILES['marks']):
        with open(FILES['marks'], 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['student_username', 'subject_id', 'marks'])

    if not os.path.exists(FILES['config']):
        with open(FILES['config'], 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['key', 'value'])
            writer.writerow(['results_published', 'False'])

def load_data():
    global USERS, SUBJECTS, MARKS, CONFIG
    USERS = {}
    SUBJECTS = {}
    MARKS = {}

    # Load Users
    if os.path.exists(FILES['users']):
        with open(FILES['users'], 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                USERS[row['username']] = row

    # Load Subjects
    if os.path.exists(FILES['subjects']):
        with open(FILES['subjects'], 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                SUBJECTS[row['id']] = row

    # Load Marks
    if os.path.exists(FILES['marks']):
        with open(FILES['marks'], 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                stu = row['student_username']
                sub = row['subject_id']
                score = int(row['marks'])
                if stu not in MARKS: MARKS[stu] = {}
                MARKS[stu][sub] = score

    # Load Config
    if os.path.exists(FILES['config']):
        with open(FILES['config'], 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['key'] == 'results_published':
                    CONFIG['results_published'] = (row['value'] == 'True')

def save_users():
    with open(FILES['users'], 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['username', 'password', 'role', 'name'])
        for u in USERS.values():
            writer.writerow([u['username'], u['password'], u['role'], u['name']])

def save_subjects():
    with open(FILES['subjects'], 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'name', 'teacher_id'])
        for s in SUBJECTS.values():
            writer.writerow([s['id'], s['name'], s['teacher_id']])

def save_marks():
    with open(FILES['marks'], 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['student_username', 'subject_id', 'marks'])
        for stu_user, subjects in MARKS.items():
            for sub_id, score in subjects.items():
                writer.writerow([stu_user, sub_id, score])

def save_config():
    with open(FILES['config'], 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['key', 'value'])
        writer.writerow(['results_published', str(CONFIG['results_published'])])

# Initialize and Load
init_db()
load_data()

# -------------------------------------------------------------------
#  HELPER FUNCTIONS & DECORATORS
# -------------------------------------------------------------------

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash("Please log in to access this page.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user' not in session or session['user'].get('role') != required_role:
                flash("Unauthorized access.", "error")
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_grade(marks):
    if marks >= 90: return 'A', 'pass'
    if marks >= 75: return 'B', 'pass'
    if marks >= 60: return 'C', 'pass'
    if marks >= 40: return 'D', 'pass'
    return 'F', 'fail'

# -------------------------------------------------------------------
#  ROUTES
# -------------------------------------------------------------------

@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role') # Passed from hidden field in tabs

        user = USERS.get(username)
        
        if user and user['password'] == password:
            if role and user['role'] != role:
                flash(f"Invalid role. Please login as {user['role']}.", "error")
                return redirect(url_for('login'))
            
            session['user'] = user
            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password.", "error")
            
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'student') # Default to student if not specified

        if username in USERS:
            flash("Username already taken.", "error")
        else:
            new_user = {
                'username': username,
                'password': password,
                'role': role,
                'name': name
            }
            USERS[username] = new_user
            save_users() # Persist
            flash("Account created! Please login.", "success")
            return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    role = session['user']['role']
    if role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif role == 'teacher':
        return redirect(url_for('teacher_dashboard'))
    elif role == 'student':
        return redirect(url_for('student_dashboard'))
    return redirect(url_for('logout'))

# ------------------- ADMIN ROUTES -------------------

@app.route('/admin')
@login_required
@role_required('admin')
def admin_dashboard():
    teacher_count = len([u for u in USERS.values() if u['role'] == 'teacher'])
    student_count = len([u for u in USERS.values() if u['role'] == 'student'])
    subject_count = len(SUBJECTS)
    
    all_results = []
    for s_username, s_marks in MARKS.items():
        stu = USERS.get(s_username)
        if not stu: continue
        
        for sub_id, score in s_marks.items():
            sub = SUBJECTS.get(sub_id)
            if sub:
                grade, status = get_grade(score)
                all_results.append({
                    'student': stu['name'],
                    'subject': sub['name'],
                    'marks': score,
                    'grade': grade,
                    'status': status
                })

    return render_template('admin_dashboard.html', 
                           users=USERS, 
                           subjects=SUBJECTS,
                           config=CONFIG,
                           stats={'teachers': teacher_count, 'students': student_count, 'subjects': subject_count},
                           all_results=all_results)

@app.route('/admin/add_subject', methods=['POST'])
@login_required
@role_required('admin')
def add_subject():
    name = request.form.get('name')
    teacher_username = request.form.get('teacher_id')
    
    if name and teacher_username:
        new_id = str(uuid.uuid4())[:8]
        SUBJECTS[new_id] = {
            'id': new_id,
            'name': name,
            'teacher_id': teacher_username
        }
        save_subjects()
        flash(f"Subject '{name}' created successfully.", "success")
    else:
        flash("Missing info for creating subject.", "error")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_user', methods=['POST'])
@login_required
@role_required('admin')
def add_user():
    username = request.form.get('username')
    password = request.form.get('password')
    name = request.form.get('name')
    role = request.form.get('role')
    
    if username in USERS:
        flash("Username already exists.", "error")
    elif username and password and role in ['student', 'teacher']:
        USERS[username] = {
            'username': username,
            'password': password,
            'role': role,
            'name': name
        }
        save_users()
        flash(f"User '{username}' created successfully.", "success")
    else:
        flash("Invalid user data.", "error")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/toggle_results')
@login_required
@role_required('admin')
def toggle_results():
    CONFIG['results_published'] = not CONFIG['results_published']
    save_config()
    status = "PUBLISHED" if CONFIG['results_published'] else "UNPUBLISHED"
    flash(f"Results are now {status}.", "info")
    return redirect(url_for('admin_dashboard'))

# ------------------- TEACHER ROUTES -------------------

@app.route('/teacher')
@login_required
@role_required('teacher')
def teacher_dashboard():
    my_username = session['user']['username']
    my_subjects = [s for s in SUBJECTS.values() if s['teacher_id'] == my_username]
    all_students = [u for u in USERS.values() if u['role'] == 'student']
    
    return render_template('teacher_dashboard.html', 
                           subjects=my_subjects,
                           students=all_students)

@app.route('/teacher/update_marks', methods=['POST'])
@login_required
@role_required('teacher')
def update_marks():
    student_username = request.form.get('student_id')
    subject_id = request.form.get('subject_id')
    marks_val = request.form.get('marks')
    
    subject = SUBJECTS.get(subject_id)
    if not subject or subject['teacher_id'] != session['user']['username']:
        flash("You are not authorized to grade this subject.", "error")
        return redirect(url_for('teacher_dashboard'))

    try:
        val = int(marks_val)
        if not (0 <= val <= 100): raise ValueError()
    except:
        flash("Marks must be a number between 0 and 100.", "error")
        return redirect(url_for('teacher_dashboard'))
        
    if student_username not in USERS:
        flash("Student not found.", "error")
        return redirect(url_for('teacher_dashboard'))

    if student_username not in MARKS:
        MARKS[student_username] = {}
        
    MARKS[student_username][subject_id] = val
    save_marks()
    flash(f"Updated marks for {USERS[student_username]['name']}.", "success")
    return redirect(url_for('teacher_dashboard'))

# ------------------- STUDENT ROUTES -------------------

@app.route('/student')
@login_required
@role_required('student')
def student_dashboard():
    if not CONFIG['results_published']:
        return render_template('student_dashboard.html', published=False)
        
    username = session['user']['username']
    student_marks = MARKS.get(username, {})
    
    report_card = []
    total_marks = 0
    max_marks = 0
    
    for sub_id, score in student_marks.items():
        subject = SUBJECTS.get(sub_id)
        if subject:
            grade, status = get_grade(score)
            report_card.append({
                'subject': subject['name'],
                'score': score,
                'grade': grade,
                'status': status
            })
            total_marks += score
            max_marks += 100
            
    percentage = 0
    if max_marks > 0:
        percentage = round((total_marks / max_marks) * 100, 2)
        
    final_grade, final_status = get_grade(percentage)
    
    return render_template('student_dashboard.html', 
                           published=True,
                           report_card=report_card,
                           total_marks=total_marks,
                           max_marks=max_marks,
                           percentage=percentage,
                           final_grade=final_grade,
                           final_status=final_status)

@app.route('/student/download')
@login_required
@role_required('student')
def download_result():
    return student_dashboard()

if __name__ == '__main__':
    app.run(debug=True, port=5000)

