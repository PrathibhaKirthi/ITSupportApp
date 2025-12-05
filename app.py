from flask import Flask, render_template, request, redirect, session, g
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "insecure-demo-key"   # intentionally insecure

BASE_DIR = os.path.dirname(__file__)
DB_DIR = os.path.join(BASE_DIR, "database")
DB_PATH = os.path.join(DB_DIR, "tickets.db")
os.makedirs(DB_DIR, exist_ok=True)

# ----------------- Database helpers -----------------
def get_conn():
    conn = getattr(g, "_conn", None)
    if conn is None:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        g._conn = conn
    return conn

@app.teardown_appcontext
def close_conn(exc):
    conn = getattr(g, "_conn", None)
    if conn is not None:
        conn.close()

def unsafe_exec(sql):
    """INSECURE: executes raw SQL with string concatenation."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    conn.commit()
    return rows

def init_db():
    unsafe_exec("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT,
            is_admin INTEGER DEFAULT 0
        )
    """)

    unsafe_exec("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            creator INTEGER,
            status TEXT DEFAULT 'Open'
        )
    """)

    unsafe_exec("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER,
            author TEXT,
            content TEXT
        )
    """)

# ----------------- Routes -----------------
@app.route("/")
def index():
    q = request.args.get("q", "")

    if q:
        # SQL injection vulnerability
        tickets = unsafe_exec(
            f"SELECT id, title, description, creator, status FROM tickets WHERE title LIKE '%{q}%'"
        )
    else:
        tickets = unsafe_exec("SELECT * FROM tickets ORDER BY id DESC")

    return render_template("index.html", tickets=tickets, q=q)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")  # STORED IN PLAINTEXT

        unsafe_exec(
            f"INSERT INTO users (username, password, is_admin) VALUES ('{username}', '{password}', 0)"
        )
        return redirect("/login")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        # SQL Injection Vulnerability
        rows = unsafe_exec(
            f"SELECT id, username, password, is_admin FROM users WHERE username = '{username}'"
        )

        if rows and rows[0]["password"] == password:
            session["user_id"] = rows[0]["id"]
            session["username"] = rows[0]["username"]
            session["is_admin"] = rows[0]["is_admin"]
            return redirect("/")
        return "Invalid credentials", 401
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/ticket/new", methods=["GET", "POST"])
def new_ticket():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        title = request.form.get("title", "")
        description = request.form.get("description", "")  # Stored XSS vulnerability

        unsafe_exec(
            f"INSERT INTO tickets (title, description, creator) VALUES ('{title}', '{description}', {session['user_id']})"
        )
        return redirect("/")
    return render_template("new_ticket.html")

@app.route("/ticket/<int:ticket_id>", methods=["GET", "POST"])
def view_ticket(ticket_id):
    ticket = unsafe_exec(f"SELECT * FROM tickets WHERE id = {ticket_id}")
    if not ticket:
        return "Not Found", 404

    comments = unsafe_exec(f"SELECT * FROM comments WHERE ticket_id = {ticket_id}")

    if request.method == "POST":
        content = request.form.get("content", "")  # Stored XSS
        author = session.get("username", "Anonymous")

        unsafe_exec(
            f"INSERT INTO comments (ticket_id, author, content) VALUES ({ticket_id}, '{author}', '{content}')"
        )
        return redirect(f"/ticket/{ticket_id}")

    return render_template("view_ticket.html", ticket=ticket[0], comments=comments)

@app.route("/admin", methods=["GET", "POST"])
def admin_dashboard():
    # ❌ Insecure: NO admin check!
    if request.method == "POST":
        tid = request.form.get("ticket_id")
        status = request.form.get("status")
        unsafe_exec(f"UPDATE tickets SET status = '{status}' WHERE id = {tid}")

    tickets = unsafe_exec("SELECT * FROM tickets ORDER BY id DESC")
    return render_template("admin.html", tickets=tickets)

# ----------------- Main -----------------
if __name__ == "__main__":
    with app.app_context():
        init_db()
        # default insecure admin with plaintext password
        unsafe_exec("INSERT INTO users (username, password, is_admin) VALUES ('admin', 'admin123', 1)")

    app.run(debug=True)
