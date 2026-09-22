"""Populate the database with demo accounts and sample data.

Run once after installing dependencies:
    python seed.py

Safe to re-run — it skips seeding if any user already exists.
"""
import os

from werkzeug.security import generate_password_hash

from app import create_app
from extensions import db
from models import ActivityLog, File, Folder, Notification, User

app = create_app()


def make_placeholder(upload_dir, stored_name, text):
    path = os.path.join(upload_dir, stored_name)
    with open(path, 'w') as fh:
        fh.write(text)
    return os.path.getsize(path)


def run():
    with app.app_context():
        if User.query.first():
            print('Database already has data — skipping seed.')
            return

        admin = User(name='Priya Admin', email='admin@demo.io',
                     password_hash=generate_password_hash('demo123'), role='admin')
        staff = User(name='Ravi Staff', email='staff@demo.io',
                     password_hash=generate_password_hash('demo123'), role='staff')
        guest = User(name='Guest User', email='user@demo.io',
                     password_hash=generate_password_hash('demo123'), role='user')
        db.session.add_all([admin, staff, guest])
        db.session.commit()

        coursework = Folder(name='Coursework', color='moss')
        reports = Folder(name='Project Reports', color='navy')
        certs = Folder(name='Certificates', color='gold')
        db.session.add_all([coursework, reports, certs])
        db.session.commit()

        upload_dir = app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)

        # (name, stored filename, folder, owner, starred, share enabled, share permission)
        entries = [
            ('Data Structures Notes.pdf', 'seed_ds_notes.txt', coursework.id, admin.id, False, False, 'view'),
            ('Semester Project Report.docx', 'seed_report.txt', reports.id, admin.id, True, True, 'view'),
            ('Internship Certificate.pdf', 'seed_cert.txt', certs.id, admin.id, False, False, 'view'),
            ('Resume.pdf', 'seed_resume.txt', None, admin.id, True, False, 'view'),
            ('Hackathon Pitch Deck.pptx', 'seed_deck.txt', None, admin.id, False, True, 'edit'),
            ('Reading List.md', 'seed_reading.txt', None, guest.id, False, False, 'view'),
        ]
        for name, stored, folder_id, owner_id, starred, share_enabled, perm in entries:
            size = make_placeholder(upload_dir, stored, f'Placeholder content for {name}')
            db.session.add(File(name=name, stored_name=stored, size_bytes=size, folder_id=folder_id,
                                 owner_id=owner_id, starred=starred, share_enabled=share_enabled,
                                 share_permission=perm))
        db.session.commit()

        db.session.add_all([
            ActivityLog(user_id=guest.id, message='Filed "Reading List.md"'),
            ActivityLog(user_id=admin.id, message='Shared "Hackathon Pitch Deck.pptx"'),
            ActivityLog(user_id=admin.id, message='Starred "Resume.pdf"'),
            Notification(target_role='admin', message='New account registered: Guest User'),
        ])
        db.session.commit()

        print('Seed complete.')
        print('Demo accounts (password for all: demo123):')
        print('  Admin — admin@demo.io')
        print('  Staff — staff@demo.io')
        print('  User  — user@demo.io')


if __name__ == '__main__':
    run()
