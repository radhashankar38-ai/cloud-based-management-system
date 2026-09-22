import os

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from config import Config
from extensions import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # During development this allows any origin to call the API with cookies.
    # Restrict `origins` to your real frontend's URL before deploying.
    CORS(app, supports_credentials=True)

    db.init_app(app)

    from auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.files import files_bp
    from routes.folders import folders_bp
    from routes.notifications import notifications_bp
    from routes.reports import reports_bp
    from routes.users import users_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(folders_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(reports_bp)

    with app.app_context():
        db.create_all()

    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))

    @app.get('/api/health')
    def health():
        return {'status': 'ok'}

    @app.get('/')
    def index():
        return send_from_directory(frontend_dir, 'cloud-document-manager.html')

    @app.get('/s/<int:file_id>')
    def share_link_download(file_id):
        from models import File
        f = File.query.get_or_404(file_id)
        if not f.share_enabled or f.trashed:
            return jsonify({'error': 'This file is not shared or no longer available.'}), 404
        return send_from_directory(app.config['UPLOAD_FOLDER'], f.stored_name,
                                    as_attachment=True, download_name=f.name)

    @app.errorhandler(404)
    def handle_404(e):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Resource not found.'}), 404
        return send_from_directory(frontend_dir, 'cloud-document-manager.html')

    @app.errorhandler(413)
    def handle_413(e):
        return jsonify({'error': 'File too large (maximum 25 MB).'}), 413

    @app.errorhandler(500)
    def handle_500(e):
        return jsonify({'error': 'An internal server error occurred.'}), 500

    return app


if __name__ == '__main__':
    application = create_app()
    application.run(debug=True, port=5000)
