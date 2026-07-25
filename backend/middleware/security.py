import hashlib
import os
import re
import sqlite3
import threading
import time
from collections import defaultdict
from datetime import datetime
from functools import wraps

from flask import jsonify, request

try:
    import redis
except ImportError:
    redis = None


class InMemoryBackend:
    """
    Thread-safe in-memory rate limit backend.
    Uses a background thread to prune stale entries periodically.
    """

    def __init__(self, cleanup_interval=60):
        self._requests = defaultdict(list)
        self._lock = threading.Lock()
        self._cleanup_interval = cleanup_interval
        self._stop_cleanup = threading.Event()
        self._cleanup_thread = threading.Thread(
            target=self._periodic_cleanup, daemon=True
        )
        self._cleanup_thread.start()

    def _periodic_cleanup(self):
        while not self._stop_cleanup.wait(self._cleanup_interval):
            try:
                self.prune_stale_entries()
            except Exception as e:
                print(f"Error in InMemoryBackend periodic cleanup: {e}")

    def prune_stale_entries(self):
        current_time = time.time()
        # Keep buffer of 5 minutes (300 seconds) max window
        max_window = 300
        with self._lock:
            for identifier in list(self._requests.keys()):
                cutoff = current_time - max_window
                self._requests[identifier] = [
                    (ts, ep)
                    for ts, ep in self._requests[identifier]
                    if ts > cutoff
                ]
                if not self._requests[identifier]:
                    del self._requests[identifier]

    def check_rate_limit(
        self, identifier, endpoint_type, max_requests, window
    ):
        current_time = time.time()
        cutoff_time = current_time - window

        with self._lock:
            # Clean old requests
            self._requests[identifier] = [
                (ts, ep)
                for ts, ep in self._requests[identifier]
                if ts > cutoff_time
            ]

            # Count requests in window
            current_requests = len(self._requests[identifier])

            # Check if limit exceeded
            if current_requests >= max_requests:
                oldest_request = min(
                    self._requests[identifier], key=lambda x: x[0]
                )
                retry_after = (
                    int(window - (current_time - oldest_request[0])) + 1
                )
                return False, retry_after, 0

            # Add current request
            self._requests[identifier].append((current_time, endpoint_type))
            remaining = max_requests - current_requests - 1

            return True, 0, remaining

    def get_stats(self):
        with self._lock:
            total_identifiers = len(self._requests)
            total_requests = sum(len(reqs) for reqs in self._requests.values())

        return {
            "total_identifiers": total_identifiers,
            "total_requests": total_requests,
        }

    def stop(self):
        self._stop_cleanup.set()


class RedisBackend:
    """
    Distributed Redis rate limit backend using TTL-based keys and an atomic Lua script.  # noqa: E501
    """

    LUA_RATE_LIMIT = """
    local key = KEYS[1]
    local now = tonumber(ARGV[1])
    local window = tonumber(ARGV[2])
    local max_requests = tonumber(ARGV[3])
    local endpoint_type = ARGV[4]

    local cutoff = now - window
    redis.call('ZREMRANGEBYSCORE', key, '-inf', cutoff)
    local current_requests = redis.call('ZCARD', key)

    if current_requests >= max_requests then
        local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
        local retry_after = 0
        if oldest[2] then
            retry_after = math.max(0, math.floor(window - (now - tonumber(oldest[2])))) + 1  # noqa: E501
        else
            retry_after = math.max(0, math.floor(window)) + 1
        end
        return {0, retry_after, 0}
    else
        redis.call('ZADD', key, now, now .. ":" .. endpoint_type)
        redis.call('EXPIRE', key, math.ceil(window))
        local remaining = max_requests - current_requests - 1
        return {1, 0, remaining}
    end
    """

    def __init__(self, redis_url="redis://localhost:6379/0"):
        if redis is None:
            raise ImportError(
                "The 'redis' package is required to use the Redis rate limit backend."  # noqa: E501
            )
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self._lua_script = self.redis_client.register_script(
            self.LUA_RATE_LIMIT
        )

    def check_rate_limit(
        self, identifier, endpoint_type, max_requests, window
    ):
        key = f"rate_limit:{identifier}:{endpoint_type}"
        current_time = time.time()

        allowed, retry_after, remaining = self._lua_script(
            keys=[key],
            args=[current_time, window, max_requests, endpoint_type],
        )

        return bool(allowed), int(retry_after), int(remaining)

    def get_stats(self):
        try:
            keys = self.redis_client.keys("rate_limit:*")
            total_identifiers = len(set(k.split(":")[1] for k in keys))
            total_requests = sum(self.redis_client.zcard(k) for k in keys)
        except Exception:
            total_identifiers = 0
            total_requests = 0

        return {
            "total_identifiers": total_identifiers,
            "total_requests": total_requests,
        }


class SQLiteBackend:
    """
    SQLite-based rate limit backend.
    Uses WAL mode for high concurrency support among Gunicorn workers.
    """

    def __init__(self, db_path="backend/rate_limit.db", cleanup_interval=60):
        self.db_path = db_path
        self._init_db()
        self._cleanup_interval = cleanup_interval
        self._stop_cleanup = threading.Event()
        self._cleanup_thread = threading.Thread(
            target=self._periodic_cleanup, daemon=True
        )
        self._cleanup_thread.start()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS rate_limits (
                    identifier TEXT,
                    endpoint_type TEXT,
                    timestamp REAL
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_rate_limits "
                "ON rate_limits (identifier, endpoint_type, timestamp)"
            )
            conn.commit()

    def _periodic_cleanup(self):
        while not self._stop_cleanup.wait(self._cleanup_interval):
            try:
                self.prune_stale_entries()
            except Exception as e:
                print(f"Error in SQLiteBackend periodic cleanup: {e}")

    def prune_stale_entries(self):
        cutoff = time.time() - 300  # 5 minutes buffer
        with self._get_connection() as conn:
            conn.execute(
                "DELETE FROM rate_limits WHERE timestamp < ?", (cutoff,)
            )
            conn.commit()

    def check_rate_limit(
        self, identifier, endpoint_type, max_requests, window
    ):
        current_time = time.time()
        cutoff_time = current_time - window

        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Clean old records for this identifier
            cursor.execute(
                "DELETE FROM rate_limits WHERE identifier = ? AND timestamp < ?",  # noqa: E501
                (identifier, cutoff_time),
            )

            # Count requests in window
            cursor.execute(
                "SELECT COUNT(*) FROM rate_limits "
                "WHERE identifier = ? AND endpoint_type = ? AND timestamp > ?",
                (identifier, endpoint_type, cutoff_time),
            )
            current_requests = cursor.fetchone()[0]

            if current_requests >= max_requests:
                cursor.execute(
                    "SELECT MIN(timestamp) FROM rate_limits "
                    "WHERE identifier = ? AND endpoint_type = ? AND timestamp > ?",  # noqa: E501
                    (identifier, endpoint_type, cutoff_time),
                )
                oldest_timestamp = cursor.fetchone()[0]
                if oldest_timestamp:
                    retry_after = (
                        int(window - (current_time - oldest_timestamp)) + 1
                    )
                else:
                    retry_after = int(window) + 1
                return False, retry_after, 0

            # Insert current request
            cursor.execute(
                "INSERT INTO rate_limits (identifier, endpoint_type, timestamp) "  # noqa: E501
                "VALUES (?, ?, ?)",
                (identifier, endpoint_type, current_time),
            )
            conn.commit()

            remaining = max_requests - current_requests - 1
            return True, 0, remaining

    def get_stats(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(DISTINCT identifier) FROM rate_limits"
            )
            total_identifiers = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM rate_limits")
            total_requests = cursor.fetchone()[0]

        return {
            "total_identifiers": total_identifiers,
            "total_requests": total_requests,
        }

    def stop(self):
        self._stop_cleanup.set()


class RateLimiter:
    """
    Token bucket rate limiter for API endpoints.
    Implements per-IP and per-endpoint rate limiting using pluggable backends.
    """

    def __init__(self):
        """Initialize rate limiter with configured backend selection."""
        # Rate limit configurations
        self._limits = {
            "default": {"requests": 100, "window": 60},  # 100 req/min
            "prediction": {"requests": 30, "window": 60},  # 30 req/min
            "ml_analysis": {"requests": 20, "window": 60},  # 20 req/min
            "report": {"requests": 10, "window": 60},  # 10 req/min
            "gemini": {"requests": 5, "window": 3600},  # 5 req/hour for Gemini API
        }

        # Pluggable backend selection
        backend_type = os.getenv("RATE_LIMIT_BACKEND", "in_memory").lower()

        if backend_type == "redis":
            try:
                redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
                self.backend = RedisBackend(redis_url=redis_url)
                print(f"[OK] RateLimiter using Redis backend ({redis_url})")
            except Exception as e:
                print(
                    f"[WARN] Failed to initialize Redis backend: {e}. Falling back to in_memory."  # noqa: E501
                )
                self.backend = InMemoryBackend()
        elif backend_type == "sqlite":
            db_path = os.getenv("RATE_LIMIT_DB_PATH", "backend/rate_limit.db")
            self.backend = SQLiteBackend(db_path=db_path)
            print(f"[OK] RateLimiter using SQLite backend ({db_path})")
        else:
            self.backend = InMemoryBackend()
            print("[OK] RateLimiter using InMemory backend")

        print("[OK] RateLimiter initialized")

    def _get_identifier(self, request_obj):
        """
        Get unique identifier for the request.

        The identifier is based solely on the client IP address.
        Using User-Agent as part of the key allowed trivial bypass
        by rotating the User-Agent header on each request.

        For authenticated requests the Authorization header value is
        also incorporated so that legitimate per-user rate limits work
        correctly when multiple users share an egress IP.

        Args:
            request_obj: Flask request object

        Returns:
            Unique identifier string
        """
        ip = request_obj.remote_addr or "unknown"

        # Include an authenticated session token when present so that
        # per-user limits are enforced even behind a shared NAT, while
        # keeping the identifier opaque (hashed, never stored in clear).
        auth_token = request_obj.headers.get("Authorization", "")

        if auth_token:
            identifier = hashlib.sha256(
                f"{ip}:{auth_token}".encode()
            ).hexdigest()
        else:
            identifier = hashlib.sha256(ip.encode()).hexdigest()

        return identifier

    def check_rate_limit(self, endpoint_type="default"):
        """
        Check if request is within rate limit.

        Args:
            endpoint_type: Type of endpoint (default, prediction, ml_analysis, report)  # noqa: E501

        Returns:
            Tuple of (allowed: bool, retry_after: int, remaining: int)
        """
        identifier = self._get_identifier(request)

        # Get rate limit config
        config = self._limits.get(endpoint_type, self._limits["default"])
        max_requests = config["requests"]
        window = config["window"]

        return self.backend.check_rate_limit(
            identifier, endpoint_type, max_requests, window
        )

    def get_stats(self):
        """
        Get rate limiter statistics.

        Returns:
            Dictionary with statistics
        """
        stats = self.backend.get_stats()
        stats["limits"] = self._limits
        stats["backend"] = self.backend.__class__.__name__
        return stats


class SecurityValidator:
    """
    Security validation for API requests.
    Prevents common attacks like XSS, SQL injection, etc.
    """

    # Dangerous patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
    ]

    SQL_PATTERNS = [
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\bSELECT\b.*\bFROM\b)",
        r"(\bINSERT\b.*\bINTO\b)",
        r"(\bDROP\b.*\bTABLE\b)",
        r"(\bDELETE\b.*\bFROM\b)",
    ]

    def __init__(self):
        """Initialize security validator."""
        print("[OK] SecurityValidator initialized")

    def validate_input(self, data, field_name="input"):
        """
        Validate input data for security threats.

        Args:
            data: Input data to validate
            field_name: Name of the field being validated

        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        if not data:
            return True, None

        data_str = str(data)

        # Check for XSS
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, data_str, re.IGNORECASE):
                return False, f"Potential XSS attack detected in {field_name}"

        # Check for SQL injection
        for pattern in self.SQL_PATTERNS:
            if re.search(pattern, data_str, re.IGNORECASE):
                return (
                    False,
                    f"Potential SQL injection detected in {field_name}",
                )

        return True, None

    def sanitize_string(self, text):
        """
        Sanitize string input.

        Args:
            text: Input text

        Returns:
            Sanitized text
        """
        if not text:
            return ""

        # Remove dangerous characters
        sanitized = re.sub(r'[<>"\']', "", str(text))

        # Limit length
        max_length = 1000
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        return sanitized.strip()

    def validate_symptoms(self, symptoms):
        """
        Validate symptom list.

        Args:
            symptoms: List of symptoms

        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        if not isinstance(symptoms, list):
            return False, "Symptoms must be a list"

        if len(symptoms) == 0:
            return False, "At least one symptom is required"

        if len(symptoms) > 50:
            return False, "Too many symptoms (maximum 50)"

        # Validate each symptom
        for symptom in symptoms:
            if not isinstance(symptom, str):
                return False, "Each symptom must be a string"

            if len(symptom) > 100:
                return False, f"Symptom too long: {symptom[:50]}..."

            # Check for dangerous patterns
            is_valid, error = self.validate_input(symptom, "symptom")
            if not is_valid:
                return False, error

        return True, None

    def validate_disease_name(self, disease):
        """
        Validate disease name.

        Args:
            disease: Disease name

        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        if not disease:
            return False, "Disease name is required"

        if not isinstance(disease, str):
            return False, "Disease name must be a string"

        if len(disease) > 100:
            return False, "Disease name too long"

        # Only allow alphanumeric, spaces, underscores, and hyphens
        if not re.match(r"^[a-zA-Z0-9\s_-]+$", disease):
            return False, "Invalid disease name format"

        return True, None


# Global instances
rate_limiter = RateLimiter()
security_validator = SecurityValidator()


def rate_limit(endpoint_type="default"):
    """
    Decorator for rate limiting endpoints.

    Args:
        endpoint_type: Type of endpoint for rate limiting

    Example:
        @app.route('/api/predict')
        @rate_limit('prediction')
        def predict():
            pass
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check rate limit
            allowed, retry_after, remaining = rate_limiter.check_rate_limit(
                endpoint_type
            )

            if not allowed:
                response = jsonify(
                    {
                        "error": "Rate limit exceeded",
                        "message": f"Too many requests. Please try again in {retry_after} seconds.",  # noqa: E501
                        "retry_after": retry_after,
                    }
                )
                response.status_code = 429
                response.headers["Retry-After"] = str(retry_after)
                response.headers["X-RateLimit-Remaining"] = "0"
                return response

            # Add rate limit headers
            response = f(*args, **kwargs)

            # Add headers if response is a Flask response object
            if hasattr(response, "headers"):
                response.headers["X-RateLimit-Remaining"] = str(remaining)
                response.headers["X-RateLimit-Limit"] = str(
                    rate_limiter._limits[endpoint_type]["requests"]
                )

            return response

        return decorated_function

    return decorator


def validate_request_data(required_fields=None, optional_fields=None):
    """
    Decorator for validating request data.

    Args:
        required_fields: List of required field names
        optional_fields: List of optional field names

    Example:
        @app.route('/api/predict', methods=['POST'])
        @validate_request_data(required_fields=['disease', 'symptoms'])
        def predict():
            pass
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get JSON data
            try:
                data = request.get_json()
            except Exception:
                return (
                    jsonify(
                        {
                            "error": "Invalid JSON",
                            "message": "Request body must be valid JSON",
                        }
                    ),
                    400,
                )

            if not data:
                return (
                    jsonify(
                        {
                            "error": "No data provided",
                            "message": "Request body is empty",
                        }
                    ),
                    400,
                )

            # Check required fields
            if required_fields:
                missing_fields = [
                    field for field in required_fields if field not in data
                ]

                if missing_fields:
                    return (
                        jsonify(
                            {
                                "error": "Missing required fields",
                                "missing_fields": missing_fields,
                            }
                        ),
                        400,
                    )

            # Validate all fields
            allowed_fields = set(required_fields or []) | set(
                optional_fields or []
            )

            for field, value in data.items():
                # Check if field is allowed
                if allowed_fields and field not in allowed_fields:
                    return (
                        jsonify(
                            {
                                "error": "Invalid field",
                                "message": f'Field "{field}" is not allowed',
                            }
                        ),
                        400,
                    )

                # Validate field value
                is_valid, error = security_validator.validate_input(
                    value, field
                )
                if not is_valid:
                    return (
                        jsonify(
                            {
                                "error": "Security validation failed",
                                "message": error,
                            }
                        ),
                        400,
                    )

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def cors_headers(f):
    """
    Decorator to add CORS headers to response.

    Example:
        @app.route('/api/data')
        @cors_headers
        def get_data():
            pass
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)

        # Add CORS headers if response is a Flask response object
        if hasattr(response, "headers"):
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, PUT, DELETE, OPTIONS"
            )
            response.headers["Access-Control-Allow-Headers"] = (
                "Content-Type, Authorization"
            )

        return response

    return decorated_function


def log_request(f):
    """
    Decorator to log API requests.

    Example:
        @app.route('/api/predict')
        @log_request
        def predict():
            pass
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Log request
        print(
            f"[{datetime.now().isoformat()}] {request.method} {request.path} "
            f"from {request.remote_addr}"
        )

        # Execute function
        start_time = time.time()
        response = f(*args, **kwargs)
        duration = time.time() - start_time

        # Log response
        status_code = (
            response.status_code if hasattr(response, "status_code") else 200
        )
        print(
            f"[{datetime.now().isoformat()}] Response: {status_code} ({duration:.3f}s)"  # noqa: E501
        )

        return response

    return decorated_function
