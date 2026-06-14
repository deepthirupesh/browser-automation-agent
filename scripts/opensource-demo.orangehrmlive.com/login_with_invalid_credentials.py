async def run(page, url: str, screenshot_dir: str) -> dict:
    import os
    from playwright.async_api import expect
    
    flow_name = "login_with_invalid_credentials"
    screenshots = []
    
    try:
        # Navigate to login page
        await page.goto(url)
        await page.wait_for_load_state('networkidle')
        
        # Take initial screenshot
        initial_screenshot = os.path.join(screenshot_dir, f"{flow_name}_initial.png")
        await page.screenshot(path=initial_screenshot, full_page=True)
        screenshots.append(initial_screenshot)
        
        # Use invalid credentials for both fields as this is an invalid_both scenario
        invalid_username = "nonexistent_user_qa"
        invalid_password = "WrongPassword!123"
        
        # Fill username field
        username_input = page.get_by_placeholder("Username").or_(page.locator("input[name='username']")).or_(page.locator("input[type='text']")).first
        await username_input.fill(invalid_username)
        
        # Fill password field
        password_input = page.get_by_placeholder("Password").or_(page.locator("input[name='password']")).or_(page.locator("input[type='password']")).first
        await password_input.fill(invalid_password)
        
        # Take screenshot before login attempt
        before_login_screenshot = os.path.join(screenshot_dir, f"{flow_name}_before_login.png")
        await page.screenshot(path=before_login_screenshot, full_page=True)
        screenshots.append(before_login_screenshot)
        
        # Click login button
        login_button = page.get_by_role("button", name="Login").or_(page.locator("button[type='submit']")).or_(page.locator(".oxd-button")).first
        await login_button.click()
        
        # Wait for response
        await page.wait_for_timeout(3000)
        
        # Take screenshot after login attempt
        after_login_screenshot = os.path.join(screenshot_dir, f"{flow_name}_after_login.png")
        await page.screenshot(path=after_login_screenshot, full_page=True)
        screenshots.append(after_login_screenshot)
        
        # Assert that login failed - check for error message or that we're still on login page
        current_url = page.url
        
        # Check for error message (multiple possible selectors)
        error_indicators = [
            page.locator(".oxd-alert-content-text"),
            page.locator(".oxd-text--toast-message"),
            page.locator("[role='alert']"),
            page.locator(".error-message"),
            page.get_by_text("Invalid credentials"),
            page.get_by_text("Login failed"),
            page.get_by_text("Authentication failed")
        ]
        
        error_found = False
        for error_locator in error_indicators:
            try:
                if await error_locator.count() > 0:
                    await expect(error_locator).to_be_visible(timeout=5000)
                    error_found = True
                    break
            except:
                continue
        
        # Also verify we're still on login page (URL contains 'login' or 'auth')
        still_on_login = 'login' in current_url.lower() or 'auth' in current_url.lower()
        
        # Assert login failure
        if not error_found and not still_on_login:
            return {
                "status": "fail",
                "error": f"Expected login to fail with invalid credentials, but no error message found and URL changed to: {current_url}",
                "flow": flow_name,
                "screenshots": screenshots
            }
        
        # Take final success screenshot
        final_screenshot = os.path.join(screenshot_dir, f"{flow_name}_success.png")
        await page.screenshot(path=final_screenshot, full_page=True)
        screenshots.append(final_screenshot)
        
        return {
            "status": "success",
            "screenshots": screenshots,
            "flow": flow_name
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