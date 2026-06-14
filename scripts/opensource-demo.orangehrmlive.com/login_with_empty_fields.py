import asyncio
from playwright.async_api import expect
import os

async def run(page, url: str, screenshot_dir: str) -> dict:
    flow_name = "login_with_empty_fields"
    screenshots = []
    
    try:
        # Navigate to login page
        await page.goto(url)
        await page.wait_for_load_state('networkidle')
        
        # Take initial screenshot
        initial_screenshot = os.path.join(screenshot_dir, f"{flow_name}_initial.png")
        await page.screenshot(path=initial_screenshot, full_page=True)
        screenshots.append(initial_screenshot)
        
        # Locate login form elements
        username_field = page.get_by_placeholder("Username")
        password_field = page.get_by_placeholder("Password")
        login_button = page.get_by_role("button", name="Login")
        
        # Wait for form elements to be visible
        await expect(username_field).to_be_visible()
        await expect(password_field).to_be_visible()
        await expect(login_button).to_be_visible()
        
        # Leave both fields empty and attempt login
        await username_field.clear()
        await password_field.clear()
        
        # Click login button with empty fields
        await login_button.click()
        
        # Wait for validation messages to appear
        await page.wait_for_timeout(2000)
        
        # Check for validation error messages
        error_messages = page.locator(".oxd-input-field-error-message")
        await expect(error_messages).to_have_count(2, timeout=5000)
        
        # Verify specific validation messages
        username_error = error_messages.nth(0)
        password_error = error_messages.nth(1)
        
        await expect(username_error).to_contain_text("Required")
        await expect(password_error).to_contain_text("Required")
        
        # Verify we're still on the login page (not redirected)
        await expect(page.locator(".orangehrm-login-form")).to_be_visible()
        
        # Verify login button is still present (indicating failed login)
        await expect(login_button).to_be_visible()
        
        # Take final screenshot showing validation errors
        final_screenshot = os.path.join(screenshot_dir, f"{flow_name}_validation_errors.png")
        await page.screenshot(path=final_screenshot, full_page=True)
        screenshots.append(final_screenshot)
        
        return {
            "status": "success",
            "screenshots": screenshots,
            "flow": flow_name,
            "message": "Successfully validated empty fields show required field errors"
        }
        
    except Exception as e:
        # Capture screenshot on failure
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