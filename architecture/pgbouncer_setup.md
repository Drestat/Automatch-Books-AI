# PgBouncer Configuration Guide for AutoMatch Books AI

## Overview
This guide explains how to set up external connection pooling with PgBouncer for serverless compatibility with Modal.

## Why PgBouncer?
- **Serverless Functions** create new database connections on every invocation
- **PostgreSQL** has a limited connection pool (typically 100-200 connections)
- **Connection Exhaustion** causes production failures when limits are exceeded
- **PgBouncer** acts as a lightweight connection pooler between the app and database

## Architecture
```
Modal Functions → PgBouncer (Transaction Mode) → PostgreSQL
(Ephemeral)       (Connection Pool)              (Limited Connections)
```

## Cloud Provider Options

### Option 1: Supabase (Recommended for Ease)
Supabase includes **Supavisor** (built-in PgBouncer alternative):

1. **Get Connection String**
   - Navigate to Supabase Dashboard → Settings → Database
   - Copy "Connection Pooling" string (port 6543, not 5432)
   - Format: `postgresql://user:pass@host:6543/db?pgbouncer=true`

2. **Update Environment Variables**
   ```bash
   DATABASE_URL=postgresql://user:pass@host:6543/db?pgbouncer=true
   ```

3. **Verify Configuration**
   - Supavisor automatically uses transaction pooling mode
   - No additional setup required

### Option 2: Neon (Serverless-Native)
Neon has built-in connection pooling:

1. **Get Pooled Connection String**
   - Navigate to Neon Dashboard → Connection Details
   - Select "Pooled connection" option
   - Copy the connection string

2. **Update Environment Variables**
   ```bash
   DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
   ```

### Option 3: AWS RDS Proxy
For AWS-hosted PostgreSQL:

1. **Create RDS Proxy**
   ```bash
   aws rds create-db-proxy \
     --db-proxy-name automatch-books-proxy \
     --engine-family POSTGRESQL \
     --auth <auth-config> \
     --role-arn <iam-role> \
     --vpc-subnet-ids <subnet-ids>
   ```

2. **Update Connection String**
   ```bash
   DATABASE_URL=postgresql://user:pass@proxy-endpoint:5432/db
   ```

### Option 4: Self-Hosted PgBouncer
For custom deployments:

1. **Install PgBouncer**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install pgbouncer
   
   # macOS
   brew install pgbouncer
   ```

2. **Configure `/etc/pgbouncer/pgbouncer.ini`**
   ```ini
   [databases]
   qbo_mirror = host=your-postgres-host port=5432 dbname=qbo_mirror
   
   [pgbouncer]
   listen_addr = 0.0.0.0
   listen_port = 6432
   auth_type = md5
   auth_file = /etc/pgbouncer/userlist.txt
   pool_mode = transaction
   max_client_conn = 1000
   default_pool_size = 20
   reserve_pool_size = 5
   reserve_pool_timeout = 3
   server_lifetime = 3600
   server_idle_timeout = 600
   ```

3. **Create User List** (`/etc/pgbouncer/userlist.txt`)
   ```
   "your_user" "md5<hashed_password>"
   ```

4. **Start PgBouncer**
   ```bash
   sudo systemctl start pgbouncer
   sudo systemctl enable pgbouncer
   ```

5. **Update Connection String**
   ```bash
   DATABASE_URL=postgresql://user:pass@pgbouncer-host:6432/qbo_mirror
   ```

## Verification

### 1. Test Connection
```bash
cd backend
python -c "from app.db.session import engine; print(engine.pool)"
```

**Expected Output:**
```
NullPool(Engine(postgresql://...))
```

### 2. Verify No Internal Pooling
```python
# backend/test_pooling.py
from app.db.session import engine
from sqlalchemy.pool import NullPool

assert isinstance(engine.pool, NullPool), "Engine should use NullPool"
print("✅ NullPool configured correctly")
```

### 3. Test Modal Function
```bash
modal run modal_app.py::sync_user_data --realm-id "test"
```

Check logs for connection errors. Should see clean execution without "too many connections" errors.

## Monitoring

### Connection Count Query
```sql
SELECT count(*) 
FROM pg_stat_activity 
WHERE datname = 'qbo_mirror';
```

**Healthy State:**
- Without PgBouncer: 50-100+ connections (one per Modal function)
- With PgBouncer: 5-20 connections (pooled)

### PgBouncer Stats
```bash
psql -h pgbouncer-host -p 6432 -U your_user pgbouncer -c "SHOW POOLS;"
```

## Troubleshooting

### Error: "remaining connection slots are reserved"
**Cause:** PostgreSQL connection limit reached  
**Solution:** Verify PgBouncer is in use, check `DATABASE_URL` points to pooler

### Error: "SSL connection has been closed unexpectedly"
**Cause:** Connection timeout or network issue  
**Solution:** Increase `connect_timeout` in `session.py`, check firewall rules

### Error: "server closed the connection unexpectedly"
**Cause:** Long-running query exceeded timeout  
**Solution:** Increase `statement_timeout` in `session.py` or optimize query

## Environment Variables Checklist

```bash
# .env file
DATABASE_URL=postgresql://user:pass@pgbouncer-host:6432/qbo_mirror?sslmode=require

# For Supabase
DATABASE_URL=postgresql://user:pass@host:6543/db?pgbouncer=true

# For Neon
DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
```

## Next Steps
1. Choose a PgBouncer provider (Supabase recommended)
2. Update `DATABASE_URL` in `.env` and Modal secrets
3. Deploy updated `modal_app.py`
4. Monitor connection counts
5. Update PLAN.md with deployment status
