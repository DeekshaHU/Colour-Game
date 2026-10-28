import os
import secrets
import sqlite3
from functools import wraps
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "colour_game.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS game_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            score INTEGER NOT NULL CHECK(score >= 0),
            correct_answers INTEGER NOT NULL CHECK(correct_answers >= 0),
            total_answers INTEGER NOT NULL CHECK(total_answers >= correct_answers),
            duration_seconds INTEGER NOT NULL DEFAULT 30,
            played_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)
    db.commit()
    db.close()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to access that page.", "warning")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if len(username) < 3 or len(username) > 24:
            flash("Username must be 3–24 characters long.", "danger")
        elif "@" not in email or len(email) > 120:
            flash("Please enter a valid email address.", "danger")
        elif len(password) < 8:
            flash("Password must contain at least 8 characters.", "danger")
        else:
            db = get_db()
            try:
                cur = db.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                    (username, email, generate_password_hash(password))
                )
                db.commit()
                session.clear()
                session["user_id"] = cur.lastrowid
                session["username"] = username
                flash("Account created. Welcome to Colour Rush!", "success")
                return redirect(url_for("dashboard"))
            except sqlite3.IntegrityError:
                flash("That username or email is already registered.", "danger")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_db().execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash("You are now logged in.", "success")
            next_url = request.args.get("next", "")
            if next_url.startswith("/") and not next_url.startswith("//"):
                return redirect(next_url)
            return redirect(url_for("dashboard"))
        flash("Incorrect email or password.", "danger")
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/game")
@login_required
def game():
    # A one-time nonce makes accidental duplicate submissions less likely.
    session["game_nonce"] = secrets.token_urlsafe(16)
    return render_template("game.html", game_nonce=session["game_nonce"])


@app.route("/api/scores", methods=["POST"])
@login_required
def save_score():
    data = request.get_json(silent=True) or {}
    nonce = data.get("game_nonce")
    if not nonce or nonce != session.get("game_nonce"):
        return jsonify({"error": "Invalid or already-used game session. Start a new game."}), 400

    try:
        score = int(data.get("score", -1))
        correct = int(data.get("correct_answers", -1))
        total = int(data.get("total_answers", -1))
        duration = int(data.get("duration_seconds", 30))
    except (TypeError, ValueError):
        return jsonify({"error": "Score details must be numbers."}), 400

    if not (0 <= score <= 100000 and 0 <= correct <= total <= 1000 and duration == 30):
        return jsonify({"error": "Invalid game result."}), 400

    # For a portfolio/demo project, this records the game result sent by the client.
    # A production leaderboard should validate each answer and timing on the server.
    db = get_db()
    db.execute(
        """INSERT INTO game_results
           (user_id, score, correct_answers, total_answers, duration_seconds)
           VALUES (?, ?, ?, ?, ?)""",
        (session["user_id"], score, correct, total, duration)
    )
    db.commit()
    session.pop("game_nonce", None)
    return jsonify({"message": "Score saved successfully!", "score": score})


@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    user_id = session["user_id"]
    stats = db.execute("""
        SELECT COUNT(*) AS games,
               COALESCE(MAX(score), 0) AS best_score,
               COALESCE(ROUND(AVG(score), 1), 0) AS average_score,
               COALESCE(SUM(correct_answers), 0) AS correct,
               COALESCE(SUM(total_answers), 0) AS total
        FROM game_results WHERE user_id = ?
    """, (user_id,)).fetchone()
    history = db.execute("""
        SELECT score, correct_answers, total_answers, played_at
        FROM game_results WHERE user_id = ?
        ORDER BY id DESC LIMIT 10
    """, (user_id,)).fetchall()
    accuracy = round((stats["correct"] / stats["total"]) * 100, 1) if stats["total"] else 0
    return render_template("dashboard.html", stats=stats, history=history, accuracy=accuracy)


@app.route("/leaderboard")
def leaderboard():
    rows = get_db().execute("""
        SELECT u.username, MAX(r.score) AS best_score, COUNT(r.id) AS games_played
        FROM users u
        JOIN game_results r ON r.user_id = u.id
        GROUP BY u.id, u.username
        ORDER BY best_score DESC, games_played DESC
        LIMIT 20
    """).fetchall()
    return render_template("leaderboard.html", rows=rows)


@app.errorhandler(404)
def not_found(error):
    return render_template("base.html", standalone_message="Page not found."), 404


init_db()

if __name__ == "__main__":
    app.run(debug=True)
