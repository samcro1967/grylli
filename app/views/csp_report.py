# ---------------------------------------------------------------------
# csp_report.py
# app/views/csp_report.py
# CSP Report handler for violation reporting
# ---------------------------------------------------------------------

from flask import Blueprint, request, jsonify
from app.utils.logging import log_info_message, log_exception_with_traceback

bp = Blueprint("csp_report", __name__)  # Match the blueprint mount name (e.g. /grylli/meta)

@bp.route("/overview", methods=["POST"])
def overview():
    try:
        report = request.get_json(force=True)
        log_info_message(f"CSP Violation Reported: {report}")
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        log_exception_with_traceback("CSP report handling failed", e)
        return jsonify({"status": "error"}), 500
