"""
Flask REST API for bank customer service chatbot.
Implements OWASP REST Security best practices.
Supports streaming responses via Server-Sent Events (SSE).
"""

import os
import json
import logging
import re
import uuid
from typing import Generator, Dict, Any
from datetime import datetime
from functools import wraps

from flask import Flask, request, Response, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
import secrets

# Import chatbot modules
from conversation import ConversationSession
from security import SecurityValidator
from audit_logger import audit_logger, AuditEventType
from validators import (
    validate_request_body,
    validate_chat_message,
    validate_session_id_param,
    ResponseValidator
)

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logging.getLogger('werkzeug').setLevel(logging.WARNING)

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
        "methods": ["GET", "POST", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "X-Client-Version"],
        "expose_headers": ["X-Total-Count"],
        "supports_credentials": True,
        "max_age": 3600
    }
})

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per hour", "50 per minute"],
    storage_uri="memory://",
    strategy="fixed-window"
)

API_KEYS = {}
SESSION_STORE = {}


def redact_session_id(session_id: str) -> str:
    """Return a redacted session ID for logs."""
    if not session_id or len(session_id) < 8:
        return "[redacted]"
    return f"{session_id[:4]}...{session_id[-4:]}"


def redact_sensitive(value: str) -> str:
    """Redact API keys and customer IDs from log messages."""
    if not value:
        return value
    redacted = value
    # Redact API keys (32+ chars) and tokens
    redacted = re.sub(r"[A-Za-z0-9_-]{32,}", "[redacted]", redacted)
    # Redact customer IDs (Taiwan ID: 1 letter + 9 digits)
    redacted = re.sub(r"\b[A-Z]\d{9}\b", "[redacted]", redacted)
    return redacted


class RedactFilter(logging.Filter):
    """Redact sensitive patterns from all log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except Exception:
            return True
        record.msg = redact_sensitive(message)
        record.args = ()
        return True


_redact_filter = RedactFilter()
logging.getLogger().addFilter(_redact_filter)
logger.addFilter(_redact_filter)


def add_security_headers(response):
    """Add OWASP recommended security headers to response."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Content-Security-Policy'] = "default-src 'none'; frame-ancestors 'none'"
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    return response


@app.after_request
def apply_security_headers(response):
    """Apply security headers to all responses."""
    return add_security_headers(response)


def validate_request_content_type():
    """Validate request content type."""
    if request.method in ['POST', 'PUT', 'PATCH']:
        content_type = request.content_type
        if content_type not in ['application/json', 'application/json; charset=utf-8']:
            return jsonify({
                'error': 'Unsupported Media Type',
                'message': 'Content-Type must be application/json'
            }), 415
    return None


def require_api_key(f):
    """Decorator to require API key for endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # API key can be in header or as query parameter
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if not api_key:
            logger.warning("Request rejected: Missing API key")
            return jsonify({
                'error': 'Unauthorized',
                'message': 'API key required'
            }), 401
        
        if not isinstance(api_key, str) or len(api_key) < 32:
            logger.warning("Request rejected: Invalid API key format")
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Invalid API key'
            }), 401
        
        return f(*args, **kwargs)
    return decorated_function


def create_session_id() -> str:
    """Create a secure session ID in UUID format."""
    return str(uuid.uuid4())


@app.errorhandler(400)
def bad_request(error):
    """Handle 400 Bad Request."""
    logger.warning(f"Bad request: {redact_sensitive(str(error))}")
    return jsonify({
        'error': 'Bad Request',
        'message': 'The request is malformed or invalid'
    }), 400


@app.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found."""
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested resource was not found'
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 Method Not Allowed."""
    return jsonify({
        'error': 'Method Not Allowed',
        'message': f'The {request.method} method is not allowed for this resource'
    }), 405


@app.errorhandler(429)
def rate_limit_exceeded(error):
    """Handle 429 Too Many Requests."""
    ip_address = request.remote_addr or 'unknown'
    audit_logger.log_rate_limit(
        ip_address=ip_address,
        endpoint=request.path
    )
    return jsonify({
        'error': 'Too Many Requests',
        'message': 'Rate limit exceeded. Please try again later'
    }), 429


@app.errorhandler(500)
def internal_server_error(error):
    """Handle 500 Internal Server Error."""
    error_msg = ResponseValidator.sanitize_error_message(str(error))
    logger.error(f"Internal server error: {redact_sensitive(error_msg)}")
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    """Catch-all handler for unexpected errors."""
    error_msg = ResponseValidator.sanitize_error_message(str(error))
    logger.error(f"Unexpected error: {redact_sensitive(error_msg)}")
    
    if any(keyword in str(error).lower() for keyword in ['injection', 'overflow', 'exploit']):
        audit_logger.log_security_violation(
            ip_address=request.remote_addr or 'unknown',
            violation_type='suspicious_error',
            details={'error': error_msg}
        )
    
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@app.route('/api/session', methods=['POST'])
@limiter.limit("10 per minute")
def create_session():
    """Create a new chatbot session."""
    error = validate_request_content_type()
    if error:
        return error
    
    try:
        session_id = create_session_id()
        SESSION_STORE[session_id] = ConversationSession(session_id=session_id)
        
        logger.info(f"New session created: {redact_session_id(session_id)}")
        audit_logger.log_event(
            event_type=AuditEventType.SESSION_CREATED,
            session_id=session_id,
            ip_address=request.remote_addr or 'unknown'
        )
        
        return jsonify({
            'session_id': session_id,
            'created_at': datetime.utcnow().isoformat()
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating session: {redact_sensitive(str(e))}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Failed to create session'
        }), 500


@app.route('/api/chat/<session_id>', methods=['POST', 'GET'])
@limiter.limit("30 per minute")
@validate_session_id_param()
def chat(session_id: str):
    """
    Send a message and receive streaming response.
    Uses Server-Sent Events (SSE) for text streaming.
    Supports both POST (with JSON body) and GET (with query parameter) for flexibility.
    """
    if session_id not in SESSION_STORE:
        logger.warning(f"Session not found: {redact_session_id(session_id)}")
        return jsonify({
            'error': 'Not Found',
            'message': 'Session not found. Please create a new session'
        }), 404
    
    try:
        if request.method == 'GET':
            message = request.args.get('message', '').strip()
            logger.info(f"GET request with message from query param")
        else:
            error = validate_request_content_type()
            if error:
                return error
            
            data = request.get_json()
            if not data or 'message' not in data:
                logger.warning("Missing 'message' field in request")
                return jsonify({
                    'error': 'Bad Request',
                    'message': 'Request body must contain "message" field'
                }), 400
            message = data.get('message', '').strip()
        
        from validators import RequestValidator
        is_valid, error_msg = RequestValidator.validate_message(message)
        if not is_valid:
            logger.warning(f"Invalid message: {error_msg}")
            return jsonify({
                'error': 'Bad Request',
                'message': error_msg
            }), 400
        
        session = SESSION_STORE[session_id]
        logger.info(
            "Processing message for session %s (length=%d)",
            redact_session_id(session_id),
            len(message)
        )
        response = session.process_message(message)
        is_valid, error_msg = SecurityValidator.validate_response(response)
        if not is_valid:
            logger.error(f"Security validation failed: {error_msg}")
            return jsonify({
                'error': 'Internal Server Error',
                'message': 'Response validation failed'
            }), 500
        
        return Response(
            stream_response(response),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )
        
    except json.JSONDecodeError:
        logger.warning("Invalid JSON in request body")
        return jsonify({
            'error': 'Bad Request',
            'message': 'Invalid JSON in request body'
        }), 400
    except Exception as e:
        logger.error(f"Error processing message: {redact_sensitive(str(e))}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Failed to process message'
        }), 500


def stream_response(text: str) -> Generator[str, None, None]:
    """
    Stream response as Server-Sent Events.
    Chunks text into smaller pieces for streaming.
    """
    chunk_size = 20
    
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i + chunk_size]
        # Format as SSE
        yield f"data: {json.dumps({'text': chunk})}\n\n"
    
    yield f"data: {json.dumps({'done': True})}\n\n"


@app.route('/api/session/<session_id>/history', methods=['GET'])
@validate_session_id_param()
def get_history(session_id: str):
    """Get conversation history for a session."""
    if session_id not in SESSION_STORE:
        return jsonify({
            'error': 'Not Found',
            'message': 'Session not found'
        }), 404
    
    try:
        session = SESSION_STORE[session_id]
        history = session.get_conversation_history()
        
        return jsonify({
            'session_id': session_id,
            'history': history,
            'count': len(history)
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving history: {redact_sensitive(str(e))}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Failed to retrieve history'
        }), 500


@app.route('/api/session/<session_id>', methods=['DELETE'])
@validate_session_id_param()
def delete_session(session_id: str):
    """Delete a session (logout)."""
    if session_id in SESSION_STORE:
        del SESSION_STORE[session_id]
        logger.info(f"Session deleted: {redact_session_id(session_id)}")
        audit_logger.log_event(
            event_type=AuditEventType.SESSION_DELETED,
            session_id=session_id,
            ip_address=request.remote_addr or 'unknown'
        )
        return jsonify({
            'message': 'Session deleted successfully'
        }), 200
    
    return jsonify({
        'error': 'Not Found',
        'message': 'Session not found'
    }), 404


@app.route('/api/info', methods=['GET'])
def api_info():
    """Get API information."""
    return jsonify({
        'name': 'Bank Customer Service Chatbot API',
        'version': '1.0.0',
        'endpoints': {
            'health': 'GET /api/health',
            'create_session': 'POST /api/session',
            'send_message': 'POST /api/chat/<session_id>',
            'get_history': 'GET /api/session/<session_id>/history',
            'delete_session': 'DELETE /api/session/<session_id>'
        }
    }), 200


if __name__ == '__main__':
    # Development only
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('FLASK_DEBUG', 'False') == 'True'
    )
