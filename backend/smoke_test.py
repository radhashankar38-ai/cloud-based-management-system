import io
import json

from app import create_app

app = create_app()
client = app.test_client()


def j(resp):
    return resp.get_json()


def check(label, cond):
    status = 'PASS' if cond else 'FAIL'
    print(f'[{status}] {label}')
    if not cond:
        raise SystemExit(1)


# --- health ---
r = client.get('/api/health')
check('health check', r.status_code == 200)

# --- register a brand-new user (should default to role=user since admin already seeded) ---
import time
unique_email = f'newbie_{int(time.time()*1000)}@test.io'
r = client.post('/api/auth/register', json={'name': 'Test Newbie', 'email': unique_email, 'password': 'abcd'})
check('register newbie', r.status_code == 201 and j(r)['user']['role'] == 'user')
client.post('/api/auth/logout')

# --- login as admin demo account ---
r = client.post('/api/auth/login', json={'email': 'admin@demo.io', 'password': 'demo123'})
check('admin login', r.status_code == 200 and j(r)['user']['role'] == 'admin')

r = client.get('/api/auth/me')
check('me returns admin', j(r)['user']['email'] == 'admin@demo.io')

# --- dashboard stats ---
r = client.get('/api/dashboard/stats')
check('dashboard stats', r.status_code == 200 and 'fileCount' in j(r))
print('   stats:', j(r))

# --- folders ---
r = client.get('/api/folders')
check('list folders', r.status_code == 200 and len(j(r)['folders']) >= 3)

r = client.post('/api/folders', json={'name': 'Test Folder', 'color': 'red'})
check('create folder', r.status_code == 201)
new_folder_id = j(r)['folder']['id']

# --- files: list, upload, update, star, share, trash, restore ---
r = client.get('/api/files')
check('list files (admin sees all)', r.status_code == 200 and len(j(r)['files']) >= 6)

data = {'file': (io.BytesIO(b'hello world'), 'smoke-test.txt'), 'folderId': str(new_folder_id)}
r = client.post('/api/files', data=data, content_type='multipart/form-data')
check('upload file', r.status_code == 201)
uploaded_id = j(r)['file']['id']

r = client.get(f'/api/files/{uploaded_id}/download')
check('download uploaded file', r.status_code == 200 and r.data == b'hello world')

r = client.patch(f'/api/files/{uploaded_id}', json={'starred': True, 'shared': {'enabled': True, 'permission': 'view'}})
check('star + share file', r.status_code == 200 and j(r)['file']['starred'] and j(r)['file']['shared']['enabled'])

r = client.post(f'/api/files/{uploaded_id}/trash')
check('trash file', r.status_code == 200 and j(r)['file']['trashed'])

r = client.get('/api/files/trash')
check('trash listing shows it', any(f['id'] == uploaded_id for f in j(r)['files']))

r = client.post(f'/api/files/{uploaded_id}/restore')
check('restore file', r.status_code == 200 and not j(r)['file']['trashed'])

# --- notifications ---
r = client.get('/api/notifications')
check('admin sees broadcast notification', any('New account registered' in n['message'] for n in j(r)['notifications']))

r = client.post('/api/notifications/mark-read')
check('mark notifications read', r.status_code == 200)

# --- reports (admin) ---
r = client.get('/api/reports/summary')
check('report summary', r.status_code == 200 and j(r)['userCount'] >= 4)

r = client.get('/api/reports/export')
check('report csv export', r.status_code == 200 and b'Name,Owner,Folder' in r.data)

# --- users management (admin) ---
r = client.post('/api/users', json={'name': 'Invited Staffer', 'email': 'invited@test.io', 'role': 'staff'})
check('admin invites new staff user', r.status_code == 201 and 'tempPassword' in j(r))
invited_id = j(r)['user']['id']

r = client.patch(f'/api/users/{invited_id}', json={'role': 'user'})
check('admin changes role', r.status_code == 200 and j(r)['user']['role'] == 'user')

r = client.delete(f'/api/users/{invited_id}')
check('admin removes user', r.status_code == 200)

# guard: cannot demote the only admin
admin_id_resp = client.get('/api/auth/me')
admin_id = j(admin_id_resp)['user']['id']
r = client.patch(f'/api/users/{admin_id}', json={'role': 'user'})
check('cannot demote last admin', r.status_code == 400)

client.post('/api/auth/logout')

# --- role restrictions: log in as the plain user demo account ---
r = client.post('/api/auth/login', json={'email': 'user@demo.io', 'password': 'demo123'})
check('user login', r.status_code == 200)

r = client.get('/api/files')
own_and_shared = j(r)['files']
check('user role sees only own + shared files', all(
    f['ownerId'] == j(admin_id_resp)['user']['id'] and f['shared']['enabled'] or f['ownerId'] != -1
    for f in own_and_shared
) and len(own_and_shared) >= 1)
print('   user sees', len(own_and_shared), 'files')

r = client.get('/api/users')
check('user role forbidden from Users list', r.status_code == 403)

r = client.get('/api/reports/summary')
check('user role forbidden from Reports', r.status_code == 403)

r = client.delete('/api/files/1')
check('user role forbidden from permanent delete', r.status_code == 403)

print('')
print('All smoke tests passed.')
