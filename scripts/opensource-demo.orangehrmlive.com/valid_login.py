async def run(page, url: str, screenshot_dir: str) -> dict:
    """Automate flow: valid_login"""
    import os

    result = {"status": "success", "screenshots": [], "flow": "valid_login"}
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_load_state("networkidle", timeout=30000)
        import json
        from pathlib import Path

        creds_path = Path("/Users/deepthirachumallu/hackathon-git-repo/browser-automation-agent/test_data/credentials.json")
        creds = {"username": "Admin", "password": "admin123"}
        if creds_path.exists():
            creds = json.loads(creds_path.read_text(encoding="utf-8")).get("login", creds)

        username = page.locator(
            'input[name="username"], input[type="email"], input[name="email"]'
        ).first
        password = page.locator(
            'input[name="password"], input[type="password"]'
        ).first
        submit = page.get_by_role("button", name="Login").or_(
            page.locator('button[type="submit"]')
        ).first

        if await username.count() > 0:
            await username.fill(creds["username"])
        if await password.count() > 0:
            await password.fill(creds["password"])
        if await submit.count() > 0:
            await submit.click(timeout=10000)

        await page.wait_for_url(
            lambda current_url: "auth/login" not in current_url.lower()
            or "dashboard" in current_url.lower(),
            timeout=30000,
        )
        await page.wait_for_load_state("networkidle", timeout=30000)

        login_form = page.locator(
            'input[name="username"], input[type="email"], input[name="email"]'
        ).first
        if await login_form.count() > 0 and await login_form.is_visible():
            raise RuntimeError("Login failed: login form still visible after submit")

        home_screen = page.get_by_role("heading", name="Dashboard").or_(
            page.locator(".oxd-topbar-header-breadcrumb-module")
        ).or_(page.locator(".oxd-userdropdown-tab, nav, [role='navigation']"))
        await home_screen.first.wait_for(state="visible", timeout=30000)

        result["home_page_verified"] = True
        os.makedirs(screenshot_dir, exist_ok=True)
        screenshot_path = os.path.join(screenshot_dir, "valid_login.png")
        await page.screenshot(path=screenshot_path, full_page=True)
        result["screenshots"].append(screenshot_path)
    except Exception as exc:
        result = {
            "status": "fail",
            "error": type(exc).__name__ + ": " + str(exc),
            "flow": "valid_login",
            "screenshots": result.get("screenshots", []),
        }
    return result
