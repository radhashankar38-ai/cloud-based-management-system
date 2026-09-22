-- =====================================================================
-- Cloud-Based Management System (CBMS) - Supabase Database Schema
-- Project ID: divmdirkiqpvojzfstop
-- =====================================================================

-- 1. USERS TABLE
CREATE TABLE IF NOT EXISTS public.users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user', -- 'admin' | 'staff' | 'user'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. FOLDERS TABLE
CREATE TABLE IF NOT EXISTS public.folders (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    color VARCHAR(20) DEFAULT 'yellow',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. FILES TABLE
CREATE TABLE IF NOT EXISTS public.files (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    stored_name VARCHAR(255) NOT NULL,
    size_bytes BIGINT DEFAULT 0,
    folder_id INTEGER REFERENCES public.folders(id) ON DELETE SET NULL,
    owner_id INTEGER NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    starred BOOLEAN DEFAULT FALSE,
    trashed BOOLEAN DEFAULT FALSE,
    share_enabled BOOLEAN DEFAULT FALSE,
    share_permission VARCHAR(10) DEFAULT 'view', -- 'view' | 'edit'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. NOTIFICATIONS TABLE
CREATE TABLE IF NOT EXISTS public.notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES public.users(id) ON DELETE CASCADE,
    target_role VARCHAR(20), -- e.g. 'admin' for role broadcasts
    message VARCHAR(255) NOT NULL,
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. ACTIVITY LOG TABLE
CREATE TABLE IF NOT EXISTS public.activity_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES public.users(id) ON DELETE SET NULL,
    message VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================================
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
CREATE INDEX IF NOT EXISTS idx_files_owner_id ON public.files(owner_id);
CREATE INDEX IF NOT EXISTS idx_files_folder_id ON public.files(folder_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON public.notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_log_user_id ON public.activity_log(user_id);

-- =====================================================================
-- PERMISSIONS & ACCESS (Supabase Roles: postgres, anon, authenticated, service_role)
-- =====================================================================
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres, anon, authenticated, service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres, anon, authenticated, service_role;

-- Row-level security: disabled by default for simplicity with Flask API / Supabase client
ALTER TABLE public.users DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.folders DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.files DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.activity_log DISABLE ROW LEVEL SECURITY;

-- =====================================================================
-- DEMO SEED DATA (Passwords hashed with Werkzeug scrypt: 'demo123')
-- =====================================================================

-- Initial Users
INSERT INTO public.users (id, name, email, password_hash, role) VALUES
(1, 'Priya Admin', 'admin@demo.io', 'scrypt:32768:8:1$zPJvquwUus40LBfo$fb09bb2e0ef21747dd130d33fcf3be4b08340b98b1350aeae9746e698d1e1f2a9c686b18c05afecb91125d457e4d71b900fcc0263608f4ff1fc33fd9c21a57f4', 'admin'),
(2, 'Ravi Staff', 'staff@demo.io', 'scrypt:32768:8:1$zPJvquwUus40LBfo$fb09bb2e0ef21747dd130d33fcf3be4b08340b98b1350aeae9746e698d1e1f2a9c686b18c05afecb91125d457e4d71b900fcc0263608f4ff1fc33fd9c21a57f4', 'staff'),
(3, 'Clara User', 'clara@demo.io', 'scrypt:32768:8:1$zPJvquwUus40LBfo$fb09bb2e0ef21747dd130d33fcf3be4b08340b98b1350aeae9746e698d1e1f2a9c686b18c05afecb91125d457e4d71b900fcc0263608f4ff1fc33fd9c21a57f4', 'user')
ON CONFLICT (id) DO NOTHING;

SELECT setval('users_id_seq', (SELECT COALESCE(MAX(id), 1) FROM public.users));

-- Initial Folders
INSERT INTO public.folders (id, name, color) VALUES
(1, 'Finance & Taxes', 'yellow'),
(2, 'Client Proposals', 'moss'),
(3, 'Operations 2026', 'gold')
ON CONFLICT (id) DO NOTHING;

SELECT setval('folders_id_seq', (SELECT COALESCE(MAX(id), 1) FROM public.folders));

-- Initial Files
INSERT INTO public.files (id, name, stored_name, size_bytes, folder_id, owner_id, starred, trashed, share_enabled, share_permission) VALUES
(1, 'Annual_Audit_2025.pdf', 'seed_report.txt', 1843200, 1, 1, TRUE, FALSE, TRUE, 'view'),
(2, 'Q3_Financial_Deck.key', 'seed_deck.txt', 4310000, 1, 2, FALSE, FALSE, FALSE, 'view'),
(3, 'Vendor_Master_Contract.docx', 'seed_cert.txt', 624100, 2, 2, TRUE, FALSE, TRUE, 'edit'),
(4, 'Board_Resolution_04.pdf', 'seed_resume.txt', 298000, 3, 1, FALSE, FALSE, FALSE, 'view'),
(5, 'Warehouse_Lease_Signed.pdf', 'seed_reading.txt', 812400, 3, 3, FALSE, FALSE, FALSE, 'view'),
(6, 'Staff_Training_Notes.txt', 'seed_ds_notes.txt', 45100, NULL, 3, FALSE, FALSE, FALSE, 'view')
ON CONFLICT (id) DO NOTHING;

SELECT setval('files_id_seq', (SELECT COALESCE(MAX(id), 1) FROM public.files));

-- Initial Notifications
INSERT INTO public.notifications (id, user_id, target_role, message, read) VALUES
(1, 1, NULL, 'Audit report filed successfully', TRUE),
(2, 2, NULL, 'Vendor contract signed and updated', FALSE),
(3, NULL, 'admin', 'System backup completed (5 files indexed)', FALSE)
ON CONFLICT (id) DO NOTHING;

SELECT setval('notifications_id_seq', (SELECT COALESCE(MAX(id), 1) FROM public.notifications));

-- Initial Activity Log
INSERT INTO public.activity_log (id, user_id, message) VALUES
(1, 1, 'Priya Admin logged in'),
(2, 1, 'Filed Annual_Audit_2025.pdf (1.8 MB)'),
(3, 2, 'Ravi Staff filed Q3_Financial_Deck.key (4.1 MB)'),
(4, 2, 'Shared Vendor_Master_Contract.docx'),
(5, 3, 'Clara User uploaded Warehouse_Lease_Signed.pdf'),
(6, 3, 'Clara User uploaded Staff_Training_Notes.txt')
ON CONFLICT (id) DO NOTHING;

SELECT setval('activity_log_id_seq', (SELECT COALESCE(MAX(id), 1) FROM public.activity_log));
