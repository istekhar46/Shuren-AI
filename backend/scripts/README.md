# Database Scripts

Essential scripts for database setup and management.

## Scripts Overview

### 1. setup_databases_simple.bat
**Purpose**: Create local development and test databases

**Usage**:
```bash
cd backend/scripts
.\setup_databases_simple.bat
```

**What it does**:
- Creates `shuren_dev_db` - For local development
- Creates `shuren_test_db` - For running tests
- Checks if databases already exist (won't recreate)

**When to use**:
- First-time setup
- After resetting PostgreSQL
- If databases were accidentally deleted

---

### 2. test_connection.py
**Purpose**: Test database connections and verify setup

**Usage**:
```bash
cd backend
poetry run python scripts/test_connection.py
```

**What it does**:
- Tests connection to `shuren_dev_db`
- Tests connection to `shuren_test_db`
- Shows table count in each database
- Verifies database isolation

**When to use**:
- After running setup_databases_simple.bat
- To verify database configuration
- Troubleshooting connection issues

---

### 3. reset_db.py
**Purpose**: Drop all tables and reset database to clean state

**Usage**:
```bash
cd backend
poetry run python scripts/reset_db.py
```

**What it does**:
- Drops all tables in the public schema
- Resets database to empty state
- **WARNING**: This deletes all data!

**When to use**:
- Development database needs clean slate
- After major schema changes
- Testing fresh migrations

**Important**: 
- Only affects the database in your `.env` file
- Never run against production!
- Run migrations after reset: `poetry run alembic upgrade head`

---

### 4. check_db.py
**Purpose**: Check database status and connection

**Usage**:
```bash
cd backend
poetry run python scripts/check_db.py
```

**What it does**:
- Checks database connection
- Shows current database name
- Lists all tables
- Displays basic database info

**When to use**:
- Quick database status check
- Verify which database you're connected to
- See what tables exist

---

## Quick Setup Guide

### First Time Setup

1. **Create databases**:
   ```bash
   cd backend/scripts
   .\setup_databases_simple.bat
   ```

2. **Verify setup**:
   ```bash
   cd backend
   poetry run python scripts/test_connection.py
   ```

3. **Run migrations**:
   ```bash
   poetry run alembic upgrade head
   ```

4. **Verify tables created**:
   ```bash
   poetry run python scripts/check_db.py
   ```

### Reset Development Database

1. **Reset database**:
   ```bash
   poetry run python scripts/reset_db.py
   ```

2. **Run migrations**:
   ```bash
   poetry run alembic upgrade head
   ```

## Database Architecture

This project uses three separate databases:

| Database | Purpose | Location |
|----------|---------|----------|
| `defaultdb` | Production | Aiven Cloud |
| `shuren_dev_db` | Development | localhost:5432 |
| `shuren_test_db` | Testing | localhost:5432 |

**Why?**
- Tests drop all tables after each run (correct behavior)
- Separate databases prevent data loss
- Production is safe from local operations

## Troubleshooting

### "Database does not exist"
```bash
cd backend/scripts
.\setup_databases_simple.bat
```

### "Connection refused"
- Check PostgreSQL is running
- Verify port 5432 is open
- Check credentials in `.env` file

### "Password authentication failed"
- Update password in `.env` file
- Ensure password is URL-encoded: `ist@123` → `ist%40123`

### Wrong database connected
```bash
# Check current database
grep DATABASE_URL backend/.env

# Should show localhost, not aivencloud.com
```

## Related Documentation

- [DATABASE_SETUP.md](../DATABASE_SETUP.md) - Complete setup guide
- [SETUP_COMPLETE.md](../SETUP_COMPLETE.md) - Verification guide
- [README.md](../README.md) - Main project documentation
