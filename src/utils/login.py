import asyncio
import json
import os
from playwright.async_api import Page
from src.utils.logger import get_logger

logger = get_logger(__name__)

class KeibaBookLogin:
    """KeibaBook Login Handler"""
    
    LOGIN_URL = "https://s.keibabook.co.jp/login/login"
    
    @staticmethod
    async def login(page: Page, login_id: str, password: str, cookie_file: str = 'cookies.json', save_cookies: bool = True) -> bool:
        """
        Perform login and save cookies
        
        Args:
            page: Playwright Page object
            login_id: User ID
            password: Password
            cookie_file: Path to save cookies
            
        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            logger.info("Starting login process...")
            await page.goto(KeibaBookLogin.LOGIN_URL)
            
            # Fill credentials
            logger.info(f"Logging in as user: {login_id}")
            await page.fill("input[name='login_id']", login_id)
            await page.fill("input[name='pswd']", password)
            
            # Check 'Keep me logged in'
            try:
                await page.check("input[name='autologin']")
                logger.debug("Checked 'Keep me logged in'")
            except Exception as e:
                logger.warning(f"Failed to check 'Keep me logged in': {e}")
            
            # Click login
            await page.click("input[name='submitbutton']")
            
            # Wait for navigation
            await page.wait_for_load_state("networkidle")
            
            # Verify login
            if "login" not in page.url:
                logger.info(f"Login SUCCESS! Redirected to: {page.url}")
                
                # Save cookies (optional) for faster subsequent runs
                if save_cookies and cookie_file:
                    cookies = await page.context.cookies()
                    with open(cookie_file, 'w', encoding='utf-8') as f:
                        json.dump(cookies, f, indent=2, ensure_ascii=False)
                    logger.info(f"Cookies saved to {cookie_file}")
                return True
            else:
                logger.error("Login FAILED. Still on login page.")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False

    @staticmethod
    async def load_cookies_to_context(context, cookie_file: str = 'cookies.json') -> bool:
        """Load cookies from a file into a Playwright context. Returns True if cookies were loaded."""
        try:
            if cookie_file and os.path.exists(cookie_file):
                with open(cookie_file, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                if cookies:
                    await context.add_cookies(cookies)
                    logger.info(f"Loaded cookies from {cookie_file}")
                    return True
        except Exception as e:
            logger.warning(f"Failed to load cookies from {cookie_file}: {e}")
        return False

    @staticmethod
    def cookie_file_expired(cookie_file: str = 'cookies.json') -> bool:
        """Return True if cookie file exists and at least one cookie has expired."""
        try:
            if cookie_file and os.path.exists(cookie_file):
                with open(cookie_file, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                import time
                now = int(time.time())
                for c in cookies:
                    # cookie expiry may be in 'expires' field
                    exp = c.get('expires') or c.get('expiry') or c.get('expire')
                    if exp is not None:
                        try:
                            if int(exp) < now:
                                return True
                        except Exception:
                            continue
        except Exception:
            return True
        return False

    @staticmethod
    async def is_logged_in(page: Page, test_url: str = "https://s.keibabook.co.jp/") -> bool:
        """Return True if navigation to test_url does not redirect to login."""
        try:
            await page.goto(test_url, wait_until='domcontentloaded', timeout=10000)
            # If the URL contains 'login', assume not logged in
            if 'login' in page.url:
                return False
            return True
        except Exception:
            return False

    @staticmethod
    async def ensure_logged_in(context, login_id: str, password: str, cookie_file: str = 'cookies.json', save_cookies: bool = True, test_url: str = 'https://s.keibabook.co.jp/') -> bool:
        """Ensure the context is logged in. Try load cookies first; if not valid, perform login."""
        # Try to load cookies into context
        loaded = await KeibaBookLogin.load_cookies_to_context(context, cookie_file)
        page = await context.new_page()
        try:
            if loaded:
                logger.debug("Cookies loaded; verifying login state...")
                if await KeibaBookLogin.is_logged_in(page, test_url):
                    logger.info("Logged in via cookies")
                    await page.close()
                    return True

            # If we reach here, proceed to explicit login
            logger.info("Performing login via credentials...")
            success = await KeibaBookLogin.login(page, login_id, password, cookie_file=cookie_file, save_cookies=save_cookies)
            await page.close()
            return success
        except Exception as e:
            logger.error(f"Error during ensure_logged_in: {e}")
            try:
                await page.close()
            except Exception:
                pass
            return False
