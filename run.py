# ---------------------------------------------------------------------
# run.py
# Entry point to start the Grylli Flask application
# ---------------------------------------------------------------------

from app import create_app
from app.utils.logging import log_step, log_info_message

# ---------------------------------------------------------------------
# Main Application Bootstrap
# ---------------------------------------------------------------------

if __name__ == "__main__":
    log_step("Starting Grylli")
    app = create_app()
    log_info_message("Grylli Flask app initialized successfully.")
    app.run(host="0.0.0.0", port=5069, debug=True)
