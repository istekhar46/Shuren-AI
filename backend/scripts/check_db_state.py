"""Check current database state before rollback test."""

import asyncio
import sys
from sqlalchemy import text
from app.db.session import AsyncSessionLocal


async def check_database_state():
    """Check the current state of the database."""
    print("=" * 60)
    print("Checking Database State Before Rollback")
    print("=" * 60)
    
    async with AsyncSessionLocal() as session:
        try:
            # Check if onboarding_states table exists
            result = await session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'onboarding_states'
                )
            """))
            table_exists = result.scalar()
            
            if not table_exists:
                print("\n✗ onboarding_states table does NOT exist")
                print("  Cannot test rollback without the table")
                return False
            
            print("\n✓ onboarding_states table exists")
            
            # Check columns
            result = await session.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'onboarding_states'
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            
            print(f"\nColumns in onboarding_states ({len(columns)} total):")
            has_agent_history = False
            for col in columns:
                print(f"  - {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
                if col[0] == 'agent_history':
                    has_agent_history = True
            
            # Check constraints
            result = await session.execute(text("""
                SELECT conname, pg_get_constraintdef(oid)
                FROM pg_constraint
                WHERE conrelid = 'onboarding_states'::regclass
                AND contype = 'c'
            """))
            constraints = result.fetchall()
            
            print(f"\nCheck constraints ({len(constraints)} total):")
            has_valid_step_constraint = False
            constraint_def = None
            for constraint in constraints:
                print(f"  - {constraint[0]}: {constraint[1]}")
                if constraint[0] == 'valid_current_step':
                    has_valid_step_constraint = True
                    constraint_def = constraint[1]
            
            # Check sample data
            result = await session.execute(text("""
                SELECT id, current_step, 
                       CASE WHEN step_data ? '_migration_metadata' THEN 'YES' ELSE 'NO' END as has_metadata,
                       CASE WHEN agent_history IS NOT NULL THEN jsonb_array_length(agent_history) ELSE NULL END as history_count
                FROM onboarding_states
                WHERE deleted_at IS NULL
                LIMIT 5
            """))
            sample_data = result.fetchall()
            
            print(f"\nSample onboarding states ({len(sample_data)} records):")
            for row in sample_data:
                print(f"  - ID: {row[0]}, Step: {row[1]}, Has Metadata: {row[2]}, History Count: {row[3]}")
            
            # Summary
            print("\n" + "=" * 60)
            print("Summary:")
            print(f"  - agent_history column: {'✓ Present' if has_agent_history else '✗ Missing'}")
            print(f"  - valid_current_step constraint: {'✓ Present' if has_valid_step_constraint else '✗ Missing'}")
            if has_valid_step_constraint and constraint_def:
                if 'current_step <= 9' in constraint_def or '<= 9' in constraint_def:
                    print(f"    Constraint allows 0-9: ✓")
                elif 'current_step <= 11' in constraint_def or '<= 11' in constraint_def:
                    print(f"    Constraint allows 0-11: ✓ (OLD)")
                else:
                    print(f"    Constraint: {constraint_def}")
            print(f"  - Sample records: {len(sample_data)}")
            print("=" * 60)
            
            return has_agent_history and has_valid_step_constraint
            
        except Exception as e:
            print(f"\n✗ Error checking database state: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    result = asyncio.run(check_database_state())
    sys.exit(0 if result else 1)
