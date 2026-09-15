from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3

app = Flask(__name__)
app.secret_key = "hospital_secret_key"

def get_db():
    conn = sqlite3.connect("hospital.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialization TEXT NOT NULL,
            available_day TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            gender TEXT,
            phone TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT NOT NULL,
            doctor_name TEXT NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            reason TEXT
        )
    """)

    try:
        conn.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ("doctor1", "doctor123", "doctor")
        )
    except sqlite3.IntegrityError:
        pass

    try:
        conn.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ("patient1", "patient123", "patient")
        )
    except sqlite3.IntegrityError:
        pass

    if conn.execute("SELECT COUNT(*) FROM doctors").fetchone()[0] == 0:
        conn.execute(
            "INSERT INTO doctors (name, specialization, available_day) VALUES (?, ?, ?)",
            ("Dr. Ravi Kumar", "Cardiologist", "Monday - Friday")
        )
        conn.execute(
            "INSERT INTO doctors (name, specialization, available_day) VALUES (?, ?, ?)",
            ("Dr. Priya Sharma", "Dermatologist", "Monday - Saturday")
        )
        conn.execute(
            "INSERT INTO doctors (name, specialization, available_day) VALUES (?, ?, ?)",
            ("Dr. Arjun Rao", "General Physician", "Monday - Friday")
        )

    if conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0] == 0:
        conn.execute(
            "INSERT INTO patients (name, age, gender, phone) VALUES (?, ?, ?, ?)",
            ("Harshita", 22, "Female", "9876543210")
        )

    conn.commit()
    conn.close()

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]

        conn = get_db()
        user = conn.execute("""
            SELECT * FROM users
            WHERE username = ? AND password = ? AND role = ?
        """, (username, password, role)).fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            if role == "doctor":
                return redirect(url_for("doctor_dashboard"))
            return redirect(url_for("patient_dashboard"))

        flash("Invalid username, password or role.")

    return render_template("login.html")

@app.route("/doctor_dashboard")
def doctor_dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "doctor":
        return redirect(url_for("patient_dashboard"))

    conn = get_db()
    doctors = conn.execute("SELECT * FROM doctors").fetchall()
    appointments = conn.execute("SELECT * FROM appointments").fetchall()
    conn.close()

    return render_template(
        "doctor_dashboard.html",
        doctors=doctors,
        appointments=appointments
    )

@app.route("/patient_dashboard")
def patient_dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "patient":
        return redirect(url_for("doctor_dashboard"))

    conn = get_db()
    doctors = conn.execute("SELECT * FROM doctors").fetchall()
    appointments = conn.execute(
        "SELECT * FROM appointments WHERE patient_name = ?",
        (session["username"],)
    ).fetchall()
    conn.close()

    return render_template(
        "patient_dashboard.html",
        doctors=doctors,
        appointments=appointments
    )

@app.route("/book_appointment", methods=["POST"])
def book_appointment():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "patient":
        return redirect(url_for("doctor_dashboard"))

    doctor_name = request.form["doctor_name"]
    appointment_date = request.form["appointment_date"]
    appointment_time = request.form["appointment_time"]
    reason = request.form["reason"]

    conn = get_db()
    conn.execute("""
        INSERT INTO appointments
        (patient_name, doctor_name, appointment_date, appointment_time, reason)
        VALUES (?, ?, ?, ?, ?)
    """, (
        session["username"],
        doctor_name,
        appointment_date,
        appointment_time,
        reason
    ))
    conn.commit()
    conn.close()

    flash("Appointment booked successfully!")
    return redirect(url_for("patient_dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
