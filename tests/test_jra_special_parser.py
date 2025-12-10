import pytest
from src.scrapers.jra_special_parser import JRASpecialParser
from src.scrapers.keibabook import KeibaBookScraper


def test_parse_special_feature_labels_extraction():
    parser = JRASpecialParser()
    html = """
    <html>
      <body>
        <h1 class="feature_title">注目特集</h1>
        <h2>血統</h2>
        <p>過去データ: これは過去の一覧</p>
        <h2>注目点</h2>
        <p>今回の注目点は強い馬の成長</p>
        <h3>コース分析</h3>
        <p>内枠有利</p>
      </body>
    </html>
    """
    result = parser.parse_special_feature(html)
    # labels should exist and contain 注目点 and コース分析 but not 血統
    assert 'labels' in result
    labels = result['labels']
    assert any('注目点' in k for k in labels.keys())
    # course labels are intentionally excluded from special pages
    assert not any('コース分析' in k or 'コース' in k for k in labels.keys())
    assert not any('血統' in k for k in labels.keys())
    # pedigree_trends should be empty since the '血統' section is present but skipped
    assert result.get('pedigree_trends', []) == []


@pytest.mark.asyncio
async def test_fetch_special_pages_grade_filter():
    settings = {
        'special_fetch_grades': 'GI',
        'skip_debug_files': True
    }
    scraper = KeibaBookScraper(settings)
    # If the race grade is GIII and allowed grades is GI only, it should skip heavy fetch
    special = await scraper._fetch_special_pages(None, 'https://s.keibabook.co.jp/cyuou', 'racekey', race_grade='GIII')
    # special should be empty dict or at least have no labels
    assert not special or special.get('labels') == {}


def test_parse_special_feature_jockey_stats():
    parser = JRASpecialParser()
    html = """
    <html>
      <body>
        <h1>特集</h1>
        <div class="picks">
          <p>吉田隼人 勝率 10.2% 連対率 24.3%</p>
          <p>西村 勝率 9.1% 連対率 21.5%</p>
        </div>
      </body>
    </html>
    """
    result = parser.parse_special_feature(html)
    # special page should not include jockey_stats (course data contains jockey stats)
    assert 'jockey_stats' not in result
