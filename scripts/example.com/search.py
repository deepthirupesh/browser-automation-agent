async def run(page, url: str, screenshot_dir: str) -> dict:
    """Automate flow: search"""
    import os

    result = {"status": "success", "screenshots": [], "flow": "search"}
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_load_state("networkidle", timeout=30000)
        search = page.get_by_role("searchbox").or_(
            page.locator('input[type="search"], input[name="q"], input[name="search"]')
        ).first
        if await search.count() > 0:
            await search.fill("test")
            await search.press("Enter")
        await page.wait_for_load_state("networkidle", timeout=30000)
        os.makedirs(screenshot_dir, exist_ok=True)
        screenshot_path = os.path.join(screenshot_dir, "search.png")
        await page.screenshot(path=screenshot_path, full_page=True)
        result["screenshots"].append(screenshot_path)
    except Exception as exc:
        result = {
            "status": "fail",
            "error": type(exc).__name__ + ": " + str(exc),
            "flow": "search",
            "screenshots": result.get("screenshots", []),
        }
    return result
