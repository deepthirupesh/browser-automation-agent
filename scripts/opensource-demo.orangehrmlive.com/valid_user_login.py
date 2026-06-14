import json
import os
from playwright.async_api import expect

async def run(page, url: str, screenshot_dir: str) -> dict:
    flow_name = "valid_user_login"
    screenshots = []
    
    try:
        # Load credentials from file
        credentials_path = "/Users/deepthirachumallu/hackathon-git-repo/browser-automation-agent/test_data/credentials.json"
        username = "Admin"
        password = "admin123"
        
        if os.path.exists(credentials_path):
            try:
                with open(credentials_path, 'r') as f:
                    creds = json.load(f)
                    if 'login' in creds:
                        username = creds['login'].get('username', username)
                        password = creds['login'].get('password', password)
            except Exception:
                pass  # Use defaults if file read fails
        
        # Navigate to login page
        await page.goto(url)
        await page.wait_for_load_state('networkidle')
        
        # Wait for login form to be visible
        await page.wait_for_selector('input[name="username"], input[placeholder*="Username"], input[type="text"]', timeout=10000)
        
        # Find username field - try multiple selectors
        username_field = None
        username_selectors = [
            'input[name="username"]',
            'input[placeholder*="Username"]',
            'input[placeholder*="username"]',
            'input[type="text"]'
        ]
        
        for selector in username_selectors:
            try:
                username_field = page.locator(selector).first
                if await username_field.is_visible():
                    break
            except Exception:
                continue
        
        if not username_field:
            raise Exception("Could not find username field")
        
        # Fill username
        await username_field.clear()
        await username_field.fill(username)
        
        # Find password field
        password_field = None
        password_selectors = [
            'input[name="password"]',
            'input[type="password"]',
            'input[placeholder*="Password"]',
            'input[placeholder*="password"]'
        ]
        
        for selector in password_selectors:
            try:
                password_field = page.locator(selector).first
                if await password_field.is_visible():
                    break
            except Exception:
                continue
        
        if not password_field:
            raise Exception("Could not find password field")
        
        # Fill password
        await password_field.clear()
        await password_field.fill(password)
        
        # Find and click login button
        login_button = None
        login_selectors = [
            'button[type="submit"]',
            'button:has-text("Login")',
            'input[type="submit"]',
            '.orangehrm-login-button',
            'button.orangehrm-login-button'
        ]
        
        for selector in login_selectors:
            try:
                login_button = page.locator(selector).first
                if await login_button.is_visible():
                    break
            except Exception:
                continue
        
        if not login_button:
            raise Exception("Could not find login button")
        
        # Click login button
        await login_button.click()
        
        # Wait for navigation after login
        await page.wait_for_load_state('networkidle')
        
        # Verify successful login by checking for dashboard elements
        success_indicators = [
            '.oxd-topbar-header-breadcrumb',
            '.oxd-main-menu',
            'nav.oxd-navbar',
            'h1:has-text("Dashboard")',
            '.dashboard',
            '[data-v-*="dashboard"]'
        ]
        
        login_successful = False
        for indicator in success_indicators:
            try:
                await page.wait_for_selector(indicator, timeout=5000)
                login_successful = True
                break
            except Exception:
                continue
        
        # Also check URL change as indicator
        current_url = page.url
        if '/dashboard' in current_url.lower() or '/index' in current_url.lower():
            login_successful = True
        
        if not login_successful:
            # Check for error messages
            error_selectors = [
                '.oxd-alert',
                '.orangehrm-login-error',
                '[role="alert"]',
                '.error-message'
            ]
            
            error_message = "Login failed - no dashboard elements found"
            for selector in error_selectors:
                try:
                    error_element = page.locator(selector).first
                    if await error_element.is_visible():
                        error_text = await error_element.text_content()
                        if error_text:
                            error_message = f"Login failed: {error_text.strip()}"
                        break
                except Exception:
                    continue
            
            raise Exception(error_message)
        
        # Take success screenshot
        screenshot_path = os.path.join(screenshot_dir, f"{flow_name}_success.png")
        await page.screenshot(path=screenshot_path, full_page=True)
        screenshots.append(screenshot_path)
        
        return {
            "status": "success",
            "screenshots": screenshots,
            "flow": flow_name
        }
        
    except Exception as e:
        # Take failure screenshot
        try:
            screenshot_path = os.path.join(screenshot_dir, f"{flow_name}_failure.png")
            await page.screenshot(path=screenshot_path, full_page=True)
            screenshots.append(screenshot_path)
        except Exception:
            pass
        
        return {
            "status": "fail",
            "error": str(e),
            "flow": flow_name,
            "screenshots": screenshots
        }