"""
app/init/errors.py
Flask application factory setup: config, DB, login, blueprints, session, i18n, and scheduler.
"""

from flask import render_template
from werkzeug.exceptions import HTTPException


def register_error_handlers(app):
    @app.errorhandler(500)
    def internal_server_error(error):
        app.logger.error("Internal server error: %s", error)
        return render_template("errors/500.html"), 500

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(Exception)
    def handle_unexpected_exception(error):
        if isinstance(error, HTTPException):
            return error
        app.logger.exception("Unhandled exception: %s", error)
        return render_template("errors/500.html"), 500
