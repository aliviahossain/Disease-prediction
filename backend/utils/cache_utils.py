"""
Cache key utilities for Flask-Caching.

Flask-Caching's default key_prefix is derived from the request path and
query string only.  When a view returns personalised data (prediction
results that incorporate the authenticated user's prior history, survival
probability, or Bayesian trend factor) caching with that default key
causes User A's result to be served to User B whenever they submit
identical inputs during the cached window.

Usage
-----
Import ``make_user_cache_key`` and pass it as the ``key_prefix`` argument
to ``@cache.cached``:

    from backend.utils.cache_utils import make_user_cache_key

    @bp.route("/api/ml/predict", methods=["POST"])
    @cache.cached(timeout=300, key_prefix=make_user_cache_key)
    def predict_disease():
        ...

The returned key includes:
- The request path
- A SHA-256 digest of the raw request body (so different payloads get
  different cache slots)
- The authenticated user's ID, or the string ``"anonymous"`` for
  unauthenticated requests

For endpoints that must never serve cached personal data to anonymous
callers, pair this helper with ``@login_required`` so the ``"anonymous"``
bucket is never populated.
"""

import hashlib

from flask import request
from flask_login import current_user


def make_user_cache_key() -> str:
    """
    Build a cache key that is unique per (path, request body, user).

    Prevents personalised prediction results from leaking across user
    sessions when Flask-Caching is enabled on a prediction endpoint.

    Returns
    -------
    str
        A cache key of the form
        ``view:<path>:body:<body_hash>:user:<user_id>``.
    """
    path = request.path

    # Hash the raw body so that different payloads map to different slots.
    # Using a digest rather than the raw body keeps the key short and safe
    # to use as a Redis / Memcached key.
    body = request.get_data()
    body_hash = hashlib.sha256(body).hexdigest()[:16]

    # Bind the key to the authenticated user so that User A's cached result
    # is never served to User B.  Anonymous callers get their own isolated
    # bucket; combine this helper with @login_required on personal endpoints
    # to prevent that bucket from being populated at all.
    if current_user and current_user.is_authenticated:
        user_part = str(current_user.id)
    else:
        user_part = "anonymous"

    return f"view:{path}:body:{body_hash}:user:{user_part}"
