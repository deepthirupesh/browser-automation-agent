async def run(page, url: str, screenshot_dir: str) -> dict:
    import os
    flow_name = "valid_login_with_credentials"
    screenshots = []
    
    try:
        # Navigate to login page
        await page.goto(url)
        await page.wait_for_load_state('networkidle')
        
        # Take initial screenshot
        initial_screenshot = os.path.join(screenshot_dir, f"{flow_name}_initial.png")
        await page.screenshot(path=initial_screenshot, full_page=True)
        screenshots.append(initial_screenshot)
        
        # Check for CSRF token or hidden fields
        csrf_token = None
        try:
            csrf_element = page.locator("input[name*='csrf'], input[name*='token'], input[type='hidden']").first
            if await csrf_element.count() > 0:
                csrf_token = await csrf_element.get_attribute('value')
        except:
            pass
        
        # Use valid credentials for happy-path flow - try multiple credential combinations
        credential_combinations = [
            ("Admin", "admin123"),
            ("admin", "admin123"),
            ("admin", "admin"),
            ("administrator", "admin123"),
            ("test", "test123")
        ]
        
        login_success = False
        
        for username, password in credential_combinations:
            try:
                # Find and fill username field
                username_selectors = [
                    "input[name='username']",
                    "input[placeholder*='Username']",
                    "input[placeholder*='username']",
                    "input[id*='username']",
                    "input[type='text']",
                    "#username",
                    ".username"
                ]
                
                username_filled = False
                for selector in username_selectors:
                    try:
                        username_field = page.locator(selector).first
                        if await username_field.count() > 0:
                            await username_field.wait_for(state="visible", timeout=3000)
                            await username_field.clear()
                            await username_field.fill(username)
                            filled_value = await username_field.input_value()
                            if filled_value == username:
                                username_filled = True
                                break
                    except:
                        continue
                
                if not username_filled:
                    continue
                
                # Find and fill password field
                password_selectors = [
                    "input[name='password']",
                    "input[placeholder*='Password']",
                    "input[placeholder*='password']",
                    "input[type='password']",
                    "input[id*='password']",
                    "#password",
                    ".password"
                ]
                
                password_filled = False
                for selector in password_selectors:
                    try:
                        password_field = page.locator(selector).first
                        if await password_field.count() > 0:
                            await password_field.wait_for(state="visible", timeout=3000)
                            await password_field.clear()
                            await password_field.fill(password)
                            password_filled = True
                            break
                    except:
                        continue
                
                if not password_filled:
                    continue
                
                # Take screenshot before login attempt
                before_login_screenshot = os.path.join(screenshot_dir, f"{flow_name}_before_login_{username}.png")
                await page.screenshot(path=before_login_screenshot, full_page=True)
                screenshots.append(before_login_screenshot)
                
                # Submit the form (try form submission first, then button click)
                form_submitted = False
                try:
                    # Try form submission
                    form = page.locator("form").first
                    if await form.count() > 0:
                        await form.evaluate("form => form.submit()")
                        form_submitted = True
                except:
                    pass
                
                if not form_submitted:
                    # Try clicking login button
                    login_selectors = [
                        "button[type='submit']",
                        "input[type='submit']",
                        "button:has-text('Login')",
                        "button:has-text('Sign In')",
                        "button:has-text('Log In')",
                        "[class*='login'] button",
                        ".login-button",
                        "#login-button"
                    ]
                    
                    for selector in login_selectors:
                        try:
                            login_button = page.locator(selector).first
                            if await login_button.count() > 0:
                                await login_button.wait_for(state="visible", timeout=3000)
                                await login_button.click()
                                form_submitted = True
                                break
                        except:
                            continue
                
                if not form_submitted:
                    continue
                
                # Wait for response with multiple strategies
                try:
                    # Wait for either navigation away from login or error message
                    await page.wait_for_function(
                        "() => !window.location.href.includes('/login') || document.querySelector('.oxd-alert, .error-message, [class*=error], [class*=alert], .invalid-feedback') !== null",
                        timeout=10000
                    )
                except:
                    pass
                
                # Additional wait for network activity
                await page.wait_for_load_state('networkidle', timeout=8000)
                
                # Check for authentication success
                current_url = page.url
                
                # Check for error messages
                error_found = False
                error_selectors = [
                    ".oxd-alert",
                    ".error-message", 
                    "[class*='error']",
                    "[class*='alert']",
                    "[role='alert']",
                    ".invalid-feedback",
                    ".validation-error",
                    ".alert-danger"
                ]
                
                for error_selector in error_selectors:
                    try:
                        error_elements = page.locator(error_selector)
                        if await error_elements.count() > 0:
                            error_text = await error_elements.first.text_content(timeout=3000)
                            if error_text and error_text.strip() and "invalid" in error_text.lower():
                                error_found = True
                                break
                    except:
                        continue
                
                if error_found:
                    continue  # Try next credential combination
                
                # Check if we're still on login page
                if "/login" in current_url.lower() or "auth/login" in current_url:
                    continue  # Try next credential combination
                
                # Check for success indicators
                success_selectors = [
                    "text=Dashboard",
                    ".oxd-topbar-header-breadcrumb", 
                    ".oxd-main-menu",
                    "[class*='dashboard']",
                    "[class*='topbar']",
                    "nav",
                    "[class*='logout']",
                    "[class*='profile']",
                    ".user-menu",
                    "[class*='header']",
                    "[class*='sidebar']",
                    "[class*='main-content']"
                ]
                
                success_found = False
                for selector in success_selectors:
                    try:
                        element = page.locator(selector).first
                        if await element.count() > 0:
                            await element.wait_for(state="visible", timeout=5000)
                            success_found = True
                            break
                    except:
                        continue
                
                # If URL changed significantly from login page, consider success
                if not success_found and current_url != url and not "/login" in current_url.lower():
                    success_found = True
                
                if success_found:
                    login_success = True
                    # Take success screenshot
                    success_screenshot = os.path.join(screenshot_dir, f"{flow_name}_success_{username}.png")
                    await page.screenshot(path=success_screenshot, full_page=True)
                    screenshots.append(success_screenshot)
                    break
                    
            except Exception as e:
                # Continue to next credential combination
                continue
        
        if login_success:
            return {"status": "success", "screenshots": screenshots, "flow": flow_name}
        else:
            return {"status": "fail", "error": "All credential combinations failed - authentication unsuccessful", "flow": flow_name, "screenshots": screenshots}
        
    except Exception as e:
        # Take error screenshot
        try:
            error_screenshot = os.path.join(screenshot_dir, f"{flow_name}_error.png")
            await page.screenshot(path=error_screenshot, full_page=True)
            screenshots.append(error_screenshot)
        except:
            pass
        
        return {"status": "fail", "error": str(e), "flow": flow_name, "screenshots": screenshots}