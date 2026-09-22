import os
import uuid

from flask import Blueprint, current_app, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename

from decorators import current_user, login_required
from extensions import db
from models import ActivityLog, File

files_bp = Blueprint('files', __name__, url_prefix='/api/files')


def visible_query(user):
    """Admin/Staff see every active file. A User sees their own files plus anything shared."""
    q = File.query.filter_by(trashed=False)
    if user.role == 'user':
        q = q.filter(db.or_(File.owner_id == user.id, File.share_enabled.is_(True)))
    return q


def can_modify(user, f):
    return user.role != 'user' or f.owner_id == user.id


@files_bp.get('')
@login_required
def list_files():
    user = current_user()
    folder_id = request.args.get('folderId', type=int)
    search = (request.args.get('search') or '').strip().lower()
    sort_by = request.args.get('sort', 'date-desc')

    q = visible_query(user)
    if folder_id:
        q = q.filter_by(folder_id=folder_id)
    results = q.all()
    if search:
        results = [f for f in results if search in f.name.lower()]

    key_fn = {
        'name-asc': lambda f: f.name.lower(), 'name-desc': lambda f: f.name.lower(),
        'size-asc': lambda f: f.size_bytes, 'size-desc': lambda f: f.size_bytes,
        'date-asc': lambda f: f.created_at, 'date-desc': lambda f: f.created_at,
    }.get(sort_by, lambda f: f.created_at)
    results.sort(key=key_fn, reverse=sort_by in ('name-desc', 'size-desc', 'date-desc'))

    return jsonify({'files': [f.to_dict() for f in results]})


@files_bp.get('/trash')
@login_required
def list_trash():
    user = current_user()
    q = File.query.filter_by(trashed=True)
    if user.role == 'user':
        q = q.filter_by(owner_id=user.id)
    results = q.order_by(File.created_at.desc()).all()
    return jsonify({'files': [f.to_dict() for f in results]})


@files_bp.post('')
@login_required
def upload_file():
    user = current_user()
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided.'}), 400
    upload = request.files['file']
    if upload.filename == '':
        return jsonify({'error': 'No file selected.'}), 400

    folder_id = request.form.get('folderId', type=int)
    safe_name = secure_filename(upload.filename) or 'file'
    stored_name = f'{uuid.uuid4().hex}_{safe_name}'
    path = os.path.join(current_app.config['UPLOAD_FOLDER'], stored_name)
    upload.save(path)
    size = os.path.getsize(path)

    rec = File(name=upload.filename, stored_name=stored_name, size_bytes=size,
               folder_id=folder_id, owner_id=user.id)
    db.session.add(rec)
    db.session.add(ActivityLog(user_id=user.id, message=f'Filed "{upload.filename}"'))
    db.session.commit()
    return jsonify({'file': rec.to_dict()}), 201


@files_bp.get('/<int:file_id>/download')
@login_required
def download_file(file_id):
    user = current_user()
    f = File.query.get_or_404(file_id)
    if user.role == 'user' and f.owner_id != user.id and not f.share_enabled:
        return jsonify({'error': 'Forbidden.'}), 403
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], f.stored_name,
                                as_attachment=True, download_name=f.name)


@files_bp.patch('/<int:file_id>')
@login_required
def update_file(file_id):
    user = current_user()
    f = File.query.get_or_404(file_id)
    if not can_modify(user, f):
        return jsonify({'error': 'Forbidden.'}), 403

    data = request.get_json(force=True, silent=True) or {}
    if 'name' in data and data['name'].strip():
        old = f.name
        f.name = data['name'].strip()
        db.session.add(ActivityLog(user_id=user.id, message=f'Renamed "{old}" to "{f.name}"'))
    if 'folderId' in data:
        f.folder_id = data['folderId']
    if 'starred' in data:
        new_starred = bool(data['starred'])
        if new_starred != f.starred:
            db.session.add(ActivityLog(user_id=user.id, message=('Starred "' if new_starred else 'Unstarred "') + f.name + '"'))
        f.starred = new_starred
    if 'shared' in data and isinstance(data['shared'], dict):
        shared = data['shared']
        if 'enabled' in shared:
            f.share_enabled = bool(shared['enabled'])
            db.session.add(ActivityLog(user_id=user.id, message=('Shared "' if f.share_enabled else 'Unshared "') + f.name + '"'))
        if 'permission' in shared and shared['permission'] in ('view', 'edit'):
            f.share_permission = shared['permission']

    db.session.commit()
    return jsonify({'file': f.to_dict()})


@files_bp.post('/<int:file_id>/trash')
@login_required
def trash_file(file_id):
    user = current_user()
    f = File.query.get_or_404(file_id)
    if not can_modify(user, f):
        return jsonify({'error': 'Forbidden.'}), 403
    f.trashed = True
    db.session.add(ActivityLog(user_id=user.id, message=f'Moved "{f.name}" to trash'))
    db.session.commit()
    return jsonify({'file': f.to_dict()})


@files_bp.post('/<int:file_id>/restore')
@login_required
def restore_file(file_id):
    user = current_user()
    f = File.query.get_or_404(file_id)
    if not can_modify(user, f):
        return jsonify({'error': 'Forbidden.'}), 403
    f.trashed = False
    db.session.add(ActivityLog(user_id=user.id, message=f'Restored "{f.name}"'))
    db.session.commit()
    return jsonify({'file': f.to_dict()})


@files_bp.delete('/<int:file_id>')
@login_required
def delete_file(file_id):
    user = current_user()
    if user.role == 'user':
        return jsonify({'error': 'Forbidden — only Admin or Staff can permanently delete.'}), 403
    f = File.query.get_or_404(file_id)
    _remove_from_disk(f.stored_name)
    name = f.name
    db.session.delete(f)
    db.session.add(ActivityLog(user_id=user.id, message=f'Permanently deleted "{name}"'))
    db.session.commit()
    return jsonify({'ok': True})


@files_bp.post('/trash/empty')
@login_required
def empty_trash():
    user = current_user()
    if user.role == 'user':
        return jsonify({'error': 'Forbidden — only Admin or Staff can empty trash.'}), 403
    trashed = File.query.filter_by(trashed=True).all()
    count = len(trashed)
    for f in trashed:
        _remove_from_disk(f.stored_name)
        db.session.delete(f)
    db.session.add(ActivityLog(user_id=user.id, message=f'Emptied trash ({count} file{"s" if count != 1 else ""})'))
    db.session.commit()
    return jsonify({'ok': True, 'count': count})


def _remove_from_disk(stored_name):
    try:
        path = os.path.join(current_app.config['UPLOAD_FOLDER'], stored_name)
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass
