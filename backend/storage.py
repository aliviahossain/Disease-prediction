"""
Central location for everything the app persists locally.

All persistent data lives in ONE dedicated folder (``database/`` at the repo
root by default):

    database/
    ├── disease_prediction.db   # users, password hashes, profiles,
    │                           # prediction history, dashboard history, ...
    └── .secret_key             # dev-only SECRET_KEY so logins survive restarts

The folder is git-ignored. Override its location with ``DATABASE_DIR``, or
point the app at an external database (PostgreSQL/MySQL) with ``DATABASE_URL``.
"""

import os
import secrets
import shutil

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_FILENAME = "disease_prediction.db"

# Pre-refactor locations, migrated automatically on first start.
_LEGACY_SQLITE_DB = os.path.join(REPO_ROOT, "backend", "site.db")
_LEGACY_DEV_SECRET_KEY = os.path.join(REPO_ROOT, "backend", ".dev_secret_key")


def get_database_dir():
    """Return the dedicated data folder, creating it if needed."""
    path = os.environ.get("DATABASE_DIR") or os.path.join(REPO_ROOT, "database")
    os.makedirs(path, exist_ok=True)
    return path


def get_sqlite_path():
    return os.path.join(get_database_dir(), DATABASE_FILENAME)


def _migrate_legacy_sqlite(target_path):
    """Copy the old backend/site.db into the new location once (never deletes it)."""
    if os.path.exists(target_path) or not os.path.exists(_LEGACY_SQLITE_DB):
        return
    # Only migrate into the default location; test/custom dirs start clean.
    if os.environ.get("DATABASE_DIR"):
        return
    shutil.copy2(_LEGACY_SQLITE_DB, target_path)
    print(f"[OK] Migrated existing data from {_LEGACY_SQLITE_DB} -> {target_path}")


def get_database_uri():
    """SQLAlchemy URI: DATABASE_URL if set, otherwise the local SQLite file."""
    database_url = (os.environ.get("DATABASE_URL") or "").strip()
    if database_url:
        # Heroku/Render style URLs use the deprecated "postgres://" scheme.
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        return database_url

    path = get_sqlite_path()
    _migrate_legacy_sqlite(path)
    return "sqlite:///" + path.replace("\\", "/")


def load_or_create_dev_secret_key():
    """Return a development SECRET_KEY that persists across restarts.

    A fresh random key on every start would invalidate all sessions, logging
    everyone out and breaking open pages with CSRF errors. Only used when
    SECRET_KEY is unset in development.
    """
    key_path = os.path.join(get_database_dir(), ".secret_key")
    for path in (key_path, _LEGACY_DEV_SECRET_KEY):
        try:
            with open(path, encoding="utf-8") as f:
                key = f.read().strip()
            if len(key) >= 32:
                if path != key_path:
                    _write_key(key_path, key)
                return key
        except OSError:
            pass

    key = secrets.token_hex(32)
    _write_key(key_path, key)
    return key


def _write_key(path, key):
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(key)
    except OSError as e:
        print(
            f"[WARN] Could not persist dev SECRET_KEY ({e}); sessions reset on restart."
        )
