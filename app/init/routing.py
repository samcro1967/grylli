"""
# ---------------------------------------------------------------------
# routing.py
# app/init/routing.py
# Route map debug logging for Flask application factory.
# ---------------------------------------------------------------------
"""

from app.utils.logging import log_debug_message


def log_route_map(app):
    """
    Log the registered routes and endpoints for debugging.
    DO NOT CHANGE FUNCTIONALITY OR ORDER—direct copy from create_app.
    """
    # -------------------------------------------
    # Route Map Debug Logging (if debug)
    # -------------------------------------------
    for rule in app.url_map.iter_rules():
        log_debug_message(
            f"[ROUTE MAP] rule: {rule}, endpoint: {rule.endpoint}, methods: {rule.methods}"
        )
    log_debug_message("---- Registered routes ----")
    for rule in app.url_map.iter_rules():
        log_debug_message(f"{rule.endpoint:30} {rule}")
    log_debug_message("---------------------------")
