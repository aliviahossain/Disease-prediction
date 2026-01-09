"""
Middleware Package
Provides security, error handling, and logging middleware for the application
"""

from .security import (
    rate_limiter,
    security_validator,
    rate_limit,
    validate_request_data,
    cors_headers,
    log_request as security_log_request
)

from .error_handler import (
    ErrorHandler,
    AppError,
    ValidationError,
    NotFoundError,
    UnauthorizedError,
    ForbiddenError,
    RateLimitError,
    PredictionError,
    handle_errors,
    validate_json_request,
    require_fields,
    success_response,
    error_response
)

from .logger import (
    StructuredLogger,
    get_logger,
    log_request,
    log_prediction_request,
    log_security_event,
    RequestLogger
)

__all__ = [
    # Security
    'rate_limiter',
    'security_validator',
    'rate_limit',
    'validate_request_data',
    'cors_headers',
    'security_log_request',
    
    # Error Handling
    'ErrorHandler',
    'AppError',
    'ValidationError',
    'NotFoundError',
    'UnauthorizedError',
    'ForbiddenError',
    'RateLimitError',
    'PredictionError',
    'handle_errors',
    'validate_json_request',
    'require_fields',
    'success_response',
    'error_response',
    
    # Logging
    'StructuredLogger',
    'get_logger',
    'log_request',
    'log_prediction_request',
    'log_security_event',
    'RequestLogger'
]
