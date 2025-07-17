# ---------------------------------------------------------------------
# csp_report.py
# app/views/csp_report.py
# CSP Report handler for violation reporting
# ---------------------------------------------------------------------
from flask import Blueprint, jsonify, request

from app.utils.logging import log_exception_with_traceback, log_info_message

bp = Blueprint("csp_report", __name__)


@bp.route("overview", methods=["POST"], strict_slashes=False)
def overview():
    try:
        # Get the JSON body that contains the CSP violation data
        report = request.get_json(force=True)

        # Extract important fields from the CSP report
        document_uri = report.get("csp-report", {}).get("document-uri", "Unknown URI")
        violated_directive = report.get("csp-report", {}).get(
            "violated-directive", "Unknown Directive"
        )
        blocked_uri = report.get("csp-report", {}).get("blocked-uri", "Unknown URI")
        source_file = report.get("csp-report", {}).get("source-file", "Unknown File")
        line_number = report.get("csp-report", {}).get("line-number", "Unknown Line")
        script_sample = report.get("csp-report", {}).get(
            "script-sample", "No script sample available"
        )

        # Log the CSP violation with file and line number for better debugging
        log_info_message(
            f"CSP Violation Reported: \n"
            f"Document URI: {document_uri}\n"
            f"Violated Directive: {violated_directive}\n"
            f"Blocked URI: {blocked_uri}\n"
            f"Source File: {source_file}\n"
            f"Line Number: {line_number}\n"
            f"Full Report: {report}\n"
            f"Script Sample: {script_sample}"
        )

        # If the violation is related to inline styles or scripts, log it with extra details
        if "inline" in blocked_uri:
            log_info_message(
                f"⚠️ Inline styles/scripts violation detected! "
                f"Source File: {source_file}, Line: {line_number}"
            )
            # Log additional script sample or inline styles if present
            if script_sample:
                log_info_message(f"Inline script sample: {script_sample}")

        # If the violation is related to a common source (e.g., htmx.min.js), log this specifically
        if "htmx.min.js" in source_file:
            log_info_message(
                "⚠️ HTMX-related CSP violation detected. Review if inline styles/scripts are being used."
            )

        # Send a successful response back to the client
        return jsonify({"status": "ok"}), 200

    except Exception as e:
        log_exception_with_traceback("CSP report handling failed", e)
        return jsonify({"status": "error"}), 500
