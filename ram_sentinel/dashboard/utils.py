"""
Utility functions for API responses and logging.
Provides standardized response formatting for all endpoints.
"""
from flask import jsonify
from datetime import datetime
import uuid
import logging

# Set up logging
logger = logging.getLogger(__name__)

def api_success(data=None, status_code=200, message=None):
    """
    Return standardized success response.
    
    Args:
        data: Response data payload
        status_code: HTTP status code
        message: Optional success message
    
    Returns:
        Flask response tuple with JSON and status code
    """
    response = {
        'success': True,
        'data': data if data is not None else {},
        'error': None,
        'error_code': None,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'request_id': str(uuid.uuid4())[:8]
    }
    
    if message:
        response['message'] = message
    
    return jsonify(response), status_code


def api_error(message, error_code=None, status_code=400, details=None):
    """
    Return standardized error response.
    
    Args:
        message: Error message
        error_code: Machine-readable error code
        status_code: HTTP status code
        details: Additional error details
    
    Returns:
        Flask response tuple with JSON and status code
    """
    response = {
        'success': False,
        'data': None,
        'error': message,
        'error_code': error_code or 'UNKNOWN_ERROR',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'request_id': str(uuid.uuid4())[:8]
    }
    
    if details:
        response['details'] = details
    
    return jsonify(response), status_code


def log_error(message, exception=None):
    """
    Log error with optional exception details.
    
    Args:
        message: Error message
        exception: Optional exception object
    """
    if exception:
        logger.error(f"{message}: {str(exception)}", exc_info=True)
    else:
        logger.error(message)
