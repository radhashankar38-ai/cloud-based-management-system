from flask import Blueprint, jsonify

from decorators import current_user, login_required
from extensions import db
from models import Notification

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')


def _visible_query(user):
    return Notification.query.filter(
        db.or_(
            Notification.user_id == user.id,
            db.and_(Notification.target_role == 'admin', user.role == 'admin'),
        )
    )


@notifications_bp.get('')
@login_required
def list_notifications():
    user = current_user()
    notes = _visible_query(user).order_by(Notification.created_at.desc()).limit(30).all()
    return jsonify({'notifications': [n.to_dict() for n in notes]})


@notifications_bp.post('/mark-read')
@login_required
def mark_read():
    user = current_user()
    notes = _visible_query(user).filter_by(read=False).all()
    for n in notes:
        n.read = True
    db.session.commit()
    return jsonify({'ok': True, 'count': len(notes)})
