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
