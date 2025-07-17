# ---------------------------------------------------------------------
# rate_limit.py
# app/utils/rate_limit.py
# Reusable soft rate-limiting logic for authentication-related views.
# Tracks failures per key (username or email) and adds delay after threshold.
# ---------------------------------------------------------------------

from collections import defaultdict
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------
FAILED_ATTEMPTS = defaultdict(list)  # {identifier: [datetime1, datetime2, ...]}

MAX_FAILURE_WINDOW_SECONDS = 900  # 15 minutes
MAX_FREE_ATTEMPTS = 3  # No delay before this many attempts
LOCKOUT_DELAY_SHORT = 10  # Delay after 5+ attempts
LOCKOUT_DELAY_LONG = 30  # Delay after 8+ attempts


# ---------------------------------------------------------------------
# Function: record_failure
# ---------------------------------------------------------------------
def record_failure(identifier):
    """Record a failed attempt timestamp for a given identifier."""
    FAILED_ATTEMPTS[identifier].append(datetime.now(timezone.utc))


# ---------------------------------------------------------------------
# Function: reset_failures
# ---------------------------------------------------------------------
def reset_failures(identifier):
    """Clear all recorded failures for a given identifier."""
    if identifier in FAILED_ATTEMPTS:
        del FAILED_ATTEMPTS[identifier]


# ---------------------------------------------------------------------
# Function: get_failure_count
# ---------------------------------------------------------------------
def get_failure_count(identifier):
    """
    Return the number of recent failures for this identifier within the sliding window.
    """
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(seconds=MAX_FAILURE_WINDOW_SECONDS)
    recent_failures = [ts for ts in FAILED_ATTEMPTS.get(identifier, []) if ts > window_start]
    FAILED_ATTEMPTS[identifier] = recent_failures  # Prune old timestamps
    return len(recent_failures)


# ---------------------------------------------------------------------
# Function: get_delay_seconds
# ---------------------------------------------------------------------
def get_delay_seconds(identifier):
    """
    Return a delay in seconds based on failure count thresholds.
    """
    count = get_failure_count(identifier)
    if count >= 8:
        return LOCKOUT_DELAY_LONG
    if count >= 5:
        return LOCKOUT_DELAY_SHORT
    return 0
