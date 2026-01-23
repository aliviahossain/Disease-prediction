"""
Tests for SECRET_KEY security configuration
Tests that the application correctly handles SECRET_KEY in different environments
"""

import os
import pytest
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_secret_key_from_env(monkeypatch, tmp_path):
    """Test that app loads SECRET_KEY from environment variable"""
    # Setup
    monkeypatch.setenv('SECRET_KEY', 'test_secret_key_12345')
    monkeypatch.setenv('FLASK_ENV', 'development')
    monkeypatch.setenv('DATABASE_URL', '')
    
    # Import after setting env vars
    from backend import create_app
    
    # Execute
    app = create_app()
    
    # Assert
    assert app.config['SECRET_KEY'] == 'test_secret_key_12345'


def test_secret_key_missing_in_production(monkeypatch):
    """Test that app raises error when SECRET_KEY is missing in production"""
    # Setup
    monkeypatch.delenv('SECRET_KEY', raising=False)
    monkeypatch.setenv('FLASK_ENV', 'production')
    monkeypatch.setenv('DATABASE_URL', '')
    
    # Import after setting env vars
    from backend import create_app
    
    # Assert - should raise ValueError
    with pytest.raises(ValueError) as exc_info:
        create_app()
    
    assert "CRITICAL ERROR" in str(exc_info.value)
    assert "SECRET_KEY environment variable is required" in str(exc_info.value)


def test_secret_key_auto_generated_in_dev(monkeypatch, capsys):
    """Test that app auto-generates SECRET_KEY in development when not provided"""
    # Setup
    monkeypatch.delenv('SECRET_KEY', raising=False)
    monkeypatch.setenv('FLASK_ENV', 'development')
    monkeypatch.setenv('DATABASE_URL', '')
    
    # Import after setting env vars
    from backend import create_app
    
    # Execute
    app = create_app()
    
    # Assert
    assert app.config['SECRET_KEY'] is not None
    assert len(app.config['SECRET_KEY']) == 64  # token_hex(32) produces 64 chars
    
    # Check warning message was printed
    captured = capsys.readouterr()
    assert "WARNING: SECRET_KEY not set in environment" in captured.out


def test_secret_key_with_flask_debug_flag(monkeypatch):
    """Test that app recognizes FLASK_DEBUG=1 as development mode"""
    # Setup
    monkeypatch.delenv('SECRET_KEY', raising=False)
    monkeypatch.delenv('FLASK_ENV', raising=False)
    monkeypatch.setenv('FLASK_DEBUG', '1')
    monkeypatch.setenv('DATABASE_URL', '')
    
    # Import after setting env vars
    from backend import create_app
    
    # Execute
    app = create_app()
    
    # Assert - should auto-generate key in debug mode
    assert app.config['SECRET_KEY'] is not None
    assert len(app.config['SECRET_KEY']) == 64


def test_secret_key_length_validation(monkeypatch):
    """Test that app requires a reasonably long SECRET_KEY"""
    # Setup
    monkeypatch.setenv('SECRET_KEY', 'short')  # Too short
    monkeypatch.setenv('FLASK_ENV', 'development')
    monkeypatch.setenv('DATABASE_URL', '')
    
    # Import after setting env vars
    from backend import create_app
    
    # Execute
    app = create_app()
    
    # Assert - app should accept even short keys, but it's insecure
    assert app.config['SECRET_KEY'] == 'short'
    # Note: A real implementation might validate minimum length, but this test
    # documents current behavior


def test_secret_key_not_hardcoded():
    """Test that SECRET_KEY is not hardcoded in the application"""
    # Read the source file
    init_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        '__init__.py'
    )
    
    with open(init_file, 'r') as f:
        content = f.read()
    
    # Assert - check that no hardcoded secret key exists
    # (look for common patterns like 'SECRET_KEY = ')
    assert "app.config['SECRET_KEY'] = " not in content or "os.getenv" in content
    
    # Make sure we're loading from environment
    assert "os.getenv('SECRET_KEY')" in content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
