"""
Shared response utilities for consistent API responses.

All route handlers should use these helpers to ensure
the response envelope matches the API contract.
"""
from flask import jsonify


def success_response(data, status_code=200, meta=None):
    """Return a standardized success response.
    
    Args:
        data: Response payload (dict, list, or primitive).
        status_code: HTTP status code (default 200).
        meta: Optional metadata dict (pagination, etc.).
    
    Returns:
        Flask response with {"data": ..., "meta": ...}
    """
    body = {"data": data}
    if meta:
        body["meta"] = meta
    return jsonify(body), status_code


def error_response(code, message, status_code=400):
    """Return a standardized error response.
    
    Args:
        code: Machine-readable error code (e.g. "BAD_REQUEST").
        message: Human-readable error message.
        status_code: HTTP status code (default 400).
    
    Returns:
        Flask response with {"error": {"code": ..., "message": ...}}
    """
    return jsonify({
        "error": {
            "code": code,
            "message": message,
        }
    }), status_code


def paginated_response(items, total, page, per_page):
    """Return a standardized paginated response.
    
    Args:
        items: List of items for the current page.
        total: Total number of items across all pages.
        page: Current page number (1-indexed).
        per_page: Items per page.
    
    Returns:
        Flask response with {"data": [...], "meta": {...}}
    """
    total_pages = max(1, (total + per_page - 1) // per_page)
    return success_response(items, meta={
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    })


# ── Convenience Error Helpers ──

def bad_request(message):
    return error_response("BAD_REQUEST", message, 400)

def auth_required(message="Authentication required"):
    return error_response("AUTH_REQUIRED", message, 401)

def forbidden(message="Access denied"):
    return error_response("FORBIDDEN", message, 403)

def not_found(message="Resource not found"):
    return error_response("NOT_FOUND", message, 404)

def conflict(message):
    return error_response("CONFLICT", message, 409)

def internal_error(message="Internal server error"):
    return error_response("INTERNAL_ERROR", message, 500)
