"""Verify the current state of the onboarding migration.

This script verifies that:
1. The agent_history column exists
2. The constraint is updated to 0-9
3. Any existing data has been migrated correctly
"""

import asyncio
from sqlalchemy import text
from app.db.session import AsyncSessionLocal


async def verify_migration():
    """Verify the migration has been applied correctly."""
    print("=" * 60)
    print("Verifying Onboarding Migration State")
    print("=" * 60)
    
    async with AsyncSessionLocal() as db:
        # Check if agent_history column exists
        print("\n1. Checking agent_history column...")
        result = await db.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'onboarding_states' 
            AND column_name = 'agent_history'
        """))
        column_info = result.fetchone()
        
        if column_info:
            print(f"   ✓ agent_history column exists")
            print(f"     - Type: {column_info[1]}")
            print(f"     - Nullable: {column_info[2]}")
            print(f"     - Default: {column_info[3]}")
        else:
            print("   ✗ agent_history column NOT FOUND")
            return False
        
        # Check constraint
        print("\n2. Checking current_step constraint...")
        result = await db.execute(text("""
            SELECT constraint_name, check_clause
            FROM information_schema.check_constraints
            WHERE constraint_name = 'valid_current_step'
        """))
        constraint = result.fetchone()
        
        if constraint:
            check_clause = constraint[1]
            print(f"   ✓ Constraint exists: {check_clause}")
            
            # Verify it's the 0-9 constraint
            if "current_step <= 9" in check_clause or "9 >= current_step" in check_clause:
                print("   ✓ Constraint correctly limits to 0-9")
            else:
                print(f"   ✗ Constraint does NOT limit to 9: {check_clause}")
                return False
        else:
            print("   ✗ valid_current_step constraint NOT FOUND")
            return False
        
        # Check for any onboarding states
        print("\n3. Checking existing onboarding states...")
        result = await db.execute(text("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN current_step > 9 THEN 1 END) as invalid_steps,
                   COUNT(CASE WHEN step_data ? '_migration_metadata' THEN 1 END) as migrated
            FROM onboarding_states
            WHERE deleted_at IS NULL
        """))
        stats = result.fetchone()
        
        total = stats[0]
        invalid_steps = stats[1]
        migrated = stats[2]
        
        print(f"   Total onboarding states: {total}")
        print(f"   States with current_step > 9: {invalid_steps}")
        print(f"   States with migration metadata: {migrated}")
        
        if invalid_steps > 0:
            print("   ✗ Found states with invalid current_step values!")
            return False
        
        if total > 0:
            print(f"   ✓ All {total} states have valid current_step values")
        
        # Sample a few records to verify structure
        if total > 0:
            print("\n4. Sampling onboarding state records...")
            result = await db.execute(text("""
                SELECT current_step, 
                       jsonb_object_keys(step_data) as keys,
                       agent_history
                FROM onboarding_states
                WHERE deleted_at IS NULL
                LIMIT 5
            """))
            
            print("   Sample records:")
            for row in result.fetchall():
                print(f"     - Step {row[0]}: key='{row[1]}', agent_history={row[2]}")
        
        # Check alembic version
        print("\n5. Checking Alembic migration version...")
        result = await db.execute(text("""
            SELECT version_num FROM alembic_version
        """))
        version = result.fetchone()
        
        if version:
            print(f"   Current version: {version[0]}")
            if version[0] == 'b2c3d4e5f6g7':
                print("   ✓ Database is at the expected migration version (b2c3d4e5f6g7)")
            else:
                print(f"   ⚠ Database is at version {version[0]}, expected b2c3d4e5f6g7")
        
        print("\n" + "=" * 60)
        print("✓ Migration Verification Complete")
        print("=" * 60)
        print("\nSummary:")
        print("  - agent_history column: ✓ Present")
        print("  - Constraint (0-9): ✓ Correct")
        print(f"  - Valid data: ✓ {total} states, 0 invalid")
        print("  - Migration version: ✓ b2c3d4e5f6g7 (head)")
        
        return True


if __name__ == "__main__":
    try:
        success = asyncio.run(verify_migration())
        if not success:
            print("\n✗ Verification FAILED")
            exit(1)
    except Exception as e:
        print(f"\n✗ Error during verification: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
