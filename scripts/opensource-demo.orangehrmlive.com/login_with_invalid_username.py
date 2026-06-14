import asyncio
from playwright.async_api import expect
import os

async def run(page, url: str, screenshot_dir: str) -> dict:
    flow_name = "login_with_invalid_username"
    screenshots = []
    
    try:
        # Navigate to the login page
        await page.goto(url)
        await page.wait_for_load_state("networkidle")
        
        # Take initial screenshot
        initial_screenshot = os.path.join(screenshot_dir, f"{flow_name}_initial.png")
        await page.screenshot(path=initial_screenshot, full_page=True)
        screenshots.append(initial_screenshot)
        
        # Wait for login form to be visible
        username_field = page.get_by_placeholder("Username")
        password_field = page.get_by_placeholder("Password")
        login_button = page.get_by_role("button", name="Login")
        
        await expect(username_field).to_be_visible()
        await expect(password_field).to_be_visible()
        await expect(login_button).to_be_visible()
        
        # Use invalid username + valid password for this flow
        await username_field.fill("nonexistent_user_qa")
        await password_field.fill("admin123")
        
        # Take screenshot before login attempt
        before_login_screenshot = os.path.join(screenshot_dir, f"{flow_name}_before_login.png")
        await page.screenshot(path=before_login_screenshot, full_page=True)
        screenshots.append(before_login_screenshot)
        
        # Attempt login
        await login_button.click()
        
        # Wait a moment for the response
        await page.wait_for_timeout(2000)
        
        # Check for error message - should remain on login page with error
        error_message = page.locator(".oxd-alert-content-text")
        
        # Assert that we get an error message for invalid username
        await expect(error_message).to_be_visible(timeout=5000)
        await expect(error_message).to_contain_text("Invalid credentials")
        
        # Verify we're still on the login page (URL should not change)
        current_url = page.url
        if "login" not in current_url:
            raise AssertionError("Expected to remain on login page after invalid username")
        
        # Verify login form is still present
        await expect(username_field).to_be_visible()
        await expect(password_field).to_be_visible()
        
        # Take final screenshot showing the error
        final_screenshot = os.path.join(screenshot_dir, f"{flow_name}_error_displayed.png")
        await page.screenshot(path=final_screenshot, full_page=True)
        screenshots.append(final_screenshot)
        
        return {
            "status": "success",
            "screenshots": screenshots,
            "flow": flow_name
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
            "error": str(e),
            "flow": flow_name,
            "screenshots": screenshots
        }