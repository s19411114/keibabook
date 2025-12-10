import pytest
from src.scrapers.keibabook import KeibaBookScraper


def test_nouryoku_parse_removed():
    settings = {'shutuba_url': 'https://example.com', 'race_type': 'jra'}
    scraper = KeibaBookScraper(settings)
    assert not hasattr(scraper, '_parse_horse_table_data')
