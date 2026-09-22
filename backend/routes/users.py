import os
import secrets

from flask import Blueprint, current_app, jsonify, request
from werkzeug.security import generate_password_hash

from decorators import current_user, role_required
from extensions import db
from models import File, Notification, User

users_bp = Blueprint('users', __name__, url_prefix='/api/users')


@users_bp.get('')
@role_required('admin')
def list_users():
    users = User.query.order_by(User.created_at.asc()).all()
    return jsonify({'users': [u.to_dict() for u in users]})


@users_bp.post('')
@role_required('admin')
def add_user():
    data = request.get_json(force=True, silent=True) or {}
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip().lower()
    role = data.get('role', 'user')
    if role not in ('admin', 'staff', 'user'):
        role = 'user'
    if not name or not email:
        return jsonify({'error': 'Name and email are required.'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'That email is already registered.'}), 409

    temp_password = secrets.token_urlsafe(6)
    user = User(name=name, email=email, password_hash=generate_password_hash(temp_password), role=role)
    db.session.add(user)
    db.session.commit()

    db.session.add(Notification(
        user_id=user.id,
        message=f'Your account was created by an Admin. Temporary password: {temp_password}'
    ))
    db.session.commit()
    # tempPassword is only ever returned here, to the admin who created the account —
    # it is never stored or logged in plain text elsewhere.
    return jsonify({'user': user.to_dict(), 'tempPassword': temp_password}), 201


@users_bp.patch('/<int:user_id>')
@role_required('admin')
def update_user_role(user_id):
    data = request.get_json(force=True, silent=True) or {}
    new_role = data.get('role')
    if new_role not in ('admin', 'staff', 'user'):
        return jsonify({'error': 'Invalid role.'}), 400

    user = User.query.get_or_404(user_id)
    if user.role == 'admin' and new_role != 'admin':
        if User.query.filter_by(role='admin').count() <= 1:
            return jsonify({'error': 'At least one Admin is required.'}), 400

    user.role = new_role
    db.session.add(Notification(user_id=user.id, message=f'Your role was changed to {new_role.capitalize()}.'))
    db.session.commit()
    return jsonify({'user': user.to_dict()})


@users_bp.delete('/<int:user_id>')
@role_required('admin')
def remove_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'admin' and User.query.filter_by(role='admin').count() <= 1:
        return jsonify({'error': 'At least one Admin is required.'}), 400

    # Clean up user's files from disk and DB
    upload_folder = current_app.config.get('UPLOAD_FOLDER', '')
    user_files = File.query.filter_by(owner_id=user_id).all()
    for f in user_files:
        try:
            p = os.path.join(upload_folder, f.stored_name)
            if os.path.exists(p):
                os.remove(p)
        except OSError:
            pass
        db.session.delete(f)

    Notification.query.filter_by(user_id=user_id).delete()
    db.session.delete(user)
    db.session.commit()
    return jsonify({'ok': True})
