# Cloud-Based Management System (CBMS)

A full-stack document registry and file management platform with role-based access control (Admin, Staff, User), folder hierarchies, link sharing with permissions, trash recovery, activity auditing, and dual database support (SQLite & Supabase PostgreSQL).

---

## Key Features

- **Role-Based Access Control**:
  - **Admin**: Complete administrative control, user role management, system-wide file access, storage reporting, and CSV data export.
  - **Staff**: Workspace overview, reports, and document management.
  - **User**: Strict user isolation — users only see and manage their own files and documents shared directly with them.
- **File & Folder Management**:
  - Drag-and-drop batch upload with size and format validation.
  - Folder creation with custom color labels and breadcrumb navigation.
  - Star documents for quick access.
  - Trash bin with one-click restore and permanent delete safeguards.
- **Effortless Sharing**:
  - Generate instant public share links with configurable permissions (`view` / `edit`).
  - Dedicated download route (`/s/<file_id>`).
- **Polished UI & Dark Mode**:
  - Clean archival/editorial aesthetic with rounded buttons and fluid elevation.
  - Built-in Dark Mode and Light Mode with instant toggle and `localStorage` persistence.
  - Crisp vector SVG iconography (no cartoon emojis).
  - Minimal floating detail panel for metadata, rename, and share controls.
- **Production-Ready Persistence**:
  - SQLite for zero-config local development.
  - Supabase PostgreSQL schema with indexes, foreign keys, and row-level security (`supabase_schema.sql`).

---

## Project Structure

```
cloud-based-management-system/
├── backend/
│   ├── app.py                  # Flask application & static file server
│   ├── auth.py                 # Authentication routes (login, register, logout, me)
│   ├── config.py               # Database URL & environment configuration
│   ├── decorators.py           # Role-based access control decorators
│   ├── extensions.py           # SQLAlchemy database instance
│   ├── models.py               # User, Folder, File, Notification, Activity models
│   ├── requirements.txt        # Python package dependencies
│   ├── seed.py                 # Database initialization & demo account seeding
│   ├── smoke_test.py           # Automated test suite (25 assertions)
│   ├── supabase_schema.sql     # Complete PostgreSQL schema for Supabase
│   ├── .env.example            # Environment configuration template
│   └── routes/                 # Modular API blueprints
│       ├── dashboard.py        # Workspace stats & recent activity feed
│       ├── files.py            # Upload, list, update, download, trash, restore
│       ├── folders.py          # Create, rename, color-code, delete folders
│       ├── notifications.py    # System alerts & broadcast notifications
│       ├── reports.py          # Storage breakdown & CSV export
│       └── users.py            # Account management & role assignments
├── frontend/
│   └── cloud-document-manager.html  # Responsive single-page application
├── .gitignore
└── README.md
```

---

## Quick Start (Local Development)

### 1. Install Dependencies

```bash
cd backend
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Seed Demo Data

```bash
python seed.py
```

### 3. Run the Server

```bash
python app.py
```

Open your browser and navigate to:
```
http://localhost:5000
```

---

## Demo Accounts

All pre-seeded demo accounts share the password: `demo123`

| Name | Email | Role | Permissions |
| :--- | :--- | :--- | :--- |
| **Eleanor Vance** | `admin@demo.io` | `Admin` | Full access, user management, audit logs, reports export |
| **Marcus Thorne** | `staff@demo.io` | `Staff` | Reports overview, workspace document inspection |
| **Julian Croft** | `user@demo.io` | `User` | Isolated access (personal + shared files only) |

---

## Supabase PostgreSQL Setup

To connect to Supabase:

1. Copy `.env.example` to `.env` inside `backend/`:
   ```bash
   cp .env.example .env
   ```
2. Paste your Supabase database connection string:
   ```env
   DATABASE_URL=postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
   ```
3. Run the SQL statements from `backend/supabase_schema.sql` in the **Supabase SQL Editor** to create all tables and indexes.

---

## Automated Verification

Run the end-to-end smoke test suite:
```bash
python smoke_test.py
```
Validates authentication, role enforcement, upload/download, star/share, trash/restore, notifications, reports, and user administration across 25 assertions.
