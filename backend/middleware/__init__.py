"""
Middleware Package
Provides security, error handling, and logging middleware for the application
"""

from .error_handler import (
    AppError,
    ErrorHandler,
    ForbiddenError,
    NotFoundError,
    PredictionError,
    RateLimitError,
    UnauthorizedError,
    ValidationError,
    error_response,
    handle_errors,
    require_fields,
    success_response,
    validate_json_request,
)
from .logger import (
    RequestLogger,
    StructuredLogger,
    get_logger,
    log_prediction_request,
    log_request,
    log_security_event,
)
from .security import cors_headers
from .security import log_request as security_log_request
from .security import (
    rate_limit,
    rate_limiter,
    security_validator,
    validate_request_data,
)

__all__ = [
    # Security
    "rate_limiter",
    "security_validator",
    "rate_limit",
    "validate_request_data",
    "cors_headers",
    "security_log_request",
    # Error Handling
    "ErrorHandler",
    "AppError",
    "ValidationError",
    "NotFoundError",
    "UnauthorizedError",
    "ForbiddenError",
    "RateLimitError",
    "PredictionError",
    "handle_errors",
    "validate_json_request",
    "require_fields",
    "success_response",
    "error_response",
    # Logging
    "StructuredLogger",
    "get_logger",
    "log_request",
    "log_prediction_request",
    "log_security_event",
    "RequestLogger",
]
