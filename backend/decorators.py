from functools import wraps

from flask import jsonify, session

from models import User


def current_user():
    uid = session.get('user_id')
    return User.query.get(uid) if uid else None


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated.'}), 401
        return f(*args, **kwargs)
    return wrapper


def role_required(*roles):
    """Restrict a route to one or more roles, e.g. @role_required('admin', 'staff')."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = current_user()
            if not user:
                return jsonify({'error': 'Not authenticated.'}), 401
            if user.role not in roles:
                return jsonify({'error': 'Forbidden — insufficient role.'}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator
