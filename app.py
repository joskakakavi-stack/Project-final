from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from flask import Flask, g, redirect, render_template, request, url_for

from scheduler import DAYS, generate_schedule as build_schedule, init_schema, rows

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "data" / "scheduler.db"

app = Flask(__name__)


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        DATABASE.parent.mkdir(exist_ok=True)
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception: Exception | None = None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    init_schema(get_db())


@app.before_request
def ensure_database() -> None:
    init_db()


@app.route("/")
def index():
    db = get_db()
    data: dict[str, Any] = {
        "professors": rows(db, "SELECT * FROM professors ORDER BY name"),
        "rooms": rows(db, "SELECT * FROM rooms ORDER BY name"),
        "courses": rows(
            db,
            """
            SELECT courses.*, professors.name AS professor_name
            FROM courses JOIN professors ON professors.id = courses.professor_id
            ORDER BY courses.semester, courses.name
            """,
        ),
        "schedule": rows(
            db,
            """
            SELECT schedule_entries.*, courses.name AS course_name, courses.credits,
                   courses.cohorts, courses.departments, courses.semester,
                   professors.name AS professor_name, rooms.name AS room_name
            FROM schedule_entries
            JOIN courses ON courses.id = schedule_entries.course_id
            JOIN professors ON professors.id = schedule_entries.professor_id
            JOIN rooms ON rooms.id = schedule_entries.room_id
            ORDER BY schedule_entries.day, schedule_entries.start_time
            """,
        ),
        "days": DAYS,
    }
    return render_template("index.html", **data)


@app.post("/professors")
def add_professor():
    unavailable_days = ",".join(request.form.getlist("unavailable_days"))
    db = get_db()
    db.execute(
        "INSERT INTO professors (name, email, unavailable_days) VALUES (?, ?, ?)",
        (request.form["name"].strip(), request.form.get("email", "").strip(), unavailable_days),
    )
    db.commit()
    return redirect(url_for("index"))


@app.post("/rooms")
def add_room():
    db = get_db()
    db.execute(
        "INSERT INTO rooms (name, capacity) VALUES (?, ?)",
        (request.form["name"].strip(), int(request.form.get("capacity", 0))),
    )
    db.commit()
    return redirect(url_for("index"))


@app.post("/courses")
def add_course():
    db = get_db()
    db.execute(
        """
        INSERT INTO courses (name, credits, total_hours, professor_id, cohorts, departments, semester)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            request.form["name"].strip(),
            int(request.form["credits"]),
            int(request.form["total_hours"]),
            int(request.form["professor_id"]),
            request.form["cohorts"].strip(),
            request.form["departments"].strip(),
            request.form["semester"].strip(),
        ),
    )
    db.commit()
    return redirect(url_for("index"))


@app.post("/generate")
def generate():
    warnings = build_schedule(get_db())
    return render_template("generated.html", warnings=warnings)


@app.post("/reset")
def reset():
    db = get_db()
    for table in ["schedule_entries", "courses", "rooms", "professors"]:
        db.execute(f"DELETE FROM {table}")
    db.commit()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
