"""
Structured Logging System
Provides comprehensive logging for debugging, monitoring, and auditing
"""

import logging
import json
from datetime import datetime
from functools import wraps
from flask import request, g
import time
import os


class StructuredLogger:
    """
    Structured logger with JSON formatting and multiple log levels.
    """
    
    def __init__(self, name='disease_prediction', log_dir='logs'):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name
            log_dir: Directory for log files
        """
        self.name = name
        self.log_dir = log_dir
        
        # Create logs directory if it doesn't exist
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Initialize logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # Add handlers
        self._add_console_handler()
        self._add_file_handlers()
        
        print(f"✅ StructuredLogger initialized: {name}")
    
    def _add_console_handler(self):
        """Add console handler with colored output."""
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Simple format for console
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
    
    def _add_file_handlers(self):
        """Add file handlers for different log levels."""
        # All logs
        all_handler = logging.FileHandler(
            os.path.join(self.log_dir, 'app.log')
        )
        all_handler.setLevel(logging.DEBUG)
        all_handler.setFormatter(self._get_json_formatter())
        self.logger.addHandler(all_handler)
        
        # Error logs
        error_handler = logging.FileHandler(
            os.path.join(self.log_dir, 'error.log')
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(self._get_json_formatter())
        self.logger.addHandler(error_handler)
        
        # API logs
        api_handler = logging.FileHandler(
            os.path.join(self.log_dir, 'api.log')
        )
        api_handler.setLevel(logging.INFO)
        api_handler.setFormatter(self._get_json_formatter())
        self.logger.addHandler(api_handler)
    
    def _get_json_formatter(self):
        """Get JSON formatter for structured logging."""
        return JsonFormatter()
    
    def _add_context(self, extra=None):
        """
        Add request context to log entry.
        
        Args:
            extra: Additional context data
            
        Returns:
            Dictionary with context data
        """
        context = extra or {}
        
        # Add request context if available
        try:
            if request:
                context.update({
                    'path': request.path,
                    'method': request.method,
                    'remote_addr': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', 'Unknown')
                })
                
                # Add request ID if available
                if hasattr(g, 'request_id'):
                    context['request_id'] = g.request_id
        except RuntimeError:
            # Outside request context
            pass
        
        return context
    
    def debug(self, message, **kwargs):
        """Log debug message."""
        self.logger.debug(message, extra=self._add_context(kwargs))
    
    def info(self, message, **kwargs):
        """Log info message."""
        self.logger.info(message, extra=self._add_context(kwargs))
    
    def warning(self, message, **kwargs):
        """Log warning message."""
        self.logger.warning(message, extra=self._add_context(kwargs))
    
    def error(self, message, **kwargs):
        """Log error message."""
        self.logger.error(message, extra=self._add_context(kwargs))
    
    def critical(self, message, **kwargs):
        """Log critical message."""
        self.logger.critical(message, extra=self._add_context(kwargs))
    
    def log_api_request(self, endpoint, method, status_code, duration, **kwargs):
        """
        Log API request with details.
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            status_code: Response status code
            duration: Request duration in seconds
            **kwargs: Additional data
        """
        self.info(
            f"API Request: {method} {endpoint}",
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            duration_ms=round(duration * 1000, 2),
            **kwargs
        )
    
    def log_prediction(self, disease, symptoms, probability, duration, **kwargs):
        """
        Log disease prediction.
        
        Args:
            disease: Disease name
            symptoms: List of symptoms
            probability: Prediction probability
            duration: Prediction duration in seconds
            **kwargs: Additional data
        """
        self.info(
            f"Prediction: {disease}",
            event_type='prediction',
            disease=disease,
            symptoms_count=len(symptoms),
            probability=round(probability, 4),
            duration_ms=round(duration * 1000, 2),
            **kwargs
        )
    
    def log_error(self, error_type, message, **kwargs):
        """
        Log error with details.
        
        Args:
            error_type: Type of error
            message: Error message
            **kwargs: Additional data
        """
        self.error(
            f"Error: {error_type}",
            error_type=error_type,
            error_message=message,
            **kwargs
        )
    
    def log_security_event(self, event_type, message, severity='warning', **kwargs):
        """
        Log security event.
        
        Args:
            event_type: Type of security event
            message: Event message
            severity: Event severity
            **kwargs: Additional data
        """
        log_func = getattr(self, severity, self.warning)
        log_func(
            f"Security: {event_type}",
            event_type='security',
            security_event=event_type,
            severity=severity,
            **kwargs
        )


class JsonFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    """
    
    def format(self, record):
        """
        Format log record as JSON.
        
        Args:
            record: Log record
            
        Returns:
            JSON string
        """
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        # Add extra fields
        if hasattr(record, '__dict__'):
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'created', 'filename', 
                              'funcName', 'levelname', 'levelno', 'lineno', 
                              'module', 'msecs', 'message', 'pathname', 
                              'process', 'processName', 'relativeCreated', 
                              'thread', 'threadName', 'exc_info', 'exc_text',
                              'stack_info']:
                    log_data[key] = value
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


# Global logger instance
_global_logger = None


def get_logger(name='disease_prediction'):
    """
    Get or create global logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        StructuredLogger instance
    """
    global _global_logger
    
    if _global_logger is None:
        _global_logger = StructuredLogger(name)
    
    return _global_logger


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
        logger = get_logger()
        
        # Generate request ID
        request_id = f"{int(time.time() * 1000)}-{request.remote_addr}"
        g.request_id = request_id
        
        # Log request start
        logger.debug(
            f"Request started: {request.method} {request.path}",
            request_id=request_id
        )
        
        # Execute function
        start_time = time.time()
        try:
            response = f(*args, **kwargs)
            duration = time.time() - start_time
            
            # Get status code
            status_code = 200
            if hasattr(response, 'status_code'):
                status_code = response.status_code
            elif isinstance(response, tuple) and len(response) > 1:
                status_code = response[1]
            
            # Log successful request
            logger.log_api_request(
                endpoint=request.path,
                method=request.method,
                status_code=status_code,
                duration=duration,
                request_id=request_id
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Log failed request
            logger.log_error(
                error_type=type(e).__name__,
                message=str(e),
                endpoint=request.path,
                method=request.method,
                duration=duration,
                request_id=request_id
            )
            
            raise
    
    return decorated_function


def log_prediction_request(f):
    """
    Decorator to log prediction requests.
    
    Example:
        @app.route('/api/predict')
        @log_prediction_request
        def predict():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logger = get_logger()
        
        # Get request data
        data = request.get_json() if request.is_json else {}
        disease = data.get('disease', 'unknown')
        symptoms = data.get('symptoms', [])
        
        # Execute function
        start_time = time.time()
        response = f(*args, **kwargs)
        duration = time.time() - start_time
        
        # Extract probability from response
        probability = 0.0
        if hasattr(response, 'get_json'):
            response_data = response.get_json()
            if isinstance(response_data, dict):
                probability = response_data.get('probability', 0.0)
        
        # Log prediction
        logger.log_prediction(
            disease=disease,
            symptoms=symptoms,
            probability=probability,
            duration=duration
        )
        
        return response
    
    return decorated_function


def log_security_event(event_type, message, severity='warning', **kwargs):
    """
    Log security event.
    
    Args:
        event_type: Type of security event
        message: Event message
        severity: Event severity
        **kwargs: Additional data
    """
    logger = get_logger()
    logger.log_security_event(event_type, message, severity, **kwargs)


class RequestLogger:
    """
    Request logger middleware for Flask.
    """
    
    def __init__(self, app=None):
        """
        Initialize request logger.
        
        Args:
            app: Flask application instance
        """
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """
        Initialize request logger for Flask app.
        
        Args:
            app: Flask application instance
        """
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        
        print("✅ RequestLogger initialized")
    
    def before_request(self):
        """Log before request."""
        g.start_time = time.time()
        g.request_id = f"{int(time.time() * 1000)}-{request.remote_addr}"
    
    def after_request(self, response):
        """
        Log after request.
        
        Args:
            response: Flask response object
            
        Returns:
            Response object
        """
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            
            logger = get_logger()
            logger.log_api_request(
                endpoint=request.path,
                method=request.method,
                status_code=response.status_code,
                duration=duration,
                request_id=getattr(g, 'request_id', 'unknown')
            )
        
        return response
