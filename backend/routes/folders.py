from flask import Blueprint, jsonify, request

from decorators import current_user, login_required
from extensions import db
from models import ActivityLog, File, Folder

folders_bp = Blueprint('folders', __name__, url_prefix='/api/folders')


@folders_bp.get('')
@login_required
def list_folders():
    folders = Folder.query.order_by(Folder.created_at.asc()).all()
    return jsonify({'folders': [f.to_dict() for f in folders]})


@folders_bp.post('')
@login_required
def create_folder():
    user = current_user()
    data = request.get_json(force=True, silent=True) or {}
    name = (data.get('name') or '').strip()
    color = data.get('color', 'moss')
    if not name:
        return jsonify({'error': 'Folder name is required.'}), 400

    folder = Folder(name=name, color=color)
    db.session.add(folder)
    db.session.add(ActivityLog(user_id=user.id, message=f'Created folder "{name}"'))
    db.session.commit()
    return jsonify({'folder': folder.to_dict()}), 201


@folders_bp.patch('/<int:folder_id>')
@login_required
def update_folder(folder_id):
    folder = Folder.query.get_or_404(folder_id)
    data = request.get_json(force=True, silent=True) or {}
    if 'name' in data and data['name'].strip():
        folder.name = data['name'].strip()
    if 'color' in data:
        folder.color = data['color']
    db.session.commit()
    return jsonify({'folder': folder.to_dict()})


@folders_bp.delete('/<int:folder_id>')
@login_required
def delete_folder(folder_id):
    user = current_user()
    folder = Folder.query.get_or_404(folder_id)
    File.query.filter_by(folder_id=folder_id).update({'folder_id': None})
    name = folder.name
    db.session.delete(folder)
    db.session.add(ActivityLog(user_id=user.id if user else None, message=f'Deleted folder "{name}"'))
    db.session.commit()
    return jsonify({'ok': True})
