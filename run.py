"""
run.py
Entry point to start the Grylli Flask application.
"""

# ---------------------------------------------------------------------
# Standard Library Imports
# ---------------------------------------------------------------------
import signal
import sys

# ---------------------------------------------------------------------
# Local Imports
# ---------------------------------------------------------------------
from app import create_app
from app.utils.logging import log_step, log_info_message
from app.utils.banner import print_banner_and_github

# ---------------------------------------------------------------------
# Signal Handling for Graceful Shutdown
# ---------------------------------------------------------------------
def handle_exit(signum, _frame):
    """
    Handles shutdown signals (SIGINT/SIGTERM) to gracefully terminate the application.

    Args:
        signum (int): Signal number (e.g., SIGINT, SIGTERM).
        _frame: Current stack frame (unused).

    Logs a shutdown message based on signal type,
    performs any cleanup if needed, and exits the program.
    """
    if signum == signal.SIGINT:
        print(
            "\n🛑 Shutting down Grylli gracefully "
            "(Ctrl+C caught)"
        )
    elif signum == signal.SIGTERM:
        print(
            "\n🛑 Shutting down Grylli gracefully "
            "(Docker stop/SIGTERM)"
        )
    else:
        print(
            f"\n🛑 Shutting down Grylli gracefully (signal {signum})"
        )
    # Note: Insert any additional cleanup logic here if needed
    # (e.g., close DB connections, flush logs).
    sys.exit(0)

# ---------------------------------------------------------------------
# Main Application Bootstrap
# ---------------------------------------------------------------------
def main():
    """
    Main application entrypoint.
    Sets up signal handlers, prints a Grylli banner, logs startup messages,
    creates the Flask app, and runs the server with configuration from app config.
    """
    # Register handlers for Docker stop (SIGTERM) and Ctrl+C (SIGINT)
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    # Initialize Flask app using factory pattern
    app = create_app()

    # Visual banner and GitHub URL, always using config
    print_banner_and_github(app)

    log_step("Starting Grylli")
    log_info_message("Grylli Flask app initialized successfully.")

    # Start Flask development server with settings from config
    app.run(
        host=app.config["FLASK_HOST"],
        port=app.config["FLASK_PORT"],
        debug=app.config["FLASK_DEBUG"],
    )

if __name__ == "__main__":
    main()
