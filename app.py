from flask import Flask, render_template, request, redirect, session, g, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)

app.secret_key = os.environ.get("FLASK_SECRET_KEY", "secure-default-key-12345")


BASE_DIR = os.path.dirname(__file__)
DB_DIR = os.path.join(BASE_DIR, "database")
DB_PATH = os.path.join(DB_DIR, "tickets.db")
os.makedirs(DB_DIR, exist_ok=True)

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

def safe_exec(sql, params=()):
    """Execute a parameterized SQL statement (secure)."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.commit()
    return rows

def init_db():
    """Initialize tables if not exist."""
    safe_exec("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            is_admin INTEGER DEFAULT 0
        )
    """)
    safe_exec("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            creator INTEGER,
            status TEXT DEFAULT 'Open'
        )
    """)
    safe_exec("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER,
            author TEXT,
            content TEXT
        )
    """)



@app.route("/")
def index():
    q = request.args.get("q", "")
    if q:
        tickets = safe_exec(
            "SELECT id, title, description, creator, status FROM tickets WHERE title LIKE ? ORDER BY id DESC",
            (f"%{q}%",)
        )
    else:
        tickets = safe_exec("SELECT id, title, description, creator, status FROM tickets ORDER BY id DESC")
    return render_template("index.html", tickets=tickets, q=q)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        hashed_password = generate_password_hash(password)

        try:
            safe_exec(
                "INSERT INTO users (username, password, is_admin) VALUES (?, ?, 0)",
                (username, hashed_password)
            )
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return "Username already exists.", 400
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        rows = safe_exec("SELECT id, username, password, is_admin FROM users WHERE username = ?", (username,))
        if rows and check_password_hash(rows[0]["password"], password):
            user = rows[0]
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["is_admin"] = bool(user["is_admin"])
            return redirect(url_for("index"))
        return "Invalid credentials.", 401
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/ticket/new", methods=["GET", "POST"])
def new_ticket():
    if "user_id" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        safe_exec(
            "INSERT INTO tickets (title, description, creator) VALUES (?, ?, ?)",
            (title, description, session["user_id"])
        )
        return redirect(url_for("index"))
    return render_template("new_ticket.html")

@app.route("/ticket/<int:ticket_id>", methods=["GET", "POST"])
def view_ticket(ticket_id):
    tickets = safe_exec("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    if not tickets:
        return "Ticket not found.", 404
    ticket = tickets[0]
    comments = safe_exec("SELECT * FROM comments WHERE ticket_id = ? ORDER BY id ASC", (ticket_id,))

    if request.method == "POST":
        if "username" not in session:
            return redirect(url_for("login"))
        author = session["username"]
        content = request.form.get("content", "")
        safe_exec(
            "INSERT INTO comments (ticket_id, author, content) VALUES (?, ?, ?)",
            (ticket_id, author, content)
        )
        return redirect(url_for("view_ticket", ticket_id=ticket_id))

    return render_template("view_ticket.html", ticket=ticket, comments=comments)

@app.route("/admin", methods=["GET", "POST"])
def admin_dashboard():
    if not session.get("is_admin"):
        return "Forbidden.", 403
    if request.method == "POST":
        tid = request.form.get("ticket_id")
        status = request.form.get("status")
        safe_exec("UPDATE tickets SET status = ? WHERE id = ?", (status, tid))
    tickets = safe_exec("SELECT * FROM tickets ORDER BY id DESC")
    return render_template("admin.html", tickets=tickets)


if __name__ == "__main__":
    with app.app_context():
        init_db()
       
        try:
            admin_user = "admin"
            admin_pass = "secureadminpass"
            hashed = generate_password_hash(admin_pass)
            safe_exec("INSERT INTO users (username, password, is_admin) VALUES (?, ?, 1)", (admin_user, hashed))
            print(f"Default admin created: {admin_user} / {admin_pass}")
        except sqlite3.IntegrityError:
            pass
    print("Running IT Support demo on http://127.0.0.1:5000")
    app.run(debug=True)
