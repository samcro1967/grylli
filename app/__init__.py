# ---------------------------------------------------------------------
# __init__.py
# Full Flask app factory with blueprints, login, Babel, sessions, etc.
# ---------------------------------------------------------------------

from app.utils.locale import get_locale
from app.views import admin, account, index, auth, about
from flask import Flask, request, redirect, url_for
from flask_login import current_user, LoginManager
from flask_migrate import Migrate, upgrade
from app.extensions import db      # import db here from extensions
from app.services.settings import seed_system_config_from_env
from sqlalchemy import inspect, text
import os
from flask_babel import Babel, _
from datetime import timedelta
from app.views import locale
from app.utils.logging import (
    log_error_message,
    log_info_message,
    log_debug_message,
    log_exception_with_traceback,
)
import os

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_pyfile(os.path.join(app.root_path, "config.py"))

    # Override or set SECRET_KEY explicitly from environment if needed
    app.config['SECRET_KEY'] = os.environ.get('FLASK_APP_KEY') or app.config.get('SECRET_KEY')

    base_url = os.environ.get("BASE_URL", "/").rstrip("/")
    app.config['BASE_URL'] = base_url

    # Setup logging DB URI info
    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI")
    log_info_message(f"DB URI: {db_uri}")

    # Initialize DB and migrations, no queries yet
    db.init_app(app)
    migrate = Migrate(app, db)

    with app.app_context():
        # Ensure instance folder exists
        os.makedirs(app.instance_path, exist_ok=True)

        # Check if DB or required tables exist:
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        log_info_message(f"Tables currently in DB: {tables}")

        # If no tables or missing critical table, run migrations before anything else
        if not tables or "system_config" not in tables:
            log_info_message("Database or system_config table missing. Running migrations now...")
            try:
                upgrade()
                log_info_message("Migrations applied successfully.")
            except Exception as e:
                log_error_message("Migration failed.")
                log_exception_with_traceback("Migration error", exception=e)
                raise

        # Now it is safe to seed system config or do DB queries
        try:
            seed_system_config_from_env()
            log_info_message("System config seeded successfully.")
        except Exception as e:
            log_error_message("Error seeding system config")
            log_exception_with_traceback("Seeding error", exception=e)
            # Optional: decide if you want to raise or continue with defaults

    # Continue with registering blueprints, Babel, session config, etc.
    app.config["SESSION_PERMANENT"] = True
    app.permanent_session_lifetime = timedelta(days=30)

    app.register_blueprint(locale.bp)

    # Session cookie config for local dev HTTP
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=False,
    )

    app.config['BABEL_DEFAULT_LOCALE'] = 'en'
    app.config["BABEL_TRANSLATION_DIRECTORIES"] = os.path.join(app.root_path, "translations")
    app.config["BABEL_DEFAULT_DOMAIN"] = "messages"
    babel = Babel(app, locale_selector=get_locale)

    app.jinja_env.globals['_'] = _
    app.jinja_env.globals['get_locale'] = get_locale
    app.jinja_env.globals['app_version'] = os.environ.get('APP_VERSION', '0.1.0')

    prefix = app.config['BASE_URL']
    if prefix == "/":
        prefix = ""  # root, no prefix needed
    elif prefix and not prefix.startswith("/"):
        prefix = "/" + prefix  # ensure leading slash

    app.register_blueprint(admin.bp, url_prefix=prefix)
    app.register_blueprint(account.bp, url_prefix=prefix)
    app.register_blueprint(index.bp, url_prefix=prefix)
    app.register_blueprint(auth.bp, url_prefix=prefix)
    app.register_blueprint(about.bp, url_prefix=prefix)

    log_debug_message("---- Registered routes ----")
    for rule in app.url_map.iter_rules():
        log_debug_message(f"{rule.endpoint:30} {rule}")
    log_debug_message("---------------------------")

    # Flask-Login setup
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

    # Admin bootstrap check
    @app.before_request
    def enforce_login_and_bootstrap():
        allowed_routes = {"auth.bootstrap", "auth.login", "static"}
        if request.endpoint in allowed_routes:
            return

        try:
            admin_count = db.session.execute(text("SELECT COUNT(*) FROM users WHERE role = 'admin'")).scalar()
        except Exception as e:
            log_error_message(f"Admin bootstrap check failed: {e}")
            return "Internal server error", 500

        if admin_count == 0:
            return redirect(url_for("auth.bootstrap"))

        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))

    log_info_message(f"App secret key: {app.config['SECRET_KEY']}")

    # Redirect base path without trailing slash to trailing slash
    if prefix:
        @app.route(prefix)
        def redirect_to_base_slash():
            return redirect(prefix + "/")

    return app
