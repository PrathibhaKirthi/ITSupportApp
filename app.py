from flask import Flask, render_template, request, redirect, session, g, url_for
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "demo-insecure-key"  # intentionally insecure for demo

# Database setup
BASE_DIR = os.path.dirname(__file__)
DB_DIR = os.path.join(BASE_DIR, "database")
DB_PATH = os.path.join(DB_DIR, "tickets.db")
os.makedirs(DB_DIR, exist_ok=True)


# ---------------- Database helpers ----------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT,
            is_admin INTEGER DEFAULT 0
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            creator TEXT,
            status TEXT DEFAULT 'Open'
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER,
            author TEXT,
            content TEXT
        )
    """)
    # default admin
    try:
        db.execute("INSERT INTO users (username, password, is_admin) VALUES ('admin', 'admin123', 1)")
    except sqlite3.IntegrityError:
        pass
    db.commit()


# ---------------- Routes ----------------

@app.route("/")
def index():
    db = get_db()
    tickets = db.execute("SELECT * FROM tickets ORDER BY id DESC").fetchall()
    return render_template("index.html", tickets=tickets)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        db = get_db()
        db.execute(f"INSERT INTO users (username, password) VALUES ('{username}', '{password}')")
        db.commit()
        return redirect("/login")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        db = get_db()
        # intentionally insecure login for SQLi demo
        user = db.execute(f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'").fetchone()
        if user:
            session["username"] = user["username"]
            session["is_admin"] = bool(user["is_admin"])
            return redirect(url_for("index"))
        return "Invalid credentials", 401
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/ticket/new", methods=["GET", "POST"])
def new_ticket():
    if "username" not in session:
        return redirect("/login")
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        db = get_db()
        # intentionally vulnerable to XSS
        db.execute(f"INSERT INTO tickets (title, description, creator) VALUES ('{title}', '{description}', '{session['username']}')")
        db.commit()
        return redirect(url_for("index"))
    return render_template("new_ticket.html")


@app.route("/ticket/<int:ticket_id>", methods=["GET", "POST"])
def view_ticket(ticket_id):
    db = get_db()
    ticket = db.execute(f"SELECT * FROM tickets WHERE id = {ticket_id}").fetchone()
    comments = db.execute(f"SELECT * FROM comments WHERE ticket_id = {ticket_id}").fetchall()

    if request.method == "POST":
        if "username" not in session:
            return redirect("/login")
        content = request.form.get("content")
        db.execute(f"INSERT INTO comments (ticket_id, author, content) VALUES ({ticket_id}, '{session['username']}', '{content}')")
        db.commit()
        # add new comment to comments for popup
        comments = list(comments)
        comments.append({"author": session["username"], "content": content})
        return render_template("view_ticket.html", ticket=ticket, comments=comments, success=True)

    return render_template("view_ticket.html", ticket=ticket, comments=comments)


@app.route("/admin_Dashboard", methods=["GET", "POST"])
def admin_dashboard():
    if not session.get("is_admin"):
        return "Forbidden", 403
    db = get_db()
    tickets = db.execute("SELECT * FROM tickets ORDER BY id DESC").fetchall()
    if request.method == "POST":
        tid = request.form.get("ticket_id")
        status = request.form.get("status")
        db.execute(f"UPDATE tickets SET status = '{status}' WHERE id = {tid}")
        db.commit()
        return redirect("/admin_Dashboard")
    return render_template("admin_Dashboard.html", tickets=tickets)


# ---------------- Main ----------------
if __name__ == "__main__":
    with app.app_context():
        init_db()
    print("Running insecure IT Support demo on http://127.0.0.1:5000")
    app.run(debug=True)
