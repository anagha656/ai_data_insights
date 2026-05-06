import os
import sqlite3
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
from flask import Flask, request, jsonify, send_from_directory, session, redirect
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "your_secret_key_change_this"
CORS(app, supports_credentials=True, origins=["http://127.0.0.1:5000", "http://localhost:5000"])

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DB = "app.db"

# Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ─────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────

def init_db():
    conn = sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email    TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id   INTEGER NOT NULL,
            filename  TEXT NOT NULL,
            rows      INTEGER,
            cols      INTEGER,
            created   TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def chart_to_base64():
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", dpi=100)
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")

def logged_in():
    return "user_id" in session

def analyze_csv(filepath):
    df = pd.read_csv(filepath)

    # fix missing values
    for col in df.columns:
        if df[col].dtype == "object" or str(df[col].dtype) == "string":
            df[col] = df[col].fillna("Unknown")
        else:
            df[col] = df[col].fillna(0)

    num_cols  = df.select_dtypes(include=["int64","float64"]).columns.tolist()
    text_cols = df.select_dtypes(include=["object","str","string"]).columns.tolist()
    rows, cols = df.shape

    # summary stats
    stats = {}
    if num_cols:
        stats = df[num_cols].describe().round(2).to_dict()

    # charts
    charts = []

    # chart 1 — bar chart for first text column
    if text_cols:
        col = text_cols[0]
        counts = df[col].value_counts().head(8)
        fig, ax = plt.subplots(figsize=(7,4))
        ax.bar(counts.index, counts.values, color="#378ADD")
        ax.set_title(f"Count by {col}")
        ax.set_ylabel("Count")
        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()
        charts.append({"title": f"Count by {col}", "img": chart_to_base64()})

    # chart 2 — histogram for first number column
    if num_cols:
        col = num_cols[0]
        fig, ax = plt.subplots(figsize=(7,4))
        ax.hist(df[col].dropna(), bins=10, color="#639922", edgecolor="white")
        ax.set_title(f"Distribution of {col}")
        plt.tight_layout()
        charts.append({"title": f"Distribution of {col}", "img": chart_to_base64()})

    # chart 3 — groupby chart
    if text_cols and num_cols:
        grp = df.groupby(text_cols[0])[num_cols[0]].sum().sort_values(ascending=False).head(8)
        fig, ax = plt.subplots(figsize=(7,4))
        ax.bar(grp.index, grp.values, color="#BA7517")
        ax.set_title(f"Total {num_cols[0]} by {text_cols[0]}")
        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()
        charts.append({"title": f"{num_cols[0]} by {text_cols[0]}", "img": chart_to_base64()})

    # data summary for AI context
    summary_text = f"""
Dataset: {os.path.basename(filepath)}
Rows: {rows} | Columns: {cols}
Number columns: {num_cols}
Text columns: {text_cols}
Stats:
{df[num_cols].describe().round(2).to_string() if num_cols else 'No numeric columns'}
Sample data:
{df.head(5).to_string()}
"""

    return {
        "rows": rows,
        "cols": cols,
        "num_cols": num_cols,
        "text_cols": text_cols,
        "stats": stats,
        "charts": charts,
        "summary_text": summary_text
    }


# ─────────────────────────────────────────
# ROUTES — PAGES
# ─────────────────────────────────────────

@app.route("/")
def home():
    return send_from_directory(".", "index.html")

@app.route("/dashboard")
def dashboard():
    if not logged_in():
        return redirect("/")
    return send_from_directory(".", "dashboard.html")


# ─────────────────────────────────────────
# ROUTES — AUTH
# ─────────────────────────────────────────

@app.route("/signup", methods=["POST"])
def signup():
    data     = request.json
    username = data.get("username", "").strip()
    email    = data.get("email", "").strip()
    password = data.get("password", "")

    if not username or not email or not password:
        return jsonify({"error": "All fields required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    hashed = generate_password_hash(password)
    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO users (username, email, password) VALUES (?,?,?)",
            (username, email, hashed)
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Signup successful!"})
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username or email already exists"}), 400


@app.route("/login", methods=["POST"])
def login():
    data     = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "")

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE username=?", (username,)
    ).fetchone()
    conn.close()

    if not user or not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid username or password"}), 401

    session["user_id"]  = user["id"]
    session["username"] = user["username"]
    return jsonify({"message": "Login successful!", "username": user["username"]})


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out!"})


@app.route("/me")
def me():
    if not logged_in():
        return jsonify({"error": "Not logged in"}), 401
    return jsonify({"username": session["username"], "user_id": session["user_id"]})


# ─────────────────────────────────────────
# ROUTES — ANALYSIS
# ─────────────────────────────────────────

@app.route("/upload", methods=["POST"])
def upload():
    if not logged_in():
        return jsonify({"error": "Please login first"}), 401

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if not file.filename.endswith(".csv"):
        return jsonify({"error": "Only CSV files supported"}), 400

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    try:
        result = analyze_csv(filepath)
    except Exception as e:
        return jsonify({"error": f"Could not analyze file: {str(e)}"}), 500

    # save to history
    conn = get_db()
    conn.execute(
        "INSERT INTO analyses (user_id, filename, rows, cols) VALUES (?,?,?,?)",
        (session["user_id"], file.filename, result["rows"], result["cols"])
    )
    conn.commit()
    conn.close()

    # remove summary_text from response (keep for AI only)
    summary = result.pop("summary_text")
    session["last_summary"] = summary  # store for AI chat

    return jsonify(result)


@app.route("/ask", methods=["POST"])
def ask():
    if not logged_in():
        return jsonify({"error": "Please login first"}), 401

    question = request.json.get("question", "")
    summary  = session.get("last_summary", "No dataset uploaded yet")

    prompt = f"""
You are a data analyst assistant. A user has uploaded a CSV dataset.
Here is the dataset summary:
{summary}

Answer this question about the data in a clear and friendly way — 2 to 4 sentences max:
{question}
"""
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )
        answer = response.choices[0].message.content
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/history")
def history():
    if not logged_in():
        return jsonify({"error": "Not logged in"}), 401
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM analyses WHERE user_id=? ORDER BY created DESC",
        (session["user_id"],)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


# ─────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
