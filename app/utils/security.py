"""
# ---------------------------------------------------------------------
# security.py
# app/utils/security.py
# File listing utility for allowed uploads (non-hidden, filtered by extension).
# ---------------------------------------------------------------------
"""

from urllib.parse import urljoin, urlparse

from flask import request, url_for


def is_safe_url(target):
    """
    Returns True if the URL is relative or local (same scheme and host).
    """
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


def get_safe_redirect(target, fallback_endpoint="home.index", **fallback_kwargs):
    """
    Returns a safe redirect URL. If the target is not same-origin or is suspicious,
    fallback to a safe endpoint.
    """

    # 🛡 Block dangerous protocol-relative URLs (e.g., //evil.com)
    if not target or target.startswith("//"):
        return url_for(fallback_endpoint, **fallback_kwargs)

    # 🛡 Validate the target is local or same-origin
    if is_safe_url(target):
        return target

    return url_for(fallback_endpoint, **fallback_kwargs)
