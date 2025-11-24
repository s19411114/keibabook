import asyncio
import os
import sys
import yaml
from playwright.async_api import async_playwright

# Add project root to path
sys.path.append(os.getcwd())

async def debug_login():
    # Load settings
    with open('config/settings.yml', 'r', encoding='utf-8') as f:
        settings = yaml.safe_load(f)

    login_id = settings['login_id']
    password = settings['login_password']
    
    print(f"Testing login for user: {login_id}")

    async with async_playwright() as p:
        # Launch browser (headless=True for background execution)
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            print("Navigating to login page...")
            await page.goto("https://s.keibabook.co.jp/login/login")
            
            print("Filling credentials...")
            # Selectors from login_page.html
            await page.fill("input[name='login_id']", login_id)
            await page.fill("input[name='pswd']", password)
            
            print("Checking 'Keep me logged in'...")
            try:
                # Use name attribute for reliability
                await page.check("input[name='autologin']")
                print("Checked 'Keep me logged in'")
            except Exception as e:
                print(f"Failed to check 'Keep me logged in': {e}")
                
            print("Clicking Login...")
            # Correct submit button selector
            await page.click("input[name='submitbutton']")
            
            print("Waiting for navigation...")
            await page.wait_for_load_state("networkidle")
            
            # Check if login succeeded
            if "login" not in page.url:
                print("Login SUCCESS! Redirected to:", page.url)
                
                # Save cookies
                cookies = await page.context.cookies()
                import json
                with open('cookies.json', 'w') as f:
                    json.dump(cookies, f, indent=2)
                print("Cookies saved to cookies.json")
            else:
                print("Login FAILED. Still on login page.")
                
        except Exception as e:
            print(f"An error occurred: {e}")
            # Take screenshot
            await page.screenshot(path="login_error.png")
            print("Screenshot saved to login_error.png")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_login())
