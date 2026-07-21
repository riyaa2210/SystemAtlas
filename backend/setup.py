"""
Quick setup verification script.
Run after filling in .env to confirm everything is wired correctly.

Usage:
    python setup.py
"""
import asyncio
import sys
import os


def check_env():
    print("Checking .env file...")
    if not os.path.exists(".env"):
        print("  ERROR: .env file not found. Copy .env.example to .env and fill in values.")
        sys.exit(1)

    from app.config import get_settings
    s = get_settings()

    warnings = []
    if "localhost" in s.database_url and "supabase" not in s.database_url:
        warnings.append("DATABASE_URL looks like it's pointing to localhost. Is PostgreSQL running?")
    if not s.gemini_api_key:
        warnings.append("GEMINI_API_KEY is empty — AI Copilot will not work.")
    if not s.github_token:
        warnings.append("GITHUB_TOKEN is empty — GitHub API rate limit will be 60 req/hr.")
    if "replace-with" in s.secret_key or "dev-secret" in s.secret_key:
        warnings.append("SECRET_KEY looks like a placeholder — change it for production.")

    for w in warnings:
        print(f"  WARN: {w}")

    print(f"  App: {s.app_name} v{s.app_version} [{s.app_env}]")
    print("  Config OK")


async def check_database():
    print("\nChecking PostgreSQL connection...")
    try:
        from app.db.postgres import engine
        from sqlalchemy import text
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("  PostgreSQL connected OK")

        from app.db.postgres import create_db_tables
        await create_db_tables()
        print("  Tables created/verified OK")
    except Exception as e:
        print(f"  ERROR: {e}")
        print("  Fix: Check DATABASE_URL in .env and ensure your Supabase project is active.")
        return False
    return True


async def check_neo4j():
    print("\nChecking Neo4j connection...")
    try:
        from app.db.neo4j import get_neo4j_driver
        driver = await get_neo4j_driver()
        async with driver.session() as session:
            result = await session.run("RETURN 1 AS n")
            await result.single()
        print("  Neo4j connected OK")
    except Exception as e:
        print(f"  ERROR: {e}")
        print("  Fix: Check NEO4J_URI / NEO4J_PASSWORD in .env and ensure Aura instance is running.")
        return False
    return True


async def main():
    print("\n" + "=" * 50)
    print(" Living Architecture Map — Setup Check")
    print("=" * 50 + "\n")

    check_env()
    db_ok = await check_database()
    neo4j_ok = await check_neo4j()

    print("\n" + "=" * 50)
    if db_ok and neo4j_ok:
        print(" All checks passed. Run the server with:")
        print("   .venv\\Scripts\\uvicorn app.main:app --reload")
        print(" Swagger docs at: http://localhost:8000/docs")
    else:
        print(" Some checks failed. Fix the errors above, then re-run.")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
