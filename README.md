# Result Management System

A simple, clean, and professional Result Management System built with Python Flask and vanilla HTML/CSS/JS.
This system uses **in-memory storage**, meaning all data is reset when the application restarts.

## 📂 Project Structure

```
Result_Management_System/
├── app.py                  # Main Application (Backend Logic)
├── requirements.txt        # Python Dependencies
├── README.md               # Project Instructions
├── static/
│   ├── css/
│   │   └── style.css       # Custom Global Styles
│   └── js/
│       └── main.js         # Frontend Interactivity
└── templates/
    ├── base.html           # Base Layout (Navbar, Flash Messages)
    ├── login.html          # Login Page
    ├── admin_dashboard.html# Admin Control Panel
    ├── teacher_dashboard.html # Teacher Marks Entry
    └── student_dashboard.html # Student Result View
```

## 🚀 How to Run

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the Application:**
    ```bash
    python app.py
    ```

3.  **Access in Browser:**
    Open [http://localhost:5000](http://localhost:5000)

## 🔑 Demo Credentials

The system comes pre-loaded with the following users:

| Role | Username | Password |
|------|----------|----------|
| **Admin** | `admin` | `123` |
| **Teacher** | `t1` | `123` |
| **Teacher** | `t2` | `123` |
| **Student** | `s1` | `123` |
| **Student** | `s2` | `123` |

## 📝 Features & Workflow

1.  **Admin (`admin`):**
    - Create new Subjects and assign them to Teachers.
    - Create new Users (Students/Teachers).
    - **Publish/Unpublish Results:** Students cannot see their grades until results are published.

2.  **Teacher (`t1`):**
    - View assigned subjects.
    - Enter/Update marks for students.

3.  **Student (`s1`):**
    - View their report card (if published).
    - Download/Print their result.
