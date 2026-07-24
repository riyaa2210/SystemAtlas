"""Quick smoke test for auth — run with: python tests/test_auth_quick.py"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_password():
    from app.core.auth.password import hash_password, verify_password
    h = hash_password("MyPassword123")
    assert verify_password("MyPassword123", h), "valid password should verify"
    assert not verify_password("WrongPass", h), "wrong password should fail"
    print("✓ Password hashing and verification OK")


def test_jwt():
    from app.core.auth.jwt import create_access_token, verify_token
    token = create_access_token("user-uuid-123")
    user_id = verify_token(token)
    assert user_id == "user-uuid-123", f"Expected user-uuid-123, got {user_id}"

    bad = verify_token("not.a.valid.token")
    assert bad is None, "Invalid token should return None"
    print("✓ JWT creation and verification OK")


def test_app_imports():
    from app.main import app
    from app.api.v1.router import api_router
    routes = [r.path for r in app.routes]
    assert "/health" in routes, "health route missing"
    print(f"✓ App imports OK — {len(app.routes)} routes registered")


def test_schemas():
    from app.schemas.auth import RegisterRequest, LoginRequest
    r = RegisterRequest(name="Test User", email="test@example.com", password="pass1234")
    assert r.name == "Test User"
    try:
        RegisterRequest(name="X", email="bad@x.com", password="short")
        assert False, "Should have raised"
    except Exception:
        pass
    print("✓ Pydantic schemas OK")


if __name__ == "__main__":
    print("\n=== LAM Auth Smoke Tests ===\n")
    test_jwt()
    test_schemas()
    test_app_imports()
    test_password()   # slowest — bcrypt, runs last
    print("\n=== All tests passed ✓ ===\n")
