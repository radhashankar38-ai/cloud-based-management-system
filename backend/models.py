from datetime import datetime, timezone

from extensions import db


def now():
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # admin | staff | user
    created_at = db.Column(db.DateTime, default=now)

    files = db.relationship('File', backref='owner', lazy=True, foreign_keys='File.owner_id')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'createdAt': self.created_at.isoformat(),
        }


class Folder(db.Model):
    __tablename__ = 'folders'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    color = db.Column(db.String(20), default='moss')
    created_at = db.Column(db.DateTime, default=now)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'createdAt': self.created_at.isoformat(),
        }


class File(db.Model):
    __tablename__ = 'files'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    stored_name = db.Column(db.String(255), nullable=False)  # actual filename on disk
    size_bytes = db.Column(db.Integer, default=0)

    folder_id = db.Column(db.Integer, db.ForeignKey('folders.id'), nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    starred = db.Column(db.Boolean, default=False)
    trashed = db.Column(db.Boolean, default=False)
    share_enabled = db.Column(db.Boolean, default=False)
    share_permission = db.Column(db.String(10), default='view')  # view | edit

    created_at = db.Column(db.DateTime, default=now)

    folder = db.relationship('Folder', backref='files')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'sizeBytes': self.size_bytes,
            'folderId': self.folder_id,
            'ownerId': self.owner_id,
            'ownerName': self.owner.name if self.owner else None,
            'starred': self.starred,
            'trashed': self.trashed,
            'shared': {'enabled': self.share_enabled, 'permission': self.share_permission},
            'createdAt': self.created_at.isoformat(),
        }


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # direct recipient
    target_role = db.Column(db.String(20), nullable=True)  # e.g. 'admin' for a broadcast
    message = db.Column(db.String(255), nullable=False)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=now)

    def to_dict(self):
        return {
            'id': self.id,
            'userId': self.user_id,
            'targetRole': self.target_role,
            'message': self.message,
            'read': self.read,
            'at': self.created_at.isoformat(),
        }


class ActivityLog(db.Model):
    __tablename__ = 'activity_log'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    message = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=now)

    def to_dict(self):
        return {
            'id': self.id,
            'userId': self.user_id,
            'message': self.message,
            'at': self.created_at.isoformat()
        }
