import json
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from functools import wraps
import uuid
import os
from flask_mysqldb import MySQL

app = Flask(__name__)
app.secret_key = 'super_secret_dev_key_change_me_in_prod'

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'om@2005'  # Replace with your MySQL root password
app.config['MYSQL_DB'] = 'result_management_system'

mysql = MySQL(app)

# -------------------------------------------------------------------
#  DATABASE INITIALIZATION
# -------------------------------------------------------------------

def init_db():
    with app.app_context():
        cur = mysql.connection.cursor()
        
        # Students: roll_number (PK), full_name, password, semester
        cur.execute('''
            CREATE TABLE IF NOT EXISTS students (
                roll_number VARCHAR(20) PRIMARY KEY,
                full_name VARCHAR(100) NOT NULL,
                password VARCHAR(100) NOT NULL,
                semester VARCHAR(20) NOT NULL
            )
        ''')
        
        # Teachers: email (PK), name, password, subject_of_teaching
        cur.execute('''
            CREATE TABLE IF NOT EXISTS teachers (
                email VARCHAR(100) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                password VARCHAR(100) NOT NULL,
                subject_of_teaching VARCHAR(100) NOT NULL
            )
        ''')
        
        # Admin: email (PK), name, password
        cur.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                email VARCHAR(100) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                password VARCHAR(100) NOT NULL
            )
        ''')
        
        # Marks: roll_number, subject_name, internal, external, remarks
        cur.execute('''
            CREATE TABLE IF NOT EXISTS marks (
                roll_number VARCHAR(20),
                subject_name VARCHAR(100),
                internal INT NOT NULL DEFAULT 0,
                external INT NOT NULL DEFAULT 0,
                remarks VARCHAR(255) DEFAULT '',
                PRIMARY KEY (roll_number, subject_name),
                FOREIGN KEY (roll_number) REFERENCES students(roll_number) ON DELETE CASCADE
            )
        ''')
        
        # Config
        cur.execute('''
            CREATE TABLE IF NOT EXISTS config (
                key_name VARCHAR(50) PRIMARY KEY,
                value VARCHAR(50) NOT NULL
            )
        ''')
        
        # Seed Default Admin
        cur.execute("SELECT * FROM admins WHERE email = 'admin@edugrade.com'")
        if not cur.fetchone():
            cur.execute("INSERT INTO admins (email, name, password) VALUES (%s, %s, %s)",
                        ('admin@edugrade.com', 'System Admin', '123'))
        
        # Seed Default Config
        cur.execute("SELECT * FROM config WHERE key_name = 'results_published'")
        if not cur.fetchone():
            cur.execute("INSERT INTO config (key_name, value) VALUES (%s, %s)",
                        ('results_published', 'False'))
            
        mysql.connection.commit()
        cur.close()

try:
    init_db()
except Exception as e:
    print(f"DB Error: {e}")

# -------------------------------------------------------------------
#  HELPER FUNCTIONS
# -------------------------------------------------------------------

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash("Session expired. Please login.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('user', {}).get('role') != role:
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
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('username') # Roll Number or Email
        password = request.form.get('password')
        role = request.form.get('role')
        
        cur = mysql.connection.cursor()
        user_info = None
        
        if role == 'student':
            cur.execute("SELECT * FROM students WHERE roll_number = %s AND password = %s", (identifier, password))
            res = cur.fetchone()
            if res: user_info = {'id': res[0], 'name': res[1], 'role': 'student', 'semester': res[3]}
        elif role == 'teacher':
            cur.execute("SELECT * FROM teachers WHERE email = %s AND password = %s", (identifier, password))
            res = cur.fetchone()
            if res: user_info = {'id': res[0], 'name': res[1], 'role': 'teacher', 'subject': res[3]}
        elif role == 'admin':
            cur.execute("SELECT * FROM admins WHERE email = %s AND password = %s", (identifier, password))
            res = cur.fetchone()
            if res: user_info = {'id': res[0], 'name': res[1], 'role': 'admin'}
            
        cur.close()
        if user_info:
            session['user'] = user_info
            flash(f"Welcome, {user_info['name']}!", "success")
            return redirect(url_for('dashboard'))
        flash("Invalid credentials.", "error")
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        role = request.form.get('role')
        name = request.form.get('name')
        password = request.form.get('password')
        cur = mysql.connection.cursor()
        try:
            if role == 'student':
                roll = request.form.get('roll_number')
                sem = request.form.get('semester')
                cur.execute("INSERT INTO students VALUES (%s, %s, %s, %s)", (roll, name, password, sem))
            else:
                email = request.form.get('email')
                subject = request.form.get('subject_of_teaching')
                cur.execute("INSERT INTO teachers VALUES (%s, %s, %s, %s)", (email, name, password, subject))
            mysql.connection.commit()
            flash("Signup successful!", "success")
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Error: {e}", "error")
        finally: cur.close()
    return render_template('signup.html')

@app.route('/dashboard')
@login_required
def dashboard():
    role = session['user']['role']
    if role == 'admin': return redirect(url_for('admin_dashboard'))
    if role == 'teacher': return redirect(url_for('teacher_dashboard'))
    return redirect(url_for('student_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# --- ADMIN ---
@app.route('/admin')
@login_required
@role_required('admin')
def admin_dashboard():
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) FROM students")
    s_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM teachers")
    t_count = cur.fetchone()[0]
    cur.execute("SELECT value FROM config WHERE key_name = 'results_published'")
    pub = cur.fetchone()[0] == 'True'
    
    cur.execute("SELECT s.full_name, m.subject_name, (m.internal + m.external) as total_marks FROM marks m JOIN students s ON m.roll_number = s.roll_number")
    results = []
    for r in cur.fetchall():
        g, st = get_grade(r[2])
        results.append({'student': r[0], 'subject': r[1], 'marks': r[2], 'grade': g, 'status': st})
        
    cur.close()
    return render_template('admin_dashboard.html', stats={'students': s_count, 'teachers': t_count}, config={'results_published': pub}, all_results=results)

@app.route('/admin/toggle_results')
@login_required
@role_required('admin')
def toggle_results():
    cur = mysql.connection.cursor()
    cur.execute("SELECT value FROM config WHERE key_name = 'results_published'")
    new_v = 'True' if cur.fetchone()[0] == 'False' else 'False'
    cur.execute("UPDATE config SET value = %s WHERE key_name = 'results_published'", (new_v,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('admin_dashboard'))

# --- TEACHER ---
@app.route('/teacher')
@login_required
@role_required('teacher')
def teacher_dashboard():
    sub = session['user']['subject']
    cur = mysql.connection.cursor()
    # Only fetch students who have marks in this subject (as per design spec, "Add Student" creates the entry)
    cur.execute('''
        SELECT s.roll_number, s.full_name, m.internal, m.external, m.remarks 
        FROM marks m JOIN students s ON m.roll_number = s.roll_number 
        WHERE m.subject_name = %s
    ''', (sub,))
    stus = []
    for r in cur.fetchall():
        stus.append({'id': r[0], 'roll': r[0], 'name': r[1], 'internal': r[2], 'external': r[3], 'remarks': r[4] or ''})
    cur.close()
    
    teacher_name = session['user']['name'] or 'Teacher'
    tj = json.dumps({
        'name': teacher_name,
        'initials': ''.join([n[0] for n in teacher_name.split()][:2]).upper() if teacher_name else 'T',
        'subject': sub,
        'code': sub.upper()[:4] + '-101',
        'semester': 'All Semesters',
        'dept': 'Faculty Dept.'
    })
    return render_template('teacher_dashboard.html', teacher_json=tj, students_json=json.dumps(stus))

@app.route('/teacher/api/save_marks', methods=['POST'])
@login_required
@role_required('teacher')
def api_save_marks():
    data = request.json
    roll = data.get('roll')
    name = data.get('name')
    internal = data.get('internal', 0)
    external = data.get('external', 0)
    remarks = data.get('remarks', '')
    sub = session['user']['subject']
    
    cur = mysql.connection.cursor()
    # Check if student exists, else insert
    cur.execute("SELECT * FROM students WHERE roll_number = %s", (roll,))
    if not cur.fetchone():
        cur.execute("INSERT INTO students (roll_number, full_name, password, semester) VALUES (%s, %s, %s, %s)",
                    (roll, name, roll, 'I'))
                    
    cur.execute("REPLACE INTO marks (roll_number, subject_name, internal, external, remarks) VALUES (%s, %s, %s, %s, %s)", 
                (roll, sub, internal, external, remarks))
    mysql.connection.commit()
    cur.close()
    return {"status": "success"}

@app.route('/teacher/api/delete_marks', methods=['POST'])
@login_required
@role_required('teacher')
def api_delete_marks():
    roll = request.json.get('roll')
    sub = session['user']['subject']
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM marks WHERE roll_number = %s AND subject_name = %s", (roll, sub))
    mysql.connection.commit()
    cur.close()
    return {"status": "success"}

# --- STUDENT ---
@app.route('/student')
@login_required
@role_required('student')
def student_dashboard():
    cur = mysql.connection.cursor()
    cur.execute("SELECT value FROM config WHERE key_name = 'results_published'")
    if cur.fetchone()[0] == 'False': 
        cur.close()
        return render_template('student_dashboard.html', published=False)
    
    roll = session['user']['id']
    cur.execute("SELECT subject_name, internal, external, (internal + external) as total_marks, remarks FROM marks WHERE roll_number = %s", (roll,))
    rows = cur.fetchall()
    report = []
    tot, mx = 0, 0
    for r in rows:
        g, s = get_grade(r[3])
        report.append({'subject': r[0], 'internal': r[1], 'external': r[2], 'score': r[3], 'remarks': r[4], 'grade': g, 'status': s})
        tot += r[3]; mx += 100
    
    perc = round((tot/mx)*100, 2) if mx > 0 else 0
    fg, fs = get_grade(perc)
    cur.close()
    return render_template('student_dashboard.html', published=True, report_card=report, total_marks=tot, max_marks=mx, percentage=perc, final_grade=fg, final_status=fs)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

