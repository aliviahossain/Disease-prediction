"""
API Rate Limiting and Security Middleware
Protects endpoints from abuse and implements security best practices
"""

from functools import wraps
from flask import request, jsonify
import time
from collections import defaultdict
from datetime import datetime, timedelta
import hashlib
import re


class RateLimiter:
    """
    Token bucket rate limiter for API endpoints.
    Implements per-IP and per-endpoint rate limiting.
    """
    
    def __init__(self):
        """Initialize rate limiter with storage for requests."""
        # Store: {identifier: [(timestamp, endpoint), ...]}
        self._requests = defaultdict(list)
        
        # Rate limit configurations
        self._limits = {
            'default': {'requests': 100, 'window': 60},  # 100 req/min
            'prediction': {'requests': 30, 'window': 60},  # 30 req/min
            'ml_analysis': {'requests': 20, 'window': 60},  # 20 req/min
            'report': {'requests': 10, 'window': 60},  # 10 req/min
        }
        
        print("✅ RateLimiter initialized")
    
    def _get_identifier(self, request_obj):
        """
        Get unique identifier for the request.
        
        Args:
            request_obj: Flask request object
            
        Returns:
            Unique identifier string
        """
        # Use IP address as identifier
        ip = request_obj.remote_addr or 'unknown'
        
        # Include user agent for better tracking
        user_agent = request_obj.headers.get('User-Agent', '')
        
        # Create hash of IP + user agent
        identifier = hashlib.md5(f"{ip}:{user_agent}".encode()).hexdigest()
        
        return identifier
    
    def _clean_old_requests(self, identifier, window):
        """
        Remove requests outside the time window.
        
        Args:
            identifier: Request identifier
            window: Time window in seconds
        """
        current_time = time.time()
        cutoff_time = current_time - window
        
        # Keep only requests within the window
        self._requests[identifier] = [
            (timestamp, endpoint) 
            for timestamp, endpoint in self._requests[identifier]
            if timestamp > cutoff_time
        ]
    
    def check_rate_limit(self, endpoint_type='default'):
        """
        Check if request is within rate limit.
        
        Args:
            endpoint_type: Type of endpoint (default, prediction, ml_analysis, report)
            
        Returns:
            Tuple of (allowed: bool, retry_after: int, remaining: int)
        """
        identifier = self._get_identifier(request)
        
        # Get rate limit config
        config = self._limits.get(endpoint_type, self._limits['default'])
        max_requests = config['requests']
        window = config['window']
        
        # Clean old requests
        self._clean_old_requests(identifier, window)
        
        # Count requests in current window
        current_requests = len(self._requests[identifier])
        
        # Check if limit exceeded
        if current_requests >= max_requests:
            # Calculate retry after time
            oldest_request = min(self._requests[identifier], key=lambda x: x[0])
            retry_after = int(window - (time.time() - oldest_request[0])) + 1
            
            return False, retry_after, 0
        
        # Add current request
        self._requests[identifier].append((time.time(), endpoint_type))
        
        # Calculate remaining requests
        remaining = max_requests - current_requests - 1
        
        return True, 0, remaining
    
    def get_stats(self):
        """
        Get rate limiter statistics.
        
        Returns:
            Dictionary with statistics
        """
        total_identifiers = len(self._requests)
        total_requests = sum(len(reqs) for reqs in self._requests.values())
        
        return {
            'total_identifiers': total_identifiers,
            'total_requests': total_requests,
            'limits': self._limits
        }


class SecurityValidator:
    """
    Security validation for API requests.
    Prevents common attacks like XSS, SQL injection, etc.
    """
    
    # Dangerous patterns
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>',
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
        print("✅ SecurityValidator initialized")
    
    def validate_input(self, data, field_name='input'):
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
                return False, f"Potential SQL injection detected in {field_name}"
        
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
        sanitized = re.sub(r'[<>"\']', '', str(text))
        
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
            is_valid, error = self.validate_input(symptom, 'symptom')
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
        if not re.match(r'^[a-zA-Z0-9\s_-]+$', disease):
            return False, "Invalid disease name format"
        
        return True, None


# Global instances
rate_limiter = RateLimiter()
security_validator = SecurityValidator()


def rate_limit(endpoint_type='default'):
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
            allowed, retry_after, remaining = rate_limiter.check_rate_limit(endpoint_type)
            
            if not allowed:
                response = jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Too many requests. Please try again in {retry_after} seconds.',
                    'retry_after': retry_after
                })
                response.status_code = 429
                response.headers['Retry-After'] = str(retry_after)
                response.headers['X-RateLimit-Remaining'] = '0'
                return response
            
            # Add rate limit headers
            response = f(*args, **kwargs)
            
            # Add headers if response is a Flask response object
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Remaining'] = str(remaining)
                response.headers['X-RateLimit-Limit'] = str(
                    rate_limiter._limits[endpoint_type]['requests']
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
            except Exception as e:
                return jsonify({
                    'error': 'Invalid JSON',
                    'message': 'Request body must be valid JSON'
                }), 400
            
            if not data:
                return jsonify({
                    'error': 'No data provided',
                    'message': 'Request body is empty'
                }), 400
            
            # Check required fields
            if required_fields:
                missing_fields = [
                    field for field in required_fields 
                    if field not in data
                ]
                
                if missing_fields:
                    return jsonify({
                        'error': 'Missing required fields',
                        'missing_fields': missing_fields
                    }), 400
            
            # Validate all fields
            allowed_fields = set(required_fields or []) | set(optional_fields or [])
            
            for field, value in data.items():
                # Check if field is allowed
                if allowed_fields and field not in allowed_fields:
                    return jsonify({
                        'error': 'Invalid field',
                        'message': f'Field "{field}" is not allowed'
                    }), 400
                
                # Validate field value
                is_valid, error = security_validator.validate_input(value, field)
                if not is_valid:
                    return jsonify({
                        'error': 'Security validation failed',
                        'message': error
                    }), 400
            
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
        if hasattr(response, 'headers'):
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        
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
        print(f"[{datetime.now().isoformat()}] {request.method} {request.path} "
              f"from {request.remote_addr}")
        
        # Execute function
        start_time = time.time()
        response = f(*args, **kwargs)
        duration = time.time() - start_time
        
        # Log response
        status_code = response.status_code if hasattr(response, 'status_code') else 200
        print(f"[{datetime.now().isoformat()}] Response: {status_code} "
              f"({duration:.3f}s)")
        
        return response
    
    return decorated_function
