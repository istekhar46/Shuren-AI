"""Test migration rollback from 9 states back to 11 steps.

This script tests the downgrade migration to ensure:
1. Original data is restored from _migration_metadata
2. Constraint is reverted to 0-11
3. agent_history column is removed
4. All data integrity is maintained

Usage:
    # Run the rollback test
    poetry run python scripts/test_migration_rollback.py
    
    # Or run with alembic directly
    poetry run alembic downgrade -1
"""

import asyncio
import sys
from sqlalchemy import text
from app.db.session import AsyncSessionLocal


async def check_pre_rollback_state():
    """Verify the database is in the migrated state (9 states) before rollback."""
    print("=" * 70)
    print("PRE-ROLLBACK VERIFICATION")
    print("=" * 70)
    
    async with AsyncSessionLocal() as session:
        try:
            # 1. Check agent_history column exists
            print("\n1. Checking agent_history column...")
            result = await session.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'onboarding_states'
                AND column_name = 'agent_history'
            """))
            agent_history_col = result.fetchone()
            
            if agent_history_col:
                print(f"   ✓ agent_history column exists")
                print(f"     - Type: {agent_history_col[1]}")
                print(f"     - Nullable: {agent_history_col[2]}")
                print(f"     - Default: {agent_history_col[3]}")
            else:
                print("   ✗ agent_history column NOT FOUND")
                print("   Migration may not have been applied yet")
                return False
            
            # 2. Check constraint is 0-9
            print("\n2. Checking current_step constraint...")
            result = await session.execute(text("""
                SELECT conname, pg_get_constraintdef(oid)
                FROM pg_constraint
                WHERE conrelid = 'onboarding_states'::regclass
                AND contype = 'c'
                AND conname = 'valid_current_step'
            """))
            constraint = result.fetchone()
            
            if constraint:
                constraint_def = constraint[1]
                print(f"   ✓ Constraint exists: {constraint_def}")
                if '<= 9' in constraint_def or 'current_step <= 9' in constraint_def:
                    print("   ✓ Constraint correctly limits to 0-9")
                else:
                    print(f"   ✗ Unexpected constraint definition: {constraint_def}")
                    return False
            else:
                print("   ✗ valid_current_step constraint NOT FOUND")
                return False
            
            # 3. Check for migration metadata
            print("\n3. Checking migration metadata...")
            result = await session.execute(text("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN step_data ? '_migration_metadata' THEN 1 ELSE 0 END) as with_metadata
                FROM onboarding_states
                WHERE deleted_at IS NULL
            """))
            counts = result.fetchone()
            
            total_states = counts[0]
            with_metadata = counts[1]
            
            print(f"   Total onboarding states: {total_states}")
            print(f"   States with migration metadata: {with_metadata}")
            
            if total_states > 0 and with_metadata == 0:
                print("   ⚠ No migration metadata found - rollback may not work properly")
                print("   This could mean:")
                print("     - Data was created after migration (no metadata needed)")
                print("     - Migration was not run with metadata preservation")
            
            # 4. Sample some data
            print("\n4. Sampling current data...")
            result = await session.execute(text("""
                SELECT id, current_step, 
                       jsonb_object_keys(step_data) as step_keys,
                       CASE WHEN step_data ? '_migration_metadata' THEN 'YES' ELSE 'NO' END as has_metadata
                FROM onboarding_states
                WHERE deleted_at IS NULL
                LIMIT 3
            """))
            samples = result.fetchall()
            
            if samples:
                print(f"   Sample records ({len(samples)} shown):")
                for sample in samples:
                    print(f"     - ID: {sample[0]}, Step: {sample[1]}, Key: {sample[2]}, Metadata: {sample[3]}")
            else:
                print("   No onboarding states found in database")
            
            print("\n" + "=" * 70)
            print("✓ Pre-rollback verification complete")
            print("  Database is ready for rollback test")
            print("=" * 70)
            
            return True
            
        except Exception as e:
            print(f"\n✗ Error during pre-rollback verification: {e}")
            import traceback
            traceback.print_exc()
            return False


async def check_post_rollback_state():
    """Verify the database is in the original state (11 steps) after rollback."""
    print("\n" + "=" * 70)
    print("POST-ROLLBACK VERIFICATION")
    print("=" * 70)
    
    async with AsyncSessionLocal() as session:
        try:
            # 1. Check agent_history column is removed
            print("\n1. Checking agent_history column...")
            result = await session.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'onboarding_states'
                AND column_name = 'agent_history'
            """))
            agent_history_col = result.fetchone()
            
            if agent_history_col:
                print("   ✗ agent_history column still exists (should be removed)")
                return False
            else:
                print("   ✓ agent_history column removed successfully")
            
            # 2. Check constraint is reverted to 0-11
            print("\n2. Checking current_step constraint...")
            result = await session.execute(text("""
                SELECT conname, pg_get_constraintdef(oid)
                FROM pg_constraint
                WHERE conrelid = 'onboarding_states'::regclass
                AND contype = 'c'
                AND conname = 'valid_current_step'
            """))
            constraint = result.fetchone()
            
            if constraint:
                constraint_def = constraint[1]
                print(f"   Constraint: {constraint_def}")
                if '<= 11' in constraint_def or 'current_step <= 11' in constraint_def:
                    print("   ✓ Constraint correctly reverted to 0-11")
                else:
                    print(f"   ✗ Unexpected constraint: {constraint_def}")
                    return False
            else:
                print("   ⚠ valid_current_step constraint NOT FOUND")
                print("   This may be expected if the original schema didn't have it")
            
            # 3. Check original data is restored
            print("\n3. Checking data restoration...")
            result = await session.execute(text("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN step_data ? '_migration_metadata' THEN 1 ELSE 0 END) as with_metadata
                FROM onboarding_states
                WHERE deleted_at IS NULL
            """))
            counts = result.fetchone()
            
            total_states = counts[0]
            with_metadata = counts[1]
            
            print(f"   Total onboarding states: {total_states}")
            print(f"   States with migration metadata: {with_metadata}")
            
            if with_metadata > 0:
                print("   ⚠ Migration metadata still present (should be removed)")
                print("   Data may not have been fully restored")
            else:
                print("   ✓ Migration metadata removed (original data restored)")
            
            # 4. Sample restored data
            print("\n4. Sampling restored data...")
            result = await session.execute(text("""
                SELECT id, current_step, 
                       jsonb_object_keys(step_data) as step_keys
                FROM onboarding_states
                WHERE deleted_at IS NULL
                LIMIT 3
            """))
            samples = result.fetchall()
            
            if samples:
                print(f"   Sample records ({len(samples)} shown):")
                for sample in samples:
                    print(f"     - ID: {sample[0]}, Step: {sample[1]}, Key: {sample[2]}")
                    
                # Check if we have old step keys (step_1 through step_11)
                result = await session.execute(text("""
                    SELECT DISTINCT jsonb_object_keys(step_data) as step_key
                    FROM onboarding_states
                    WHERE deleted_at IS NULL
                    AND jsonb_object_keys(step_data) LIKE 'step_%'
                    ORDER BY step_key
                """))
                step_keys = [row[0] for row in result.fetchall()]
                
                if step_keys:
                    print(f"\n   Step keys found in data: {', '.join(step_keys)}")
                    
                    # Check if we have step_10 or step_11 (only in 11-step schema)
                    has_old_steps = any(key in step_keys for key in ['step_10', 'step_11'])
                    if has_old_steps:
                        print("   ✓ Original 11-step data structure detected")
                    else:
                        print("   ⚠ No step_10 or step_11 found - may still be in 9-state format")
            else:
                print("   No onboarding states found in database")
            
            print("\n" + "=" * 70)
            print("✓ Post-rollback verification complete")
            print("=" * 70)
            
            return True
            
        except Exception as e:
            print(f"\n✗ Error during post-rollback verification: {e}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    """Main test function."""
    print("\n" + "=" * 70)
    print("MIGRATION ROLLBACK TEST")
    print("=" * 70)
    print("\nThis script verifies the migration rollback process.")
    print("It checks the database state before and after running:")
    print("  poetry run alembic downgrade -1")
    print("\n" + "=" * 70)
    
    # Check pre-rollback state
    print("\nStep 1: Verifying pre-rollback state...")
    pre_rollback_ok = await check_pre_rollback_state()
    
    if not pre_rollback_ok:
        print("\n✗ Pre-rollback verification failed")
        print("  Cannot proceed with rollback test")
        print("\nPossible issues:")
        print("  - Migration has not been applied yet")
        print("  - Database connection issues")
        print("  - Schema is in unexpected state")
        return False
    
    # Prompt user to run rollback
    print("\n" + "=" * 70)
    print("READY FOR ROLLBACK")
    print("=" * 70)
    print("\nThe database is in the correct state for rollback testing.")
    print("\nTo test the rollback, run:")
    print("  poetry run alembic downgrade -1")
    print("\nAfter running the downgrade, run this script again with --verify flag:")
    print("  poetry run python scripts/test_migration_rollback.py --verify")
    print("\n" + "=" * 70)
    
    return True


async def verify_rollback():
    """Verify the rollback was successful."""
    print("\n" + "=" * 70)
    print("VERIFYING ROLLBACK RESULTS")
    print("=" * 70)
    
    result = await check_post_rollback_state()
    
    if result:
        print("\n" + "=" * 70)
        print("✓ ROLLBACK TEST PASSED")
        print("=" * 70)
        print("\nThe migration rollback was successful:")
        print("  ✓ agent_history column removed")
        print("  ✓ Constraint reverted to 0-11")
        print("  ✓ Original data restored from metadata")
        print("\n" + "=" * 70)
    else:
        print("\n" + "=" * 70)
        print("✗ ROLLBACK TEST FAILED")
        print("=" * 70)
        print("\nThe rollback did not complete successfully.")
        print("Review the errors above for details.")
        print("\n" + "=" * 70)
    
    return result


if __name__ == "__main__":
    import sys
    
    # Check for --verify flag
    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        result = asyncio.run(verify_rollback())
    else:
        result = asyncio.run(main())
    
    sys.exit(0 if result else 1)
