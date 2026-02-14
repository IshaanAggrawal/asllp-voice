# 🗄️ Supabase Database Setup Guide

## Quick Start

### 1. Access Supabase SQL Editor
1. Go to your Supabase project dashboard
2. Click on "SQL Editor" in the left sidebar
3. Click "New Query"

### 2. Run the Schema
1. Copy the entire contents of `supabase_schema.sql`
2. Paste into the Supabase SQL Editor
3. Click "Run" button
4. Wait for confirmation: "Success. No rows returned"

### 3. Verify Setup
Run this query in SQL Editor to verify tables were created:
```sql
SELECT tablename 
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY tablename;
```

You should see:
- `auth_user`
- `agents_agentconfiguration`
- `agents_conversationsession`
- `agents_conversationlog`

---

## Schema Overview

### Tables Created

#### 1. **auth_user** (Django compatible)
- User authentication and profiles
- Fields: id, username, email, password, etc.
- Indexes: username, email

#### 2. **agents_agentconfiguration**
- Custom AI agent definitions
- Foreign key to `auth_user` (user isolation)
- Auto-generated UUID primary key
- Auto-updating `updated_at` timestamp

#### 3. **agents_conversationsession**
- Voice call sessions
- Links agent to user
- Tracks status (active/ended/error)
- Stores metrics (turns, latency)

#### 4. **agents_conversationlog**
- Individual conversation turns
- Transcripts and intents
- Performance metrics

---

## Security Features

### Row Level Security (RLS)
✅ Enabled on all agent/session tables  
✅ Users can only access their own data  
✅ Enforced at database level  

**How it works:**
```sql
-- Users can only see their own agents
CREATE POLICY agents_user_isolation ON agents_agentconfiguration
    FOR ALL
    USING (user_id = current_setting('app.current_user_id')::INTEGER);
```

### Foreign Key Constraints
✅ `ON DELETE CASCADE` - Deleting user removes all their data  
✅ Referential integrity enforced  
✅ Prevents orphaned records  

---

## Analytics Views

### user_statistics
Get overview of each user's activity:
```sql
SELECT * FROM user_statistics WHERE username = 'testuser';
```

Returns:
- Total agents created
- Total sessions
- Active sessions
- Last session date

### agent_performance
Analyze agent usage and performance:
```sql
SELECT * FROM agent_performance ORDER BY total_sessions DESC;
```

Returns:
- Agent usage stats
- Average turns per session
- Average latency
- Last used date

---

## Utility Functions

### Get Agent Count
```sql
SELECT get_user_agent_count(1);  -- Returns count for user ID 1
```

### Get Active Sessions
```sql
SELECT get_active_sessions_count(1);  -- Active sessions for user ID 1
```

---

## Django Integration

After running the SQL schema in Supabase:

### 1. Update .env
```bash
DB_HOST=aws-1-ap-south-1.pooler.supabase.com
DB_USER=postgres.fqfqzeoqiecimugchaer
DB_PASSWORD=your-actual-password
DB_NAME=postgres
DB_PORT=6543
```

### 2. Run Django Migrations
```bash
cd backend/django_app
python manage.py migrate
```

Django will:
- Detect existing tables
- Create migration tracking table
- Sync schema with models
- Apply any additional migrations

### 3. Create Superuser
```bash
python manage.py createsuperuser
```

---

## Testing Database Connection

### Python Test Script
```python
import psycopg2

conn = psycopg2.connect(
    dbname="postgres",
    user="postgres.fqfqzeoqiecimugchaer",
    password="your-password",
    host="aws-1-ap-south-1.pooler.supabase.com",
    port="6543"
)

cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM auth_user;")
print(f"Users: {cursor.fetchone()[0]}")

cursor.close()
conn.close()
```

### SQL Test
Run in Supabase SQL Editor:
```sql
-- Test user isolation
INSERT INTO auth_user (username, email, password)
VALUES ('testuser', 'test@example.com', 'test123')
RETURNING id, username;

-- Create test agent
INSERT INTO agents_agentconfiguration (user_id, name, system_prompt)
VALUES (1, 'Test Agent', 'You are a helpful assistant')
RETURNING id, name;
```

---

## Interview Talking Points

### Database Architecture
- "We use PostgreSQL on Supabase for scalability and managed hosting"
- "Row-level security ensures users can only access their own data"
- "Foreign key constraints maintain referential integrity"
- "Indexes optimize common query patterns"

### Security Design
- "Database-level isolation prevents unauthorized data access"
- "ON DELETE CASCADE ensures clean data removal"
- "RLS policies work even with direct SQL access"
- "Compatible with Django ORM for developer productivity"

### Production Considerations
- "Supabase provides automatic backups"
- "Connection pooling handles concurrent requests"
- "Read replicas available for scaling reads"
- "PostgreSQL extensions available (PostGIS, pg_vector, etc.)"

---

## Common Issues & Solutions

### Issue: "relation already exists"
**Solution:** Tables already created. Safe to ignore or drop and recreate:
```sql
DROP TABLE IF EXISTS agents_conversationlog CASCADE;
DROP TABLE IF EXISTS agents_conversationsession CASCADE;
DROP TABLE IF EXISTS agents_agentconfiguration CASCADE;
DROP TABLE IF EXISTS auth_user CASCADE;
```

### Issue: Django migrations fail
**Solution:** Django expects to manage schema. Either:
1. Run migrations first, then manual SQL
2. Use `--fake-initial` flag: `python manage.py migrate --fake-initial`

### Issue: Can't connect from Django
**Solution:** Check:
- Password is correct (no [YOUR-PASSWORD] placeholder)
- `psycopg2-binary` installed: `pip install psycopg2-binary`
- Firewall allows outbound connections on port 6543
- Supabase project is not paused

---

## Production Checklist

Before deploying:
- [ ] Update `DJANGO_SECRET_KEY` in `.env`
- [ ] Set `DJANGO_DEBUG=False`
- [ ] Use strong database password
- [ ] Enable Supabase backups
- [ ] Set up monitoring/alerts
- [ ] Configure allowed hosts
- [ ] Enable SSL/TLS
- [ ] Set up logging

---

**Your Supabase database is production-ready!** 🚀
