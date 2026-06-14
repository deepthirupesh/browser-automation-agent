import json
import os
from playwright.async_api import expect

async def run(page, url: str, screenshot_dir: str) -> dict:
    flow_name = "empty_fields_login"
    screenshots = []
    
    try:
        # Navigate to the login page
        await page.goto(url)
        await page.wait_for_load_state('networkidle')
        
        # Take initial screenshot
        initial_screenshot = os.path.join(screenshot_dir, f"{flow_name}_initial.png")
        await page.screenshot(path=initial_screenshot, full_page=True)
        screenshots.append(initial_screenshot)
        
        # Wait for login form to be visible
        await expect(page.get_by_role("textbox", name="Username")).to_be_visible(timeout=10000)
        
        # Attempt to login with empty fields - just click the login button without filling any fields
        login_button = page.get_by_role("button", name="Login")
        await expect(login_button).to_be_visible()
        await login_button.click()
        
        # Wait a moment for any validation messages to appear
        await page.wait_for_timeout(2000)
        
        # Take screenshot after attempting login with empty fields
        empty_fields_screenshot = os.path.join(screenshot_dir, f"{flow_name}_empty_attempt.png")
        await page.screenshot(path=empty_fields_screenshot, full_page=True)
        screenshots.append(empty_fields_screenshot)
        
        # Check for validation messages or error indicators
        # Look for common validation message patterns
        validation_messages = await page.locator("[class*='error'], [class*='invalid'], [class*='required'], .oxd-input-field-error-message, .oxd-text--span").count()
        
        # Verify we're still on the login page (not redirected)
        current_url = page.url
        is_still_on_login = "login" in current_url.lower() or "auth" in current_url.lower()
        
        # Take final screenshot
        final_screenshot = os.path.join(screenshot_dir, f"{flow_name}_final.png")
        await page.screenshot(path=final_screenshot, full_page=True)
        screenshots.append(final_screenshot)
        
        # Determine success based on whether we're still on login page and validation messages appear
        if is_still_on_login and validation_messages > 0:
            return {
                "status": "success", 
                "screenshots": screenshots, 
                "flow": flow_name,
                "message": f"Empty fields login validation working correctly. Found {validation_messages} validation messages."
            }
        elif is_still_on_login:
            return {
                "status": "success", 
                "screenshots": screenshots, 
                "flow": flow_name,
                "message": "Empty fields login prevented (no redirect occurred)"
            }
        else:
            return {
                "status": "fail", 
                "error": "Login succeeded with empty fields - this should not happen", 
                "flow": flow_name, 
                "screenshots": screenshots
            }
            
    except Exception as e:
        error_screenshot = os.path.join(screenshot_dir, f"{flow_name}_error.png")
        try:
            await page.screenshot(path=error_screenshot, full_page=True)
            screenshots.append(error_screenshot)
        except:
            pass
            
        return {
            "status": "fail", 
            "error": str(e), 
            "flow": flow_name, 
            "screenshots": screenshots
        }