#!/usr/bin/env python3
"""
Verification script for database connection pooling configuration.
Ensures NullPool is properly configured for serverless compatibility.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def verify_nullpool():
    """Verify that SQLAlchemy engine uses NullPool"""
    print("🔍 Verifying database connection pooling configuration...\n")
    
    try:
        from app.db.session import engine
        from sqlalchemy.pool import NullPool
        
        # Check 1: Verify NullPool is configured
        pool_class = engine.pool.__class__.__name__
        print(f"✓ Pool Class: {pool_class}")
        
        if isinstance(engine.pool, NullPool):
            print("✅ SUCCESS: NullPool is properly configured")
            print("   → SQLAlchemy's internal pooling is disabled")
            print("   → External PgBouncer will handle connection pooling")
        else:
            print(f"❌ FAILURE: Expected NullPool, got {pool_class}")
            print("   → This will cause connection exhaustion in serverless!")
            return False
        
        # Check 2: Verify connection configuration
        print("\n🔧 Connection Configuration:")
        print(f"   Database: {engine.url.database}")
        print(f"   Host: {engine.url.host}")
        
        # Check if using a connection pooler (Neon, Supabase, etc.)
        if 'pooler' in str(engine.url.host).lower():
            print("   ✅ Using external connection pooler (detected in hostname)")
        elif '6543' in str(engine.url) or '6432' in str(engine.url):
            print("   ✅ Using external connection pooler (detected pooler port)")
        else:
            print("   ⚠️  No external pooler detected - consider setting up PgBouncer")
        
        # Check 3: Test connection
        print("\n🔌 Testing database connection...")
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ Connection successful!")
            print(f"   PostgreSQL version: {version.split(',')[0]}")
        
        print("\n" + "="*60)
        print("✅ ALL CHECKS PASSED - Serverless pooling configured correctly")
        print("="*60)
        print("\n📋 Next Steps:")
        print("   1. Set up external PgBouncer (see architecture/pgbouncer_setup.md)")
        print("   2. Update DATABASE_URL to point to PgBouncer endpoint")
        print("   3. Deploy to Modal: modal deploy modal_app.py")
        print("   4. Monitor connection counts in production")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("   Make sure you're running from the backend directory")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = verify_nullpool()
    sys.exit(0 if success else 1)
