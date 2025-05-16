# ---------------------------------------------------------------------
# __init__.py
# Flask app factory and application-wide setup for Grylli
# ---------------------------------------------------------------------

from flask import Flask, request, session, redirect, url_for
from flask_login import current_user, LoginManager
from flask_migrate import Migrate, upgrade
from app.models import db
from app.services.settings import seed_system_config_from_env
from sqlalchemy import text
import os
from flask_babel import Babel

from app.utils.logging import (
    log_error_message,
    log_step,
    log_info_message,
    log_exception_with_traceback,
)

def create_app():
    """
    Initializes and configures the Flask application.

    Returns:
        Flask: A configured Flask app instance.
    """
    app = Flask(__name__, instance_relative_config=True)

    # Correctly load app/config.py regardless of instance_relative_config
    app.config.from_pyfile(os.path.join(app.root_path, "config.py"))

    # -------------------------------------------------------------
    # Force session cookie settings for local dev (HTTP)
    # -------------------------------------------------------------
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=False,  # Must be False for local HTTP testing
    )

    # -------------------------------------------------------------
    # Initialize Babel
    # -------------------------------------------------------------
    # Optional: set default locale
    app.config['BABEL_DEFAULT_LOCALE'] = 'en'
    app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'app/translations'

    def get_locale():
        # Check session first, fallback to browser settings
        return session.get('lang') or request.accept_languages.best_match(['en', 'es', 'fr'])

    babel = Babel(app, locale_selector=get_locale)

    # ✅ Add this AFTER the Babel line:
    app.jinja_env.globals['get_locale'] = get_locale

    # -------------------------------------------------------------
    # Basic Configuration
    # -------------------------------------------------------------
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'supersecretkey')
    app.config['UPLOAD_FOLDER'] = os.path.join(app.instance_path, 'uploads')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # -------------------------------------------------------------
    # Load environment-specific configuration
    # -------------------------------------------------------------
    app.config.from_pyfile(os.path.join(app.root_path, "config.py"))

    # -------------------------------------------------------------
    # Blueprint Registration
    # -------------------------------------------------------------
    from app.views import about, auth, index, account, admin

    app.register_blueprint(admin.bp)
    app.register_blueprint(account.bp)
    app.register_blueprint(index.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(about.bp)

    print("---- Registered routes ----")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint:30} {rule}")
    print("---------------------------")

    # -------------------------------------------------------------
    # Initialize SQLAlchemy and Flask-Migrate
    # -------------------------------------------------------------
    db.init_app(app)
    migrate = Migrate(app, db)

    with app.app_context():
        os.makedirs(app.instance_path, exist_ok=True)
        # Automatically apply any pending migrations
        if os.path.exists(os.path.join(app.root_path, "migrations")):
            upgrade()
        seed_system_config_from_env()

    # -------------------------------------------------------------
    # Jinja Globals
    # -------------------------------------------------------------
    app.jinja_env.globals['app_version'] = os.environ.get('APP_VERSION', '0.1.0')

    # -------------------------------------------------------------
    # Flask-Login Setup
    # -------------------------------------------------------------
    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    @app.context_processor
    def inject_user():
        return dict(current_user=current_user)

    # -------------------------------------------------------------
    # Admin Bootstrap Check
    # -------------------------------------------------------------
    @app.before_request
    def enforce_login_and_bootstrap():
        allowed_routes = {"auth.bootstrap", "auth.login", "static"}

        if request.endpoint in allowed_routes:
            return  # allow access to login, bootstrap, static files

        try:
            admin_count = db.session.execute(
                text("SELECT COUNT(*) FROM users WHERE role = 'admin'")
            ).scalar()
        except Exception as e:
            log_error_message(f"Admin bootstrap check failed: {e}")
            return "Internal server error", 500

        # If no admin exists, always redirect to bootstrap
        if admin_count == 0:
            return redirect(url_for("auth.bootstrap"))

        # Block any unauthenticated user
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))

    log_info_message(f"App secret key: {app.config['SECRET_KEY']}")

    return app
