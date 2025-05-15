# ---------------------------------------------------------------------
# __init__.py
# Flask app factory and application-wide setup for Grylli
# ---------------------------------------------------------------------

from flask import Flask, request, session, redirect, url_for
from flask_login import current_user, LoginManager
import os
import sqlite3
from app.utils.logging import (
    log_error_message,
    log_step,
    log_info_message,
    log_exception_with_traceback,
)

# ---------------------------------------------------------------------
# Function: create_app
# ---------------------------------------------------------------------

def create_app():
    """
    Initializes and configures the Flask application.

    Returns:
        Flask: A configured Flask app instance.
    """
    app = Flask(__name__, instance_relative_config=True)

    # -------------------------------------------------------------
    # Force session cookie settings for local dev (HTTP)
    # -------------------------------------------------------------
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=False,  # Must be False for local HTTP testing
    )

    # -------------------------------------------------------------
    # Basic Configuration
    # -------------------------------------------------------------
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'supersecretkey')
    app.config['UPLOAD_FOLDER'] = os.path.join(app.instance_path, 'uploads')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # -------------------------------------------------------------
    # Load environment-specific configuration
    # -------------------------------------------------------------
    env_config = os.environ.get('GRYLLI_CONFIG')
    if env_config:
        app.config.from_envvar(env_config)

    # -------------------------------------------------------------
    # Blueprint Registration (to be added per module)
    # -------------------------------------------------------------
    from app.views import about, auth, index
    # from app.views import auth, account, messages, admin, destinations

    # app.register_blueprint(account.bp)
    app.register_blueprint(index.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(about.bp)

    # -------------------------------------------------------------
    # Jinja Globals or Filters (if needed)
    # -------------------------------------------------------------
    app.jinja_env.globals['app_version'] = os.environ.get('APP_VERSION', '0.1.0')

    # ---------------------------------------------------------------------
    # Database Configuration, Creation, and Teardown
    # ---------------------------------------------------------------------
    app.config['DATABASE'] = os.path.join(app.instance_path, 'grylli.db')

    from app.db import close_db, get_db
    from app.models import create_tables

    app.teardown_appcontext(close_db)

    try:
        # Ensure the instance folder exists
        os.makedirs(app.instance_path, exist_ok=True)

        # If the database doesn't exist, create and initialize it
        if not os.path.exists(app.config['DATABASE']):
            log_step("Creating grylli.db and initializing schema")
            conn = sqlite3.connect(app.config['DATABASE'])
            create_tables(conn)
            conn.close()
            log_info_message("Database created and tables initialized successfully.")
    except Exception as e:
        log_exception_with_traceback("Failed to create database on first run", e)

    # ---------------------------------------------------------------------
    # REDIRECT if no admin exists and user is not already bootstrapping
    # ---------------------------------------------------------------------
    @app.before_request
    def redirect_if_no_admin():
        """
        Redirects to /auth/bootstrap if no admin exists and the user is unauthenticated.

        Ensures the app cannot be used until the first admin is created.
        """
        allowed_routes = {"auth.bootstrap", "auth.login", "static"}

        if request.endpoint not in allowed_routes and not session.get("user_id"):
            try:
                db = get_db()
                admin_count = db.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'").fetchone()[0]
                if admin_count == 0:
                    return redirect(url_for("auth.bootstrap"))
            except Exception as e:
                log_error_message(f"Admin bootstrap check failed: {e}")

    # ---------------------------------------------------------------------
    # Create a LoginManager instance and initialize it
    # ---------------------------------------------------------------------
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.login_view = "auth.login"  # Adjust to your login route name
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        db = get_db()
        return User.get_by_id(db, user_id)

    log_info_message(f"App secret key: {app.config['SECRET_KEY']}")

    # ---------------------------------------------------------------------
    # Set Current user
    # ---------------------------------------------------------------------
    @app.context_processor
    def inject_user():
        return dict(current_user=current_user)

    return app
