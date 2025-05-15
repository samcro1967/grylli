# ---------------------------------------------------------------------
# __init__.py
# Flask app factory and application-wide setup for Grylli
# ---------------------------------------------------------------------

from flask import Flask
import os

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
    from app.views import about
    #from app.views import auth, account, about  # Add others as created

    #app.register_blueprint(auth.bp)
    #app.register_blueprint(account.bp)
    app.register_blueprint(about.bp)

    # -------------------------------------------------------------
    # Jinja Globals or Filters (if needed)
    # -------------------------------------------------------------
    app.jinja_env.globals['app_version'] = os.environ.get('APP_VERSION', '0.1.0')

    return app
