"""Verify all API routes are registered correctly."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.api.v1.router import api_router
from app.main import app

print(f"\napi_router has {len(api_router.routes)} routes:")
for r in api_router.routes:
    if hasattr(r, 'path'):
        methods = list(r.methods) if r.methods else []
        print(f"  {methods} {r.path}")

print(f"\nFull app has {len(app.routes)} routes")

# Check all expected paths exist
expected = [
    "/auth/register", "/auth/login", "/auth/me",
    "/repositories", "/repositories/{repo_id}",
    "/repositories/{repo_id}/scan",
    "/graph/{repo_id}", "/analytics/{repo_id}",
    "/analytics/{repo_id}/risks", "/copilot/ask",
]
registered_paths = [r.path for r in api_router.routes if hasattr(r, 'path')]
missing = [p for p in expected if not any(p in rp for rp in registered_paths)]
if missing:
    print(f"\nMISSING ROUTES: {missing}")
    sys.exit(1)
else:
    print(f"\nAll {len(expected)} expected routes present. ✓")
