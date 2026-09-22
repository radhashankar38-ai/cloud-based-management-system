# Cloud-Based Management System — Backend

A Flask + SQLite REST API implementing the full feature set: registration & login,
role-based access (Admin / Staff / User), a centralized file & folder registry,
sharing, trash, notifications, and reports. This is the backend only — pair it
with any frontend (a web app, mobile app, or the earlier HTML prototype adapted
to call these endpoints instead of local storage).

## Setup

```bash
cd cbms-backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

python seed.py                    # creates demo accounts + sample data
python app.py                     # runs on http://localhost:5000
```

Tables are also created automatically on first run even without `seed.py`,
but seeding gives you demo accounts to log in with right away.

## Demo accounts

| Role  | Email         | Password |
|-------|---------------|----------|
| Admin | admin@demo.io | demo123  |
| Staff | staff@demo.io | demo123  |
| User  | user@demo.io  | demo123  |

The **first account ever registered** through `/api/auth/register` also
becomes Admin automatically; everyone after that starts as a User and can be
promoted from the Users screen.

## Configuration

Environment variables (see `.env.example`):

- `SECRET_KEY` — signs session cookies. Set a real random value in production.
- `DATABASE_URL` — defaults to a local SQLite file. Point this at Postgres or
  MySQL for a real deployment, e.g. `postgresql://user:pass@host/cbms`.

## Authentication

Sessions use Flask's signed cookies (`session['user_id']`), sent automatically
by the browser once you're logged in. If your frontend runs on a different
origin, send requests with `credentials: 'include'` (fetch) or
`withCredentials: true` (axios) so the cookie round-trips.

## API reference

All request/response bodies are JSON unless noted. Endpoints marked 🔒 require
login; 🛡️ Admin/Staff only; 👑 Admin only.

### Auth
| Method | Path | Description |
|---|---|---|
| POST | `/api/auth/register` | `{name, email, password}` → creates account, logs in |
| POST | `/api/auth/login` | `{email, password}` → logs in |
| POST | `/api/auth/logout` | 🔒 ends the session |
| GET  | `/api/auth/me` | returns the current user, or `{"user": null}` |

### Files 🔒
| Method | Path | Description |
|---|---|---|
| GET | `/api/files?folderId=&search=&sort=` | list files (scoped to role) |
| GET | `/api/files/trash` | list trashed files |
| POST | `/api/files` | multipart upload: `file`, optional `folderId` |
| GET | `/api/files/<id>/download` | download the stored file |
| PATCH | `/api/files/<id>` | update `name`, `folderId`, `starred`, `shared` |
| POST | `/api/files/<id>/trash` | move to trash |
| POST | `/api/files/<id>/restore` | restore from trash |
| DELETE | `/api/files/<id>` | 🛡️ permanently delete |
| POST | `/api/files/trash/empty` | 🛡️ empty the trash |

A User can only see/act on their own files plus anything shared; only Admin/Staff
can permanently delete or empty trash.

### Folders 🔒
| Method | Path | Description |
|---|---|---|
| GET | `/api/folders` | list all folders |
| POST | `/api/folders` | `{name, color}` |
| PATCH | `/api/folders/<id>` | rename / recolor |
| DELETE | `/api/folders/<id>` | delete (files inside become unfiled) |

### Users 👑
| Method | Path | Description |
|---|---|---|
| GET | `/api/users` | list all accounts |
| POST | `/api/users` | `{name, email, role}` → creates account, returns a temp password |
| PATCH | `/api/users/<id>` | `{role}` — blocked if it would leave zero Admins |
| DELETE | `/api/users/<id>` | remove account — same last-Admin guard |

### Notifications 🔒
| Method | Path | Description |
|---|---|---|
| GET | `/api/notifications` | recent notifications for the current user |
| POST | `/api/notifications/mark-read` | marks all currently-visible ones read |

### Dashboard 🔒
| Method | Path | Description |
|---|---|---|
| GET | `/api/dashboard/stats` | file/folder/starred/shared counts + recent activity |

### Reports 🛡️
| Method | Path | Description |
|---|---|---|
| GET | `/api/reports/summary` | totals, accounts by role, last-7-days chart data |
| GET | `/api/reports/export` | downloads `cbms-records.csv` |

## Notes on security

- Passwords are hashed with Werkzeug's `generate_password_hash` (PBKDF2) —
  never stored in plain text.
- Every write route checks the session and, where relevant, the caller's role
  server-side — role checks in a frontend are just UI convenience, this is the
  real enforcement.
- CORS is wide open (`CORS(app)`) for easy local development. Before deploying,
  restrict it to your actual frontend origin, e.g.
  `CORS(app, origins=["https://your-frontend.example"], supports_credentials=True)`.
- Uploaded files are stored on disk under `uploads/` with randomized filenames;
  only metadata lives in the database.
- For a production deployment: serve behind HTTPS, set `SESSION_COOKIE_SECURE = True`
  in `config.py`, and switch `DATABASE_URL` to Postgres/MySQL.

## Project structure

```
cbms-backend/
├── app.py              # app factory, blueprint registration
├── config.py            # settings (secret key, DB URI, upload folder)
├── extensions.py         # shared SQLAlchemy instance
├── models.py             # User, Folder, File, Notification, ActivityLog
├── decorators.py          # @login_required, @role_required
├── auth.py               # register / login / logout / me
├── seed.py                # demo data
├── routes/
│   ├── files.py
│   ├── folders.py
│   ├── users.py
│   ├── notifications.py
│   ├── dashboard.py
│   └── reports.py
├── requirements.txt
└── uploads/              # created automatically at runtime
```
