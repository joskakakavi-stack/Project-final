from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config


app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."
login_manager.login_message_category = "warning"


class User(UserMixin, db.Model):
    """A user who can access the scheduling application."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == "admin"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def seed_default_users():
    """Create the demonstration accounts when the database is initialized."""
    if User.query.count():
        return

    admin = User(
        username="admin",
        email="admin@university.com",
        full_name="Administrateur System",
        role="admin",
    )
    admin.set_password("admin123")

    teacher = User(
        username="prof_dupont",
        email="dupont@university.com",
        full_name="Jean Dupont",
        role="user",
    )
    teacher.set_password("password")

    db.session.add_all((admin, teacher))
    db.session.commit()


@app.route("/")
def index():
    return redirect(url_for("dashboard"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password) and user.is_active:
            login_user(user)
            flash("Connexion réussie !", "success")
            return redirect(url_for("dashboard"))

        flash("Identifiants invalides ou compte inactif.", "danger")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Vous êtes déconnecté.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    stats = {
        "total_users": User.query.count(),
        "total_faculties": 0,
        "total_courses": 0,
        "total_teachers": 0,
    }
    return render_template("dashboard.html", stats=stats)


@app.shell_context_processor
def make_shell_context():
    return {"app": app, "db": db, "User": User}


def initialize_database():
    """Set up the Phase 1 schema and its sample accounts."""
    db.create_all()
    seed_default_users()


if __name__ == "__main__":
    with app.app_context():
        initialize_database()
    app.run(debug=True, host="0.0.0.0", port=5000)
