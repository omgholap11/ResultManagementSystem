# EduGrade — Result Management System

EduGrade is a professional, high-performance Result Management System built with **Python Flask** and a sleek, multi-role dashboard architecture. It features a robust **MySQL** backend for data persistence and a modern, responsive UI designed with vanilla HTML and CSS.

## 🚀 Key Features

-   **Multi-Role Authentication**: Dedicated portals for **Admins**, **Teachers**, and **Students**.
-   **Teacher Dashboard**:
    -   Securely add, update, and delete student marks using async `fetch` APIs.
    -   Automatic grade calculation (S, A, B, C, F).
    -   Export results to CSV for offline analysis.
-   **Student Dashboard**:
    -   Modern, tabular view of internal and external marks.
    -   Overall performance summaries with dynamic donut charts.
    -   Printable marksheet view.
-   **Admin Control**:
    -   Toggle result visibility (Publish/Unpublish) for the entire student body.
    -   Centralized student and teacher management.

## 📂 Project Structure

```text
Result_Management_System/
├── app.py                  # Flask Backend & Database Initialization
├── requirements.txt        # Project Dependencies
├── README.md               # Documentation
├── static/
│   ├── css/
│   │   ├── style.css       # Global & Landing Styles
│   │   ├── teacher.css     # Dedicated Teacher Dashboard UI
│   │   └── student.css     # Dedicated Student Dashboard UI
│   └── js/
│       └── main.js         # Core Frontend Logic
└── templates/
    ├── base.html           # Shared Navigation & Layout
    ├── landing.html        # Modern Hero Landing Page
    ├── login.html          # Multi-tab Authentication Portal
    ├── signup.html         # User Registration
    ├── admin_dashboard.html# Global Control Panel
    ├── teacher_dashboard.html # Faculty Mark Management
    └── student_dashboard.html # Personal Academic Results
```

## 🛠️ Setup & Installation

### 1. Prerequisites
-   Python 3.8+
-   MySQL Server installed and running.

### 2. Database Setup
1.  Log into your MySQL terminal:
    ```sql
    CREATE DATABASE result_management_system;
    ```

### 3. Application Configuration
Open `app.py` and update the MySQL configuration with your local credentials:
```python
# app.py
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'your_username'
app.config['MYSQL_PASSWORD'] = 'your_password' # Use your actual MySQL password
app.config['MYSQL_DB'] = 'result_management_system'
```
> **Note:** The tables (`students`, `teachers`, `admins`, `marks`, `config`) will be automatically created the first time you run the application.

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Run the Application
```bash
python app.py
```
Access the system at: `http://localhost:5000`

## 🔑 Default Credentials
-   **Admin**: `admin@edugrade.com` | `123`
-   **Demo Teacher**: (Create via Signup)
-   **Demo Student**: (Create via Signup)

## 🎨 UI Design
The system uses a premium "EduGrade" design language featuring:
-   **Dark/Light Mode** support.
-   **Dynamic Micro-animations** for interactive elements.
-   **Custom Typography**: Syne & DM Sans fonts.
-   **Glassmorphism** and soft gradients for a modern look.
