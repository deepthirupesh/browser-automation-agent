import json
import os
from playwright.async_api import expect

async def run(page, url: str, screenshot_dir: str) -> dict:
    flow_name = "logout_after_login"
    screenshots = []
    
    try:
        # Load credentials from file
        credentials_path = "/Users/deepthirachumallu/hackathon-git-repo/browser-automation-agent/test_data/credentials.json"
        try:
            with open(credentials_path, 'r') as f:
                creds_data = json.load(f)
                username = creds_data.get('login', {}).get('username', 'Admin')
                password = creds_data.get('login', {}).get('password', 'admin123')
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            # Fallback to default credentials
            username = 'Admin'
            password = 'admin123'
        
        # Navigate to login page
        await page.goto(url)
        await page.wait_for_load_state('networkidle')
        
        # Fill login form
        username_field = page.get_by_placeholder('Username')
        await expect(username_field).to_be_visible(timeout=10000)
        await username_field.fill(username)
        
        password_field = page.get_by_placeholder('Password')
        await expect(password_field).to_be_visible(timeout=10000)
        await password_field.fill(password)
        
        # Click login button
        login_button = page.get_by_role('button', name='Login')
        await expect(login_button).to_be_visible(timeout=10000)
        await login_button.click()
        
        # Wait for successful login - check for dashboard or user menu
        await page.wait_for_load_state('networkidle')
        
        # Look for user dropdown menu or profile icon
        user_dropdown = page.locator('.oxd-userdropdown-tab, .oxd-userdropdown, [class*="user-dropdown"], [class*="profile"]').first
        await expect(user_dropdown).to_be_visible(timeout=15000)
        
        # Take screenshot after successful login
        login_screenshot = os.path.join(screenshot_dir, f"{flow_name}_logged_in.png")
        await page.screenshot(path=login_screenshot, full_page=True)
        screenshots.append(login_screenshot)
        
        # Click on user dropdown to open menu
        await user_dropdown.click()
        await page.wait_for_timeout(1000)
        
        # Look for logout option in dropdown
        logout_option = page.get_by_text('Logout')
        await expect(logout_option).to_be_visible(timeout=10000)
        
        # Click logout
        await logout_option.click()
        
        # Wait for redirect back to login page
        await page.wait_for_load_state('networkidle')
        
        # Verify we're back at login page
        login_form = page.get_by_placeholder('Username')
        await expect(login_form).to_be_visible(timeout=10000)
        
        # Take final screenshot after logout
        logout_screenshot = os.path.join(screenshot_dir, f"{flow_name}_logged_out.png")
        await page.screenshot(path=logout_screenshot, full_page=True)
        screenshots.append(logout_screenshot)
        
        return {
            "status": "success",
            "screenshots": screenshots,
            "flow": flow_name
        }
        
    except Exception as e:
        # Take error screenshot if possible
        try:
            error_screenshot = os.path.join(screenshot_dir, f"{flow_name}_error.png")
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