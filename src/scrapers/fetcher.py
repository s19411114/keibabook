import time
import asyncio
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def fetch_page_content(page, url, settings, rate_limiter=None, last_fetches=None, retry_count=3, retry_delay=2, wait_until=None):
    """
    Fetch page content with retries and optional rate limiter.
    Appends debug info into last_fetches list if provided.
    """
    for attempt in range(retry_count):
        try:
            t_start = time.perf_counter()
            wu = wait_until if wait_until else settings.get('playwright_wait_until', 'domcontentloaded')
            if rate_limiter:
                # caller should await rate_limiter.wait() if they want, but keep as defense-in-depth
                try:
                    await rate_limiter.wait()
                except Exception:
                    pass
            response = await page.goto(url, wait_until=wu, timeout=settings.get("playwright_timeout", 30000))
            t_goto = time.perf_counter()
            status = None
            try:
                if response:
                    status = response.status
            except Exception:
                status = None
            if status:
                logger.debug(f"HTTP status for {url}: {status}")
            if status == 429:
                wait_seconds = min(10 * (attempt + 1), 30)
                logger.warning(f"429 Too Many Requests detected for {url}: waiting {wait_seconds}s before retrying")
                await asyncio.sleep(wait_seconds)
                continue
            content = await page.content()
            t_content = time.perf_counter()
            logger.info(f"ページ取得成功: {url}")
            # Save debug fetch detail if requested
            try:
                actual_url = response.url if response else getattr(page, 'url', None)
            except Exception:
                actual_url = None
            if isinstance(last_fetches, list):
                last_fetches.append({
                    'requested_url': url,
                    'actual_url': actual_url,
                    'status': status,
                    'goto_ms': (t_goto - t_start) * 1000,
                    'content_ms': (t_content - t_goto) * 1000,
                    'total_ms': (t_content - t_start) * 1000
                })
            if settings.get('perf'):
                logger.info(f"PERF page_fetch: {url} goto_ms={(t_goto - t_start)*1000:.0f} content_ms={(t_content - t_goto)*1000:.0f} total_ms={(t_content - t_start)*1000:.0f}")
            return content
        except Exception as e:
            if attempt < retry_count - 1:
                logger.warning(f"ページ取得失敗（リトライ {attempt + 1}/{retry_count}）: {url} - {e}")
                await asyncio.sleep(retry_delay * (attempt + 1))
            else:
                logger.error(f"ページ取得最終失敗: {url} - {e}")
                raise
