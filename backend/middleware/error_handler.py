"""
Centralized Error Handling Middleware
Provides consistent error responses and logging across the application
"""

from flask import jsonify, request
from functools import wraps
import traceback
from datetime import datetime
import sys


class AppError(Exception):
    """Base exception class for application errors."""
    
    def __init__(self, message, status_code=500, payload=None):
        """
        Initialize application error.
        
        Args:
            message: Error message
            status_code: HTTP status code
            payload: Additional error data
        """
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload or {}
    
    def to_dict(self):
        """Convert error to dictionary."""
        error_dict = {
            'error': self.__class__.__name__,
            'message': self.message,
            'timestamp': datetime.now().isoformat()
        }
        error_dict.update(self.payload)
        return error_dict


class ValidationError(AppError):
    """Exception for validation errors."""
    
    def __init__(self, message, field=None, **kwargs):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            field: Field that failed validation
            **kwargs: Additional error data
        """
        payload = kwargs
        if field:
            payload['field'] = field
        super().__init__(message, status_code=400, payload=payload)


class NotFoundError(AppError):
    """Exception for resource not found errors."""
    
    def __init__(self, resource, resource_id=None):
        """
        Initialize not found error.
        
        Args:
            resource: Resource type (e.g., 'Disease', 'Patient')
            resource_id: Resource identifier
        """
        message = f"{resource} not found"
        if resource_id:
            message += f": {resource_id}"
        
        payload = {'resource': resource}
        if resource_id:
            payload['resource_id'] = resource_id
        
        super().__init__(message, status_code=404, payload=payload)


class UnauthorizedError(AppError):
    """Exception for unauthorized access errors."""
    
    def __init__(self, message="Unauthorized access"):
        """Initialize unauthorized error."""
        super().__init__(message, status_code=401)


class ForbiddenError(AppError):
    """Exception for forbidden access errors."""
    
    def __init__(self, message="Access forbidden"):
        """Initialize forbidden error."""
        super().__init__(message, status_code=403)


class RateLimitError(AppError):
    """Exception for rate limit exceeded errors."""
    
    def __init__(self, retry_after=60):
        """
        Initialize rate limit error.
        
        Args:
            retry_after: Seconds until retry is allowed
        """
        message = f"Rate limit exceeded. Try again in {retry_after} seconds."
        super().__init__(
            message, 
            status_code=429, 
            payload={'retry_after': retry_after}
        )


class PredictionError(AppError):
    """Exception for prediction/ML model errors."""
    
    def __init__(self, message, model_name=None):
        """
        Initialize prediction error.
        
        Args:
            message: Error message
            model_name: Name of the model that failed
        """
        payload = {}
        if model_name:
            payload['model'] = model_name
        super().__init__(message, status_code=500, payload=payload)


class ErrorHandler:
    """
    Centralized error handler for Flask application.
    """
    
    def __init__(self, app=None):
        """
        Initialize error handler.
        
        Args:
            app: Flask application instance
        """
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """
        Initialize error handlers for Flask app.
        
        Args:
            app: Flask application instance
        """
        # Register error handlers
        app.errorhandler(AppError)(self.handle_app_error)
        app.errorhandler(ValidationError)(self.handle_app_error)
        app.errorhandler(NotFoundError)(self.handle_app_error)
        app.errorhandler(UnauthorizedError)(self.handle_app_error)
        app.errorhandler(ForbiddenError)(self.handle_app_error)
        app.errorhandler(RateLimitError)(self.handle_app_error)
        app.errorhandler(PredictionError)(self.handle_app_error)
        
        # Register HTTP error handlers
        app.errorhandler(400)(self.handle_400)
        app.errorhandler(404)(self.handle_404)
        app.errorhandler(405)(self.handle_405)
        app.errorhandler(500)(self.handle_500)
        
        # Register generic exception handler
        app.errorhandler(Exception)(self.handle_generic_error)
        
        print("✅ ErrorHandler initialized")
    
    def handle_app_error(self, error):
        """
        Handle application-specific errors.
        
        Args:
            error: AppError instance
            
        Returns:
            JSON response with error details
        """
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        
        # Add retry-after header for rate limit errors
        if isinstance(error, RateLimitError):
            response.headers['Retry-After'] = str(error.payload.get('retry_after', 60))
        
        # Log error
        self._log_error(error, error.status_code)
        
        return response
    
    def handle_400(self, error):
        """Handle 400 Bad Request errors."""
        return jsonify({
            'error': 'BadRequest',
            'message': 'The request could not be understood or was missing required parameters',
            'timestamp': datetime.now().isoformat()
        }), 400
    
    def handle_404(self, error):
        """Handle 404 Not Found errors."""
        return jsonify({
            'error': 'NotFound',
            'message': f'The requested resource was not found: {request.path}',
            'path': request.path,
            'timestamp': datetime.now().isoformat()
        }), 404
    
    def handle_405(self, error):
        """Handle 405 Method Not Allowed errors."""
        return jsonify({
            'error': 'MethodNotAllowed',
            'message': f'Method {request.method} is not allowed for {request.path}',
            'method': request.method,
            'path': request.path,
            'timestamp': datetime.now().isoformat()
        }), 405
    
    def handle_500(self, error):
        """Handle 500 Internal Server Error."""
        self._log_error(error, 500)
        
        return jsonify({
            'error': 'InternalServerError',
            'message': 'An internal server error occurred. Please try again later.',
            'timestamp': datetime.now().isoformat()
        }), 500
    
    def handle_generic_error(self, error):
        """
        Handle generic uncaught exceptions.
        
        Args:
            error: Exception instance
            
        Returns:
            JSON response with error details
        """
        # Log full traceback
        self._log_error(error, 500, include_traceback=True)
        
        # Return generic error response (don't expose internal details)
        return jsonify({
            'error': 'InternalServerError',
            'message': 'An unexpected error occurred. Please try again later.',
            'timestamp': datetime.now().isoformat()
        }), 500
    
    def _log_error(self, error, status_code, include_traceback=False):
        """
        Log error details.
        
        Args:
            error: Error instance
            status_code: HTTP status code
            include_traceback: Whether to include full traceback
        """
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'status_code': status_code,
            'error_type': type(error).__name__,
            'message': str(error),
            'path': request.path,
            'method': request.method,
            'remote_addr': request.remote_addr
        }
        
        # Print error info
        print(f"\n{'='*60}")
        print(f"❌ ERROR: {error_info['error_type']}")
        print(f"{'='*60}")
        print(f"Message: {error_info['message']}")
        print(f"Status: {error_info['status_code']}")
        print(f"Path: {error_info['path']}")
        print(f"Method: {error_info['method']}")
        print(f"IP: {error_info['remote_addr']}")
        print(f"Time: {error_info['timestamp']}")
        
        # Include traceback for 500 errors
        if include_traceback:
            print(f"\nTraceback:")
            traceback.print_exc()
        
        print(f"{'='*60}\n")


def handle_errors(f):
    """
    Decorator to handle errors in route functions.
    Converts exceptions to appropriate HTTP responses.
    
    Example:
        @app.route('/api/predict')
        @handle_errors
        def predict():
            # Your code here
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except AppError:
            # Re-raise app errors (will be handled by error handler)
            raise
        except ValueError as e:
            # Convert ValueError to ValidationError
            raise ValidationError(str(e))
        except KeyError as e:
            # Convert KeyError to ValidationError
            raise ValidationError(f"Missing required field: {str(e)}")
        except FileNotFoundError as e:
            # Convert FileNotFoundError to NotFoundError
            raise NotFoundError("File", str(e))
        except Exception as e:
            # Log unexpected errors
            print(f"❌ Unexpected error in {f.__name__}: {str(e)}")
            traceback.print_exc()
            # Re-raise to be handled by generic error handler
            raise
    
    return decorated_function


def validate_json_request(f):
    """
    Decorator to validate that request contains valid JSON.
    
    Example:
        @app.route('/api/predict', methods=['POST'])
        @validate_json_request
        def predict():
            data = request.get_json()
            # data is guaranteed to be valid JSON
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            raise ValidationError(
                "Request must be JSON",
                payload={'content_type': request.content_type}
            )
        
        try:
            data = request.get_json()
            if data is None:
                raise ValidationError("Request body is empty")
        except Exception as e:
            raise ValidationError(f"Invalid JSON: {str(e)}")
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_fields(*required_fields):
    """
    Decorator to require specific fields in JSON request.
    
    Args:
        *required_fields: Field names that must be present
        
    Example:
        @app.route('/api/predict', methods=['POST'])
        @require_fields('disease', 'symptoms')
        def predict():
            data = request.get_json()
            # data['disease'] and data['symptoms'] are guaranteed to exist
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json()
            
            if not data:
                raise ValidationError("Request body is empty")
            
            missing_fields = [
                field for field in required_fields
                if field not in data
            ]
            
            if missing_fields:
                raise ValidationError(
                    "Missing required fields",
                    payload={'missing_fields': missing_fields}
                )
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def success_response(data=None, message=None, status_code=200):
    """
    Create a standardized success response.
    
    Args:
        data: Response data
        message: Success message
        status_code: HTTP status code
        
    Returns:
        JSON response
    """
    response_data = {
        'success': True,
        'timestamp': datetime.now().isoformat()
    }
    
    if message:
        response_data['message'] = message
    
    if data is not None:
        response_data['data'] = data
    
    return jsonify(response_data), status_code


def error_response(message, status_code=400, **kwargs):
    """
    Create a standardized error response.
    
    Args:
        message: Error message
        status_code: HTTP status code
        **kwargs: Additional error data
        
    Returns:
        JSON response
    """
    response_data = {
        'success': False,
        'error': message,
        'timestamp': datetime.now().isoformat()
    }
    
    response_data.update(kwargs)
    
    return jsonify(response_data), status_code
