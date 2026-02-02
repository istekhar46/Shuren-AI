# Database Migrations Guide

## What Are Database Migrations?

Database migrations are version-controlled changes to your database schema. Think of them like Git commits, but for your database structure instead of code. Each migration represents a specific change (adding a table, modifying a column, creating an index, etc.) and can be applied or rolled back.

### Why Use Migrations?

**Without migrations:**
- Developers manually run SQL scripts
- No history of schema changes
- Hard to sync database state across environments
- Difficult to rollback changes
- Team members have inconsistent database schemas

**With migrations:**
- Automated, repeatable schema changes
- Version-controlled database evolution
- Easy to sync across development, staging, and production
- Can rollback changes if needed
- Everyone on the team has the same schema

## How Migrations Work

### The Migration Lifecycle

1. **Create a migration** - Generate a new migration file describing the change
2. **Review the migration** - Check the auto-generated SQL is correct
3. **Apply the migration** - Run the migration to update the database
4. **Track the state** - Alembic records which migrations have been applied

### Migration Files

Migrations live in `backend/alembic/versions/`. Each file has:
- A unique revision ID (e.g., `3a4feffbb7a1`)
- A timestamp and description
- An `upgrade()` function (applies the change)
- A `downgrade()` function (reverts the change)

Example migration file:
```python
"""add_workout_and_chat_tables

Revision ID: 3a4feffbb7a1
Revises: 0c90191dbca7
Create Date: 2026-01-30 14:47:22.925842
"""

def upgrade() -> None:
    """Apply the schema change."""
    op.create_table(
        'chat_sessions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        # ... more columns
    )

def downgrade() -> None:
    """Revert the schema change."""
    op.drop_table('chat_sessions')
```

## Using Alembic (Our Migration Tool)

Shuren uses **Alembic**, a database migration tool for SQLAlchemy. All commands should be run from the `backend/` directory with `poetry run` prefix.

### Common Commands

#### 1. Check Current Migration State
```bash
poetry run alembic current
```
Shows which migration your database is currently at.

#### 2. View Migration History
```bash
poetry run alembic history
```
Lists all available migrations in order.

#### 3. Create a New Migration

**Auto-generate from model changes (recommended):**
```bash
poetry run alembic revision --autogenerate -m "add user preferences table"
```
Alembic compares your SQLAlchemy models to the database and generates a migration automatically.

**Create empty migration (manual):**
```bash
poetry run alembic revision -m "add custom index"
```
Creates an empty migration file you fill in manually.

#### 4. Apply Migrations

**Upgrade to latest:**
```bash
poetry run alembic upgrade head
```
Applies all pending migrations.

**Upgrade one step:**
```bash
poetry run alembic upgrade +1
```
Applies just the next migration.

**Upgrade to specific revision:**
```bash
poetry run alembic upgrade 3a4feffbb7a1
```
Upgrades to a specific migration.

#### 5. Rollback Migrations

**Downgrade one step:**
```bash
poetry run alembic downgrade -1
```
Reverts the most recent migration.

**Downgrade to specific revision:**
```bash
poetry run alembic downgrade 0c90191dbca7
```
Rolls back to a specific migration.

**Downgrade all:**
```bash
poetry run alembic downgrade base
```
Reverts all migrations (empty database).

#### 6. Fix Migration State Issues

**Mark database as being at a specific version (without running migrations):**
```bash
poetry run alembic stamp head
```
Useful when you manually created tables or the migration state is out of sync.

## Workflow: Making Schema Changes

### Step 1: Update Your Models
Edit the SQLAlchemy model in `backend/app/models/`:

```python
# backend/app/models/user.py
class User(BaseModel):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    # NEW: Add a field
    phone_number = Column(String(20), nullable=True)
```

### Step 2: Generate Migration
```bash
cd backend
poetry run alembic revision --autogenerate -m "add phone number to users"
```

### Step 3: Review the Generated Migration
Open the new file in `backend/alembic/versions/`. Check that:
- The `upgrade()` function adds the column correctly
- The `downgrade()` function removes it
- Data types are correct
- Constraints are appropriate

Example generated migration:
```python
def upgrade() -> None:
    op.add_column('users', sa.Column('phone_number', sa.String(length=20), nullable=True))

def downgrade() -> None:
    op.drop_column('users', 'phone_number')
```

### Step 4: Apply the Migration
```bash
poetry run alembic upgrade head
```

### Step 5: Verify
Check your database to confirm the change was applied:
```bash
# Connect to PostgreSQL and check
\d users
```

## Best Practices

### DO ✅

1. **Always review auto-generated migrations** - Alembic isn't perfect, check the SQL
2. **Use descriptive migration messages** - `"add user preferences"` not `"update db"`
3. **Test migrations on a copy of production data** - Catch issues before deployment
4. **Keep migrations small and focused** - One logical change per migration
5. **Never edit applied migrations** - Create a new migration to fix issues
6. **Commit migrations to version control** - They're part of your codebase
7. **Run migrations as part of deployment** - Automate with CI/CD

### DON'T ❌

1. **Don't manually modify the database** - Always use migrations
2. **Don't delete old migrations** - They're your schema history
3. **Don't edit migrations after they're applied** - Create a new one instead
4. **Don't skip reviewing auto-generated migrations** - They can be wrong
5. **Don't run migrations directly in production** - Test in staging first

## Common Scenarios

### Scenario 1: Adding a New Table

1. Create the model in `backend/app/models/`
2. Import it in `backend/app/models/__init__.py`
3. Generate migration: `poetry run alembic revision --autogenerate -m "create notifications table"`
4. Review and apply: `poetry run alembic upgrade head`

### Scenario 2: Modifying an Existing Column

1. Update the model (e.g., change `nullable=False` to `nullable=True`)
2. Generate migration: `poetry run alembic revision --autogenerate -m "make email optional"`
3. Review the migration - may need to handle existing data
4. Apply: `poetry run alembic upgrade head`

### Scenario 3: Adding Data (Seed Data)

Migrations can also insert data:

```python
def upgrade() -> None:
    # Create table
    op.create_table('roles', ...)
    
    # Insert seed data
    op.execute("""
        INSERT INTO roles (id, name) VALUES 
        (gen_random_uuid(), 'admin'),
        (gen_random_uuid(), 'user')
    """)
```

### Scenario 4: Complex Schema Changes

For complex changes (renaming columns, splitting tables), write migrations manually:

```python
def upgrade() -> None:
    # Rename column
    op.alter_column('users', 'name', new_column_name='full_name')
    
    # Add index
    op.create_index('idx_users_email', 'users', ['email'])
    
    # Add constraint
    op.create_check_constraint(
        'valid_email',
        'users',
        "email LIKE '%@%'"
    )
```

### Scenario 5: Migration State Out of Sync

**Problem:** Database has tables but Alembic thinks migrations haven't run.

**Solution:**
```bash
# Mark database as being at latest version
poetry run alembic stamp head
```

**Problem:** Migration fails halfway through.

**Solution:**
```bash
# Rollback the failed migration
poetry run alembic downgrade -1

# Fix the migration file
# Try again
poetry run alembic upgrade head
```

## Troubleshooting

### Error: "relation already exists"

**Cause:** Database has tables that the migration is trying to create.

**Fix:**
```bash
poetry run alembic stamp head
```

### Error: "Can't locate revision"

**Cause:** Migration files are missing or alembic_version table is corrupted.

**Fix:**
```bash
# Check what migrations exist
poetry run alembic history

# Manually set to a known good state
poetry run alembic stamp <revision_id>
```

### Error: "Target database is not up to date"

**Cause:** Trying to create a migration when pending migrations exist.

**Fix:**
```bash
# Apply pending migrations first
poetry run alembic upgrade head

# Then create new migration
poetry run alembic revision --autogenerate -m "my change"
```

## Migration Checklist

Before deploying a migration to production:

- [ ] Migration tested on local database
- [ ] Migration tested on staging with production-like data
- [ ] Downgrade tested (can rollback if needed)
- [ ] Migration is idempotent (can run multiple times safely)
- [ ] Data migration handles existing records correctly
- [ ] Indexes added for new columns that will be queried
- [ ] Foreign key constraints are correct
- [ ] No breaking changes without a deprecation plan
- [ ] Team reviewed the migration
- [ ] Backup plan exists if migration fails

## Integration with Development Workflow

### Local Development

The `run_local.bat` script automatically runs migrations:
```bash
.\run_local.bat
# Runs: poetry run alembic upgrade head
# Then starts the server
```

### CI/CD Pipeline

Migrations should run automatically during deployment:
```yaml
# Example deployment step
- name: Run database migrations
  run: |
    cd backend
    poetry run alembic upgrade head
```

### Team Collaboration

When pulling changes from Git:
1. Pull the latest code
2. Check for new migrations: `poetry run alembic history`
3. Apply them: `poetry run alembic upgrade head`
4. Start developing

## Advanced Topics

### Branching and Merging

When multiple developers create migrations simultaneously:

```bash
# Check for multiple heads
poetry run alembic heads

# Merge them
poetry run alembic merge -m "merge migrations" <rev1> <rev2>
```

### Data Migrations

Migrations can transform data, not just schema:

```python
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    # Add new column
    op.add_column('users', sa.Column('full_name', sa.String(255)))
    
    # Migrate data from old columns
    connection = op.get_bind()
    connection.execute("""
        UPDATE users 
        SET full_name = first_name || ' ' || last_name
        WHERE full_name IS NULL
    """)
    
    # Drop old columns
    op.drop_column('users', 'first_name')
    op.drop_column('users', 'last_name')
```

### Testing Migrations

Write tests for complex migrations:

```python
# tests/test_migrations.py
def test_user_migration():
    # Setup: Create old schema
    # Run: Apply migration
    # Assert: New schema is correct
    pass
```

## Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- Project migrations: `backend/alembic/versions/`
- Migration config: `backend/alembic.ini`
- Migration environment: `backend/alembic/env.py`

## Quick Reference

```bash
# Check current state
poetry run alembic current

# View history
poetry run alembic history

# Create migration
poetry run alembic revision --autogenerate -m "description"

# Apply migrations
poetry run alembic upgrade head

# Rollback one migration
poetry run alembic downgrade -1

# Fix state issues
poetry run alembic stamp head
```

---

**Remember:** Migrations are your database's version control. Treat them with the same care as your code!
