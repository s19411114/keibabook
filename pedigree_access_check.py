import asyncio
import json
import sys
import os
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

sys.path.append(os.getcwd())

async def test_pedigree_access():
    """Test if cookies provide access to 3-generation pedigree"""
    
    # Test race ID (use existing one from settings)
    test_race_id = "202505040611"  # From settings.yml
    pedigree_url = f"https://s.keibabook.co.jp/cyuou/kettou/{test_race_id}"
    
    print(f"Testing pedigree access for race: {test_race_id}")
    print(f"URL: {pedigree_url}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        
        # Ensure login using cookies or credentials
        from src.utils.login import KeibaBookLogin
        logged_in = await KeibaBookLogin.ensure_logged_in(context, os.environ.get('LOGIN_ID'), os.environ.get('LOGIN_PASSWORD'), cookie_file='cookies.json', save_cookies=True)
        if logged_in:
            print("✅ Logged in via cookies or credentials")
        else:
            print("❌ Could not ensure login; proceeding may fail")
        except Exception as e:
            print(f"❌ Failed to load cookies: {e}")
            return
        
        page = await context.new_page()
        
        try:
            print("Navigating to pedigree page...")
            await page.goto(pedigree_url, wait_until="domcontentloaded", timeout=30000)
            
            # Check if redirected to login
            if "login" in page.url:
                print("❌ REDIRECTED TO LOGIN - Cookies expired or invalid")
                await browser.close()
                return
            
            print(f"✅ Accessed page: {page.url}")
            
            # Get HTML content
            html_content = await page.content()
            
            # Save for inspection
            with open("debug_files/debug_pedigree_test.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            print("✅ HTML saved to debug_files/debug_pedigree_test.html")
            
            # Parse pedigree data
            soup = BeautifulSoup(html_content, 'html.parser')
            pedigree_tables = soup.select("table.kettou.sandai")
            
            print(f"\n📊 Found {len(pedigree_tables)} pedigree tables")
            
            if pedigree_tables:
                # Analyze first table
                table = pedigree_tables[0]
                links = table.select("a.umalink_click")
                
                print(f"📊 Found {len(links)} horse links in first table")
                print("\n🐴 Horse names in order:")
                for i, link in enumerate(links):
                    print(f"  {i}: {link.get_text(strip=True)}")
                
                # Check if we have 6+ links (3-generation pedigree)
                if len(links) >= 6:
                    print("\n✅ SUCCESS: Full 3-generation pedigree is accessible!")
                    print("   - Father lineage: links[0-2]")
                    print("   - Mother lineage: links[3-5]")
                else:
                    print(f"\n⚠️ WARNING: Only {len(links)} links found")
                    print("   Expected 6+ for full 3-generation pedigree")
                    print("   This might indicate login is not working properly")
            else:
                print("❌ No pedigree tables found!")
                print("   Check if the page structure has changed")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            await page.screenshot(path="pedigree_error.png")
            print("Screenshot saved to pedigree_error.png")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_pedigree_access())
