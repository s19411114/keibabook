import asyncio
from src.utils.config import load_settings
from src.scrapers.keibabook import KeibaBookScraper

async def main():
    settings = load_settings()
    scraper = KeibaBookScraper(settings)
    scraped_data = await scraper.scrape()
    print(scraped_data) # スクレイピング結果を表示

if __name__ == '__main__':
    asyncio.run(main())
