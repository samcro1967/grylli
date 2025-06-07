"""
# ---------------------------------------------------------------------
# rate_limit.py
# app/utils/rate_limit.py
# Reusable soft rate-limiting logic for authentication-related views.
# Tracks failures per key (username or email) and adds delay after threshold.
# ---------------------------------------------------------------------
"""

import time

# ---------------------------------------------------------------------
# Module-level in-memory failure tracker
# ---------------------------------------------------------------------
_failure_tracker = {}

_MAX_FREE_ATTEMPTS = 3
_LOCKOUT_DURATION = 30


# ---------------------------------------------------------------------
# Function: record_failure
# ---------------------------------------------------------------------
def record_failure(key):
    """
    Record a failed attempt for the given key (username or email).

    Args:
        key (str): Identifier to track (e.g., username or email).
    """
    now = time.time()
    entry = _failure_tracker.get(key, {"count": 0, "last": now})
    entry["count"] += 1
    entry["last"] = now
    _failure_tracker[key] = entry


# ---------------------------------------------------------------------
# Function: get_delay_seconds
# ---------------------------------------------------------------------
def get_delay_seconds(key):
    entry = _failure_tracker.get(key)
    if not entry:
        return 0
    if entry["count"] <= _MAX_FREE_ATTEMPTS:
        return 0
    elapsed = time.time() - entry["last"]
    return max(0, _LOCKOUT_DURATION - elapsed)


# ---------------------------------------------------------------------
# Function: reset_failures
# ---------------------------------------------------------------------
def reset_failures(key):
    """
    Reset the failure count for the given key (e.g., after successful auth).

    Args:
        key (str): Identifier to reset (e.g., username or email).
    """
    _failure_tracker.pop(key, None)
