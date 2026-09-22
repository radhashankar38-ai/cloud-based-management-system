from flask import Blueprint, jsonify

from decorators import current_user, login_required
from extensions import db
from models import ActivityLog, File, Folder

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')


@dashboard_bp.get('/stats')
@login_required
def stats():
    user = current_user()
    q = File.query.filter_by(trashed=False)
    if user.role == 'user':
        q = q.filter(db.or_(File.owner_id == user.id, File.share_enabled.is_(True)))
    files = q.all()

    act_q = ActivityLog.query
    if user.role == 'user':
        act_q = act_q.filter_by(user_id=user.id)
    activity = act_q.order_by(ActivityLog.created_at.desc()).limit(20).all()

    user_storage = sum(f.size_bytes for f in files if (user.role != 'user' or f.owner_id == user.id))

    return jsonify({
        'fileCount': len(files),
        'folderCount': Folder.query.count(),
        'starredCount': sum(1 for f in files if f.starred),
        'sharedCount': sum(1 for f in files if f.share_enabled),
        'storageBytes': user_storage,
        'quotaBytes': 15 * 1024 * 1024 * 1024,
        'activity': [a.to_dict() for a in activity],
    })
