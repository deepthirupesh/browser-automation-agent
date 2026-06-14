import json
import os
from playwright.async_api import expect

async def run(page, url: str, screenshot_dir: str) -> dict:
    flow_name = "invalid_credentials_login"
    screenshots = []
    
    try:
        # Load test credentials
        credentials_path = "/Users/deepthirachumallu/hackathon-git-repo/browser-automation-agent/test_data/credentials.json"
        with open(credentials_path, 'r') as f:
            credentials = json.load(f)
        
        login_creds = credentials.get('login', {})
        
        # Navigate to the login page
        await page.goto(url)
        await page.wait_for_load_state('networkidle')
        
        # Take initial screenshot
        initial_screenshot = os.path.join(screenshot_dir, f"{flow_name}_initial.png")
        await page.screenshot(path=initial_screenshot, full_page=True)
        screenshots.append(initial_screenshot)
        
        # Find username field and enter invalid username
        username_field = page.get_by_placeholder("Username").or_(page.locator('input[name="username"]')).or_(page.locator('input[type="text"]')).first
        await expect(username_field).to_be_visible(timeout=10000)
        await username_field.fill("invalid_user")
        
        # Find password field and enter invalid password
        password_field = page.get_by_placeholder("Password").or_(page.locator('input[name="password"]')).or_(page.locator('input[type="password"]')).first
        await expect(password_field).to_be_visible(timeout=10000)
        await password_field.fill("invalid_password")
        
        # Take screenshot before submitting
        before_submit_screenshot = os.path.join(screenshot_dir, f"{flow_name}_before_submit.png")
        await page.screenshot(path=before_submit_screenshot, full_page=True)
        screenshots.append(before_submit_screenshot)
        
        # Find and click login button
        login_button = page.get_by_role("button", name="Login").or_(page.locator('button[type="submit"]')).or_(page.locator('.oxd-button')).first
        await expect(login_button).to_be_visible(timeout=10000)
        await login_button.click()
        
        # Wait for error message or response
        await page.wait_for_timeout(3000)
        
        # Check for error message indicating invalid credentials
        error_message = page.locator('.oxd-alert-content').or_(page.locator('.error')).or_(page.locator('[class*="error"]')).or_(page.locator('text="Invalid credentials"')).first
        
        # Take final screenshot
        final_screenshot = os.path.join(screenshot_dir, f"{flow_name}_final.png")
        await page.screenshot(path=final_screenshot, full_page=True)
        screenshots.append(final_screenshot)
        
        # Verify that login failed (either error message is visible or we're still on login page)
        current_url = page.url
        is_still_on_login = "login" in current_url or "auth" in current_url
        
        error_visible = False
        try:
            await expect(error_message).to_be_visible(timeout=5000)
            error_visible = True
        except:
            pass
        
        if error_visible or is_still_on_login:
            return {
                "status": "success",
                "screenshots": screenshots,
                "flow": flow_name,
                "message": "Invalid credentials login test passed - login was rejected as expected"
            }
        else:
            return {
                "status": "fail",
                "error": "Invalid credentials login test failed - login was unexpectedly accepted",
                "flow": flow_name,
                "screenshots": screenshots
            }
            
    except Exception as e:
        # Capture error screenshot if possible
        try:
            error_screenshot = os.path.join(screenshot_dir, f"{flow_name}_error.png")
            await page.screenshot(path=error_screenshot, full_page=True)
            screenshots.append(error_screenshot)
        except:
            pass
            
        return {
            "status": "fail",
            "error": f"Exception during invalid credentials login test: {str(e)}",
            "flow": flow_name,
            "screenshots": screenshots
        }