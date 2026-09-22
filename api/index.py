import os
import sys

# Ensure backend directory is in Python path for Vercel
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '..'))
backend_dir = os.path.join(root_dir, 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app import create_app

app = create_app()

# Auto-seed initial demo accounts on first launch if database is empty
with app.app_context():
    try:
        from models import User
        if User.query.count() == 0:
            import seed
            seed.run()
    except Exception as e:
        app.logger.warning(f"Initial seed check: {e}")
