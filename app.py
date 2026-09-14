

from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3


app = Flask(__name__)

app.secret_key = "jobportal_secret_key_2026"


# =========================
# DATABASE CONNECTION
# =========================

def get_db_connection():

    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row

    return conn


# =========================
# CREATE TABLES
# =========================

def create_tables():

    conn = get_db_connection()

    # USERS
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            email TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL,

            role TEXT NOT NULL DEFAULT 'user'
        )
    """)


    # JOBS
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            title TEXT NOT NULL,

            company TEXT NOT NULL,

            location TEXT NOT NULL,

            salary TEXT,

            description TEXT
        )
    """)


    # APPLICATIONS
    conn.execute("""
        CREATE TABLE IF NOT EXISTS applications (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            job_id INTEGER NOT NULL,

            status TEXT NOT NULL DEFAULT 'Applied',

            FOREIGN KEY (user_id)
                REFERENCES users(id),

            FOREIGN KEY (job_id)
                REFERENCES jobs(id)
        )
    """)


    conn.commit()
    conn.close()


# =========================
# HOME
# =========================

@app.route("/")
def home():

    conn = get_db_connection()

    jobs = conn.execute("""
        SELECT *
        FROM jobs
        ORDER BY id DESC
        LIMIT 3
    """).fetchall()

    conn.close()

    return render_template(
        "index.html",
        jobs=jobs
    )


# =========================
# JOBS
# =========================

@app.route("/jobs")
def jobs():

    conn = get_db_connection()

    jobs = conn.execute("""
        SELECT *
        FROM jobs
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "jobs.html",
        jobs=jobs
    )


# =========================
# REGISTER
# =========================

@app.route("/register", methods=["GET", "POST"])
def register():

    message = ""

    if request.method == "POST":

        name = request.form["name"]

        email = request.form["email"]

        password = request.form["password"]


        conn = get_db_connection()


        try:

            conn.execute(
                """
                INSERT INTO users
                (name, email, password)
                VALUES (?, ?, ?)
                """,

                (
                    name,
                    email,
                    password
                )
            )

            conn.commit()

            message = "Registration successful!"


        except sqlite3.IntegrityError:

            message = "Email already registered!"


        conn.close()


    return render_template(
        "register.html",
        message=message
    )


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    message = ""

    if request.method == "POST":

        email = request.form["email"]

        password = request.form["password"]


        conn = get_db_connection()


        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            AND password = ?
            """,

            (
                email,
                password
            )
        ).fetchone()


        conn.close()


        if user:

            session["user_id"] = user["id"]

            session["user_name"] = user["name"]

            session["user_role"] = user["role"]


            return redirect(
                url_for("dashboard")
            )


        else:

            message = "Invalid email or password!"


    return render_template(
        "login.html",
        message=message
    )


# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():

    # User must be logged in
    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    # Create Admin link only for admin
    admin_link = ""


    if session.get("user_role") == "admin":

        admin_link = """
            <br><br>

            <a href="/admin">
                Admin Dashboard
            </a>
        """


    return f"""
        <h1>
            Welcome, {session["user_name"]}!
        </h1>

        <p>
            You are successfully logged in.
        </p>

        <p>
            Role: {session["user_role"]}
        </p>

        <br>

        <a href="/jobs">
            Browse Jobs
        </a>

        {admin_link}

        <br><br>

        <a href="/logout">
            Logout
        </a>
    """


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )


# =========================
# ADMIN DASHBOARD
# =========================

@app.route("/admin")
def admin():

    # User must be logged in
    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    # Only admin can access
    if session.get("user_role") != "admin":

        return """
            <h2>Access Denied</h2>

            <p>
                Only administrators can access this page.
            </p>

            <a href="/">
                Go Home
            </a>
        """


    conn = get_db_connection()


    jobs = conn.execute("""
        SELECT *
        FROM jobs
        ORDER BY id DESC
    """).fetchall()


    conn.close()


    return render_template(
        "admin.html",
        jobs=jobs
    )





# =========================
# JOB DETAILS
# =========================

@app.route("/job/<int:job_id>")
def job_details(job_id):

    conn = get_db_connection()

    job = conn.execute(
        """
        SELECT *
        FROM jobs
        WHERE id = ?
        """,
        (job_id,)
    ).fetchone()

    conn.close()


    if job is None:

        return """
            <h2>Job Not Found</h2>

            <a href="/">
                Go Home
            </a>
        """


    return render_template(
        "job_details.html",
        job=job
    )




# =========================
# APPLY FOR JOB
# =========================

@app.route("/apply/<int:job_id>", methods=["POST"])
def apply_job(job_id):

    # User must be logged in
    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    conn = get_db_connection()


    # Check if job exists
    job = conn.execute(
        """
        SELECT *
        FROM jobs
        WHERE id = ?
        """,
        (job_id,)
    ).fetchone()


    if job is None:

        conn.close()

        return """
            <h2>Job Not Found</h2>

            <a href="/">
                Go Home
            </a>
        """


    # Check if user already applied
    existing_application = conn.execute(
        """
        SELECT *
        FROM applications
        WHERE user_id = ?
        AND job_id = ?
        """,
        (
            session["user_id"],
            job_id
        )
    ).fetchone()


    if existing_application:

        conn.close()

        return """
            <h2>Already Applied</h2>

            <p>
                You have already applied for this job.
            </p>

            <a href="/jobs">
                Back to Jobs
            </a>
        """


    # Insert application
    conn.execute(
        """
        INSERT INTO applications
        (user_id, job_id, status)
        VALUES (?, ?, ?)
        """,
        (
            session["user_id"],
            job_id,
            "Applied"
        )
    )


    conn.commit()
    conn.close()


    return redirect(
        url_for(
            "application_success",
            job_id=job_id
        )
    )


# =========================
# APPLICATION SUCCESS
# =========================

@app.route("/application-success/<int:job_id>")
def application_success(job_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    conn = get_db_connection()


    job = conn.execute(
        """
        SELECT *
        FROM jobs
        WHERE id = ?
        """,
        (job_id,)
    ).fetchone()


    conn.close()


    return render_template(
        "application_success.html",
        job=job
    )


# =========================
# ADD JOB
# =========================

@app.route("/admin/add-job", methods=["GET", "POST"])
def add_job():

    # User must be logged in
    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    # Only admin
    if session.get("user_role") != "admin":

        return """
            <h2>Access Denied</h2>

            <p>
                Only administrators can add jobs.
            </p>

            <a href="/">
                Go Home
            </a>
        """


    if request.method == "POST":

        title = request.form["title"]

        company = request.form["company"]

        location = request.form["location"]

        salary = request.form["salary"]

        description = request.form["description"]


        conn = get_db_connection()


        conn.execute(
            """
            INSERT INTO jobs
            (
                title,
                company,
                location,
                salary,
                description
            )
            VALUES (?, ?, ?, ?, ?)
            """,

            (
                title,
                company,
                location,
                salary,
                description
            )
        )


        conn.commit()

        conn.close()


        return redirect(
            url_for("admin")
        )


    return render_template(
        "add_job.html"
    )


# =========================
# START APPLICATION
# =========================

if __name__ == "__main__":

    create_tables()

    app.run(debug=True)

