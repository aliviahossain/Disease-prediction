import os
import time
import threading
import sqlite3
from unittest import mock
import pytest
from flask import Flask

from backend.middleware.security import (
    RateLimiter,
    InMemoryBackend,
    SQLiteBackend,
    RedisBackend
)

# Set up a mock request context for identifier generation tests
app = Flask(__name__)


def test_in_memory_backend_basic():
    """Test basic functionality of InMemoryBackend."""
    backend = InMemoryBackend(cleanup_interval=10)
    try:
        identifier = "test_ip_1"
        endpoint = "prediction"
        max_requests = 3
        window = 2

        # First request
        allowed, retry_after, remaining = backend.check_rate_limit(
            identifier, endpoint, max_requests, window
        )
        assert allowed is True
        assert retry_after == 0
        assert remaining == 2

        # Second request
        allowed, retry_after, remaining = backend.check_rate_limit(
            identifier, endpoint, max_requests, window
        )
        assert allowed is True
        assert remaining == 1

        # Third request
        allowed, retry_after, remaining = backend.check_rate_limit(
            identifier, endpoint, max_requests, window
        )
        assert allowed is True
        assert remaining == 0

        # Fourth request should be blocked
        allowed, retry_after, remaining = backend.check_rate_limit(
            identifier, endpoint, max_requests, window
        )
        assert allowed is False
        assert retry_after > 0
        assert remaining == 0
    finally:
        backend.stop()


def test_in_memory_backend_sliding_window():
    """Test that requests outside the window expire correctly."""
    backend = InMemoryBackend(cleanup_interval=10)
    try:
        identifier = "test_ip_2"
        endpoint = "default"
        max_requests = 2
        window = 1

        allowed, _, _ = backend.check_rate_limit(identifier, endpoint, max_requests, window)
        assert allowed is True

        allowed, _, _ = backend.check_rate_limit(identifier, endpoint, max_requests, window)
        assert allowed is True

        # Third request immediately should be blocked
        allowed, _, _ = backend.check_rate_limit(identifier, endpoint, max_requests, window)
        assert allowed is False

        # Wait for window to expire
        time.sleep(1.1)

        # Should be allowed again
        allowed, _, remaining = backend.check_rate_limit(identifier, endpoint, max_requests, window)
        assert allowed is True
        assert remaining == 1
    finally:
        backend.stop()


def test_in_memory_backend_cleanup():
    """Test that stale entries are automatically cleaned up from in-memory backend."""
    backend = InMemoryBackend(cleanup_interval=10)
    try:
        identifier = "stale_ip"
        backend.check_rate_limit(identifier, "default", 5, 60)
        
        # Verify it was added
        assert identifier in backend._requests
        
        # Mock time forward beyond max_window (300s)
        with mock.patch("time.time", return_value=time.time() + 301):
            backend.prune_stale_entries()
            
        # Verify it has been cleaned up completely (deleted from dict)
        assert identifier not in backend._requests
    finally:
        backend.stop()


def test_sqlite_backend_basic(tmp_path):
    """Test SQLiteBackend basic functionality."""
    db_file = tmp_path / "rate_limit_test.db"
    backend = SQLiteBackend(db_path=str(db_file), cleanup_interval=10)
    try:
        identifier = "test_sqlite_ip"
        endpoint = "report"
        max_requests = 2
        window = 5

        # First request
        allowed, retry_after, remaining = backend.check_rate_limit(
            identifier, endpoint, max_requests, window
        )
        assert allowed is True
        assert remaining == 1

        # Second request
        allowed, retry_after, remaining = backend.check_rate_limit(
            identifier, endpoint, max_requests, window
        )
        assert allowed is True
        assert remaining == 0

        # Third request should be blocked
        allowed, retry_after, remaining = backend.check_rate_limit(
            identifier, endpoint, max_requests, window
        )
        assert allowed is False
        assert retry_after > 0
    finally:
        backend.stop()


def test_sqlite_backend_cleanup(tmp_path):
    """Test SQLiteBackend cleanup of stale entries."""
    db_file = tmp_path / "rate_limit_test_cleanup.db"
    backend = SQLiteBackend(db_path=str(db_file), cleanup_interval=10)
    try:
        identifier = "stale_sqlite_ip"
        backend.check_rate_limit(identifier, "default", 5, 60)
        
        # Verify record exists in DB
        with backend._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM rate_limits WHERE identifier = ?", (identifier,))
            assert cursor.fetchone()[0] == 1
            
        # Mock time forward beyond max_window
        with mock.patch("time.time", return_value=time.time() + 301):
            backend.prune_stale_entries()
            
        # Verify record is deleted
        with backend._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM rate_limits WHERE identifier = ?", (identifier,))
            assert cursor.fetchone()[0] == 0
    finally:
        backend.stop()


def test_redis_backend_lua_mock():
    """Test RedisBackend using mock Redis client executing Lua script."""
    mock_redis = mock.MagicMock()
    mock_script = mock.MagicMock()
    
    # We mock self._lua_script to return a mock rate limit evaluation:
    # allowed=1 (True), retry_after=0, remaining=5
    mock_script.return_value = (1, 0, 5)
    mock_redis.register_script.return_value = mock_script

    # Mock the redis module inside security
    mock_redis_module = mock.MagicMock()
    mock_redis_module.from_url.return_value = mock_redis

    with mock.patch("backend.middleware.security.redis", mock_redis_module):
        backend = RedisBackend(redis_url="redis://dummy:6379/0")
        
        allowed, retry_after, remaining = backend.check_rate_limit(
            "dummy_ip", "default", 10, 60
        )
        
        assert allowed is True
        assert retry_after == 0
        assert remaining == 5
        
        # Verify register_script was called with LUA_RATE_LIMIT script
        mock_redis.register_script.assert_called_once_with(backend.LUA_RATE_LIMIT)
        # Verify the registered script was called with correct keys & args
        mock_script.assert_called_once()
        call_kwargs = mock_script.call_args[1]
        assert "keys" in call_kwargs
        assert call_kwargs["keys"] == ["rate_limit:dummy_ip:default"]
        assert call_kwargs["args"][1] == 60  # window
        assert call_kwargs["args"][2] == 10  # max_requests


@mock.patch.dict(os.environ, {"RATE_LIMIT_BACKEND": "in_memory"})
def test_rate_limiter_load_in_memory():
    """Test that RateLimiter initializes InMemoryBackend by default or when configured."""
    limiter = RateLimiter()
    assert isinstance(limiter.backend, InMemoryBackend)
    limiter.backend.stop()


@mock.patch.dict(os.environ, {"RATE_LIMIT_BACKEND": "sqlite", "RATE_LIMIT_DB_PATH": "backend/rate_limit_test.db"})
def test_rate_limiter_load_sqlite():
    """Test that RateLimiter initializes SQLiteBackend when configured."""
    limiter = RateLimiter()
    try:
        assert isinstance(limiter.backend, SQLiteBackend)
        assert limiter.backend.db_path == "backend/rate_limit_test.db"
    finally:
        limiter.backend.stop()
        if os.path.exists("backend/rate_limit_test.db"):
            try:
                os.remove("backend/rate_limit_test.db")
            except Exception:
                pass


@mock.patch.dict(os.environ, {"RATE_LIMIT_BACKEND": "redis", "REDIS_URL": "redis://localhost:6379/0"})
def test_rate_limiter_load_redis_fallback():
    """Test that RateLimiter falls back to InMemoryBackend if Redis connection/initialization fails."""
    mock_redis = mock.MagicMock()
    mock_redis.from_url.side_effect = Exception("Redis connection error")
    with mock.patch("backend.middleware.security.redis", mock_redis):
        limiter = RateLimiter()
        # Should print warning and fall back to InMemoryBackend
        assert isinstance(limiter.backend, InMemoryBackend)
        limiter.backend.stop()
