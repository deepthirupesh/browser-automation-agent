async def run(page, url: str, screenshot_dir: str) -> dict:
    """Automate flow: content_view"""
    import os

    result = {"status": "success", "screenshots": [], "flow": "content_view"}
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_load_state("networkidle", timeout=30000)

        os.makedirs(screenshot_dir, exist_ok=True)
        screenshot_path = os.path.join(screenshot_dir, "content_view.png")
        await page.screenshot(path=screenshot_path, full_page=True)
        result["screenshots"].append(screenshot_path)
    except Exception as exc:
        result = {
            "status": "fail",
            "error": type(exc).__name__ + ": " + str(exc),
            "flow": "content_view",
            "screenshots": result.get("screenshots", []),
        }
    return result
