"""
Test all API routes - server must be running at localhost:8000.
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import httpx

BASE = "http://localhost:8000"
PASS = 0
FAIL = 0


def test(name: str, passed: bool, detail: str = ""):
    global PASS, FAIL
    if passed:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name} -- {detail}")


def main():
    global PASS, FAIL
    client = httpx.Client(base_url=BASE, timeout=10)

    # ── 1. Health Check ──────────────────────────────────
    print("\n=== 1. Health Check ===")
    
    r = client.get("/")
    test("GET / → 200", r.status_code == 200, f"got {r.status_code}")
    data = r.json()
    test("Root health status=ok", data.get("status") == "ok", f"got {data}")

    r = client.get("/api/health")
    test("GET /api/health → 200", r.status_code == 200, f"got {r.status_code}")

    # ── 2. Auth — Register ───────────────────────────────
    print("\n=== 2. Auth - Register ===")

    # Register a new test user
    test_email = "testuser_api@covankn.ai"
    r = client.post("/api/auth/register", json={
        "email": test_email,
        "password": "TestUser@2026!",
        "full_name": "Test User API",
    })
    if r.status_code == 201:
        test("POST /api/auth/register → 201", True)
        reg_data = r.json()
        test("Register returns access_token", "access_token" in reg_data, f"keys: {reg_data.keys()}")
        test("Register returns user info", reg_data.get("user", {}).get("email") == test_email)
        user_token = reg_data["access_token"]
        user_id = reg_data["user"]["id"]
    elif r.status_code == 409:
        # User already exists — login instead
        test("POST /api/auth/register → 409 (already exists)", True)
        r2 = client.post("/api/auth/login", json={
            "email": test_email,
            "password": "TestUser@2026!",
        })
        test("Fallback login → 200", r2.status_code == 200, f"got {r2.status_code}")
        reg_data = r2.json()
        user_token = reg_data["access_token"]
        user_id = reg_data["user"]["id"]
    else:
        test("POST /api/auth/register", False, f"got {r.status_code}: {r.text}")
        user_token = None
        user_id = None

    # Register with duplicate email
    r = client.post("/api/auth/register", json={
        "email": test_email,
        "password": "AnotherPass@2026!",
        "full_name": "Duplicate",
    })
    test("Duplicate email → 409", r.status_code == 409, f"got {r.status_code}")

    # Register with short password
    r = client.post("/api/auth/register", json={
        "email": "short@test.com",
        "password": "123",
    })
    test("Short password → 422 (validation)", r.status_code == 422, f"got {r.status_code}")

    # ── 3. Auth — Login ──────────────────────────────────
    print("\n=== 3. Auth - Login ===")

    # Login admin
    r = client.post("/api/auth/login", json={
        "email": "admin@covankn.ai",
        "password": "Admin@2026!",
    })
    test("Admin login → 200", r.status_code == 200, f"got {r.status_code}: {r.text}")
    if r.status_code == 200:
        admin_data = r.json()
        admin_token = admin_data["access_token"]
        test("Admin has role=admin", admin_data["user"]["role"] == "admin")
        test("Login returns token_type=bearer", admin_data.get("token_type") == "bearer")
    else:
        admin_token = None

    # Login with wrong password
    r = client.post("/api/auth/login", json={
        "email": "admin@covankn.ai",
        "password": "WrongPassword!",
    })
    test("Wrong password → 401", r.status_code == 401, f"got {r.status_code}")

    # Login with non-existent email
    r = client.post("/api/auth/login", json={
        "email": "nobody@covankn.ai",
        "password": "Whatever@2026!",
    })
    test("Non-existent email → 401", r.status_code == 401, f"got {r.status_code}")

    # ── 4. Auth — Profile (JWT) ──────────────────────────
    print("\n=== 4. Auth - Profile (JWT) ===")

    if user_token:
        r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {user_token}"})
        test("GET /api/auth/me → 200 (user)", r.status_code == 200, f"got {r.status_code}")
        if r.status_code == 200:
            me = r.json()
            test("Profile returns correct email", me.get("email") == test_email)
            test("Profile has role field", "role" in me)

    if admin_token:
        r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
        test("GET /api/auth/me → 200 (admin)", r.status_code == 200, f"got {r.status_code}")

    # No token
    r = client.get("/api/auth/me")
    test("No token → 401/403", r.status_code in (401, 403), f"got {r.status_code}")

    # Invalid token
    r = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
    test("Invalid token → 401", r.status_code == 401, f"got {r.status_code}")

    # ── 5. Admin — List Users ────────────────────────────
    print("\n=== 5. Admin Routes ===")

    if admin_token:
        r = client.get("/api/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
        test("GET /api/admin/users → 200", r.status_code == 200, f"got {r.status_code}")
        if r.status_code == 200:
            users = r.json()
            test("Users is a list", isinstance(users, list))
            test("At least 1 user (admin)", len(users) >= 1, f"got {len(users)} users")

    # Non-admin trying admin route
    if user_token:
        r = client.get("/api/admin/users", headers={"Authorization": f"Bearer {user_token}"})
        test("User → admin route → 403", r.status_code == 403, f"got {r.status_code}")

    # ── 6. Admin — Stats ─────────────────────────────────
    print("\n=== 6. Admin - Stats ===")

    if admin_token:
        r = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {admin_token}"})
        test("GET /api/admin/stats → 200", r.status_code == 200, f"got {r.status_code}")
        if r.status_code == 200:
            stats = r.json()
            test("Stats has total_users", "total_users" in stats)
            test("Stats has total_sessions", "total_sessions" in stats)
            test("Stats has total_tokens_used", "total_tokens_used" in stats)
            test("total_users >= 1", stats.get("total_users", 0) >= 1)

    # ── 7. Admin — Toggle User Active ────────────────────
    print("\n=== 7. Admin - Toggle Active ===")

    if admin_token and user_id:
        # Toggle user → inactive
        r = client.patch(
            f"/api/admin/users/{user_id}/toggle-active",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        test("PATCH toggle-active → 200", r.status_code == 200, f"got {r.status_code}")
        if r.status_code == 200:
            toggled = r.json()
            was_active = toggled.get("is_active")
            test(f"User is_active toggled (now={was_active})", was_active is not None)

        # Toggle back
        r = client.patch(
            f"/api/admin/users/{user_id}/toggle-active",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        test("Toggle back → 200", r.status_code == 200, f"got {r.status_code}")
        if r.status_code == 200:
            test("User is_active restored", r.json().get("is_active") != was_active)

    # ── 8. Debate — List (empty) ─────────────────────────
    print("\n=== 8. Debate Routes (no AI - just DB) ===")

    if user_token:
        r = client.get("/api/debate", headers={"Authorization": f"Bearer {user_token}"})
        test("GET /api/debate → 200", r.status_code == 200, f"got {r.status_code}")
        if r.status_code == 200:
            sessions = r.json()
            test("Debate sessions is list", isinstance(sessions, list))

    # Debate without auth
    r = client.get("/api/debate")
    test("Debate no auth → 401/403", r.status_code in (401, 403), f"got {r.status_code}")

    # ── 9. Swagger /docs accessible ──────────────────────
    print("\n=== 9. Swagger UI ===")

    r = client.get("/docs")
    test("GET /docs → 200", r.status_code == 200, f"got {r.status_code}")
    test("/docs has HTML content", "swagger" in r.text.lower() or "openapi" in r.text.lower())

    r = client.get("/openapi.json")
    test("GET /openapi.json → 200", r.status_code == 200, f"got {r.status_code}")
    if r.status_code == 200:
        schema = r.json()
        paths = list(schema.get("paths", {}).keys())
        test(f"OpenAPI has {len(paths)} paths", len(paths) >= 8, f"paths: {paths}")

    # ── Summary ──────────────────────────────────────────
    print(f"\n" + "="*50)
    print(f"  RESULTS: {PASS} passed, {FAIL} failed, {PASS+FAIL} total")
    print("="*50)

    client.close()
    return FAIL == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
