# ohra-backend

## User Management

Add users manually: `docker-compose exec backend sh -c "cd /app/projects/ohra-backend && python3 << 'EOF' ... (see scripts/add_users.py for full script)"`

example:

```bash
$ docker-compose exec backend sh -c "cd /app/projects/ohra-backend && python3 << 'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path('/app/projects/ohra-backend/src')))
import sqlite3
import uuid
from datetime import datetime
users = [
    {'email': 'eunhee.jo@a-ha.io', 'name': '조은희'},
    {'email': 'inseok.lee@a-ha.io', 'name': '이인석'},
    {'email': 'dj.sull@a-ha.io', 'name': '덕덕'},
]
db_path = Path('/app/projects/ohra-backend/data/database.db')
if not db_path.exists():
    print(f'Database not found at: {db_path}')
    sys.exit(1)
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()
now = datetime.now()
added_count = 0
skipped_count = 0
for user_info in users:
    email = user_info['email']
    name = user_info['name']
    cursor.execute('SELECT id, email FROM ohra_user WHERE email = ?', (email,))
    existing = cursor.fetchone()
    if existing:
        print(f'User already exists: {email} (ID: {existing[0]})')
        skipped_count += 1
    else:
        user_id = str(uuid.uuid4())
        cursor.execute('INSERT INTO ohra_user (id, email, name, is_active, is_admin, external_user_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (user_id, email, name, True, False, None, now, now))
        conn.commit()
        print(f'User created: {email} / {name} (ID: {user_id})')
        added_count += 1
conn.close()
print(f'Done! Added: {added_count}, Skipped: {skipped_count}')
EOF"
```
