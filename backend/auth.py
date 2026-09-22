from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from decorators import current_user, login_required
from extensions import db
from models import ActivityLog, Notification, User

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.post('/register')
def register():
    data = request.get_json(force=True, silent=True) or {}
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not name or not email or len(password) < 4:
        return jsonify({'error': 'Name, email, and a password of at least 4 characters are required.'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'An account with that email already exists.'}), 409

    # First account to ever register becomes Admin; everyone after defaults to User
    # and can be promoted later from the Users screen.
    role = 'admin' if User.query.count() == 0 else 'user'

    user = User(name=name, email=email, password_hash=generate_password_hash(password), role=role)
    db.session.add(user)
    db.session.commit()

    db.session.add(Notification(target_role='admin', message=f'New account registered: {name}'))
    db.session.add(ActivityLog(user_id=user.id, message=f'Account created: {name}'))
    db.session.commit()

    session['user_id'] = user.id
    return jsonify({'user': user.to_dict()}), 201


@auth_bp.post('/login')
def login():
    data = request.get_json(force=True, silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'error': 'No matching account — check email and password.'}), 401

    session['user_id'] = user.id
    return jsonify({'user': user.to_dict()})


@auth_bp.post('/logout')
@login_required
def logout():
    session.pop('user_id', None)
    return jsonify({'ok': True})


@auth_bp.get('/me')
def me():
    user = current_user()
    return jsonify({'user': user.to_dict() if user else None})
