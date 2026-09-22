import csv
import io
from datetime import datetime, timedelta, timezone

from flask import Blueprint, Response, jsonify

from decorators import role_required
from models import File, User

reports_bp = Blueprint('reports', __name__, url_prefix='/api/reports')


@reports_bp.get('/summary')
@role_required('admin', 'staff')
def summary():
    files = File.query.filter_by(trashed=False).all()
    trashed_count = File.query.filter_by(trashed=True).count()
    users = User.query.all()

    by_role = {'admin': 0, 'staff': 0, 'user': 0}
    for u in users:
        by_role[u.role] = by_role.get(u.role, 0) + 1

    today = datetime.now(timezone.utc).date()
    days = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        count = sum(1 for f in files if f.created_at.date() == d)
        days.append({'date': d.isoformat(), 'count': count})

    return jsonify({
        'fileCount': len(files),
        'trashedCount': trashed_count,
        'userCount': len(users),
        'byRole': by_role,
        'storageBytes': sum(f.size_bytes for f in files),
        'last7Days': days,
    })


@reports_bp.get('/export')
@role_required('admin', 'staff')
def export_csv():
    files = File.query.order_by(File.created_at.desc()).all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(['Name', 'Owner', 'Folder', 'Size (bytes)', 'Filed on', 'Status'])
    for f in files:
        writer.writerow([
            f.name,
            f.owner.name if f.owner else '',
            f.folder.name if f.folder else '',
            f.size_bytes,
            f.created_at.isoformat(),
            'Trashed' if f.trashed else 'Active',
        ])
    return Response(
        buf.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=cbms-records.csv'},
    )
