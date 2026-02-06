from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from functools import wraps
import uuid

app = Flask(__name__)
app.secret_key = 'super_secret_dev_key_change_me_in_prod'  # Required for sessions

# -------------------------------------------------------------------
#  IN-MEMORY DATA STRUCTURES (DATABASE REPLACEMENTS)
# -------------------------------------------------------------------

# USERS: username -> { 'id': str, 'password': str, 'role': str, 'name': str }
USERS = {}

# SUBJECTS: id -> { 'id': str, 'name': str, 'teacher_id': str (username) }
SUBJECTS = {}

# MARKS: student_username -> { subject_id: int }
MARKS = {}

# GLOBAL SETTINGS
CONFIG = {
    'results_published': False
}

# -------------------------------------------------------------------
#  HELPER FUNCTIONS & DECORATORS
# -------------------------------------------------------------------

def populate_dummy_data():
    """Initializes the system with some default data for testing."""
    # Create Admin
    USERS['admin'] = {'id': 'admin', 'username': 'admin', 'password': '123', 'role': 'admin', 'name': 'System Administrator'}
    
    # Create Teachers
    USERS['t1'] = {'id': 't1', 'username': 't1', 'password': '123', 'role': 'teacher', 'name': 'Alice Teacher'}
    USERS['t2'] = {'id': 't2', 'username': 't2', 'password': '123', 'role': 'teacher', 'name': 'Bob Teacher'}
    
    # Create Students
    USERS['s1'] = {'id': 's1', 'username': 's1', 'password': '123', 'role': 'student', 'name': 'John Student'}
    USERS['s2'] = {'id': 's2', 'username': 's2', 'password': '123', 'role': 'student', 'name': 'Jane Student'}
    
    # Create Subjects
    sub1_id = str(uuid.uuid4())[:8]
    SUBJECTS[sub1_id] = {'id': sub1_id, 'name': 'Mathematics', 'teacher_id': 't1'}
    
    sub2_id = str(uuid.uuid4())[:8]
    SUBJECTS[sub2_id] = {'id': sub2_id, 'name': 'Science', 'teacher_id': 't2'}

    # Initial Marks (for demo)
    # Student 1 Math
    MARKS['s1'] = {} 
    
    print("--- Dummy Data Loaded ---")
    print("Admin:   admin / 123")
    print("Teacher: t1 / 123")
    print("Student: s1 / 123")

# Run population once on import
populate_dummy_data()

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
                return redirect(url_for('dashboard', role=session.get('user', {}).get('role')))
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
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = USERS.get(username)
        
        if user and user['password'] == password:
            session['user'] = user
            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password.", "error")
            
    return render_template('login.html')

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
    # Gather stats
    teacher_count = len([u for u in USERS.values() if u['role'] == 'teacher'])
    student_count = len([u for u in USERS.values() if u['role'] == 'student'])
    subject_count = len(SUBJECTS)
    
    all_results = []
    # Compile a big list of results for Admin view
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
            'id': username, # using username as ID for simplicity
            'username': username,
            'password': password,
            'role': role,
            'name': name
        }
        flash(f"User '{username}' created successfully.", "success")
    else:
        flash("Invalid user data.", "error")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/toggle_results')
@login_required
@role_required('admin')
def toggle_results():
    CONFIG['results_published'] = not CONFIG['results_published']
    status = "PUBLISHED" if CONFIG['results_published'] else "UNPUBLISHED"
    flash(f"Results are now {status}.", "info")
    return redirect(url_for('admin_dashboard'))

# ------------------- TEACHER ROUTES -------------------

@app.route('/teacher')
@login_required
@role_required('teacher')
def teacher_dashboard():
    my_username = session['user']['username']
    
    # Get subjects assigned to this teacher
    my_subjects = [s for s in SUBJECTS.values() if s['teacher_id'] == my_username]
    
    # Get list of ALL students for dropdowns
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
    
    # Validation: Ensure this teacher owns the subject
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

    # Save marks
    if student_username not in MARKS:
        MARKS[student_username] = {}
        
    MARKS[student_username][subject_id] = val
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
    # Re-use logic or just render a print-friendly version
    return student_dashboard() # The dashboard template will have a print view

# -------------------------------------------------------------------

if __name__ == '__main__':
    app.run(debug=True, port=5000)
