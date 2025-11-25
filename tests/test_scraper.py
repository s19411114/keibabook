import os
from src.utils.config import load_settings
from src.scrapers.keibabook import KeibaBookScraper

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call, ANY
from playwright.async_api import Page, Browser, BrowserContext, async_playwright
from bs4 import BeautifulSoup # 追加

mock_training_html = """
<html>
<body>
    <table class="TrainingTable">
        <tbody>
            <tr>
                <td class="HorseNum">1</td>
                <td class="TrainingDate">11/5</td>
                <td class="TrainingLocation">美浦南Ｗ</td>
                <td class="TrainingTime">68.9-53.5-38.6-11.9</td>
                <td class="TrainingEvaluation">馬ナリ余力</td>
            </tr>
        </tbody>
    </table>
</body>
</html>
"""

mock_pedigree_html = """
<html>
<body>
    <table class="PedigreeTable">
        <tbody>
            <tr>
                <td class="HorseNum">1</td>
                <td class="Father">ドレフォン</td>
                <td class="Mother">セイウンアワード</td>
                <td class="MothersFather">タニノギムレット</td>
            </tr>
        </tbody>
    </table>
</body>
</html>
"""

mock_stable_comment_html = """
<html>
<body>
    <div class="StableCommentTable">
        <div class="HorseComment">
            <p class="HorseNum">1</p>
            <p class="Comment">まだ素質だけで走っている感じ。使いつつ良くなってくれば。</p>
        </div>
    </div>
</body>
</html>
"""

mock_previous_race_comment_html = """
<html>
<body>
    <div class="PreviousRaceCommentTable">
        <div class="HorseComment">
            <p class="HorseNum">1</p>
            <p class="Comment">スタートで後手を踏んだのが全て。力負けではない。</p>
        </div>
    </div>
</body>
</html>
"""

mock_horse_past_results_html = """
<html>
<body>
    <div class="HorsePastResultsTable">
        <table>
            <thead>
                <tr>
                    <th>日付</th>
                    <th>開催</th>
                    <th>R</th>
                    <th>着順</th>
                    <th>タイム</th>
                    <th>騎手</th>
                    <th>斤量</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>2025/10/20</td>
                    <td>東京</td>
                    <td>1</td>
                    <td>1着</td>
                    <td>1:35.0</td>
                    <td>ルメール</td>
                    <td>55</td>
                </tr>
            </tbody>
        </table>
    </div>
</body>
</html>
"""

def test_load_settings():
    cfg = load_settings()
    assert 'race_id' in cfg
    assert 'shutuba_url' in cfg

def test_keibabook_scraper_initialization():
    settings = load_settings()
    scraper = KeibaBookScraper(settings)
    assert scraper is not None

@pytest.mark.asyncio
async def test_keibabook_scraper_fetch_page_content():
    settings = load_settings()
    scraper = KeibaBookScraper(settings)

    # playwrightのモックを作成
    mock_page = AsyncMock(spec=Page)
    mock_page.content.return_value = "<html><body>Mocked Page Content</body></html>"

    # fetch_page_contentがモックのpageを使用するように設定
    # ここでは、直接_fetch_page_contentをテストするために、pageオブジェクトを渡す
    content = await scraper._fetch_page_content(mock_page, "http://mockurl.com")
    
    mock_page.goto.assert_called_once_with("http://mockurl.com", wait_until="domcontentloaded", timeout=ANY)
    mock_page.content.assert_called_once()
    assert content == "<html><body>Mocked Page Content</body></html>"

def test_keibabook_scraper_parse_race_data():
    settings = load_settings()
    scraper = KeibaBookScraper(settings)
    
    # モックのHTMLコンテンツ (更新)
    mock_html = """
    <html>
    <body>
        <div class="racemei">
            <p>2025年11月9日 3回福島2日目</p>
            <p>1R ２歳未勝利</p>
        </div>
        <div class="racetitle_sub">
            <p>[指定]</p>
            <p>1150m (ダート・右) 曇・良</p>
        </div>
        <table class="syutuba_sp">
            <tbody>
                <tr>
                    <td class="umaban">1</td>
                    <td class="kbamei">
                        <a href="#">馬名1</a>
                    </td>
                    <td class="left">
                        <p class="kisyu">
                            <a href="#">騎手1</a>
                        </p>
                    </td>
                </tr>
                <tr>
                    <td class="umaban">2</td>
                    <td class="kbamei">
                        <a href="#">馬名2</a>
                    </td>
                                            <td class="left">
                                                <p class="kisyu">
                                                    <a href="#">騎手2</a>
                                                </p>
                                            </td>                </tr>
            </tbody>
        </table>
    </body>
    </html>
    """
    
    race_data = scraper._parse_race_data(mock_html)

    assert race_data['race_name'] == "2025年11月9日 3回福島2日目"
    assert race_data['race_grade'] == "1R ２歳未勝利"
    assert race_data['distance'] == "1150m"
    assert len(race_data['horses']) == 2
    assert race_data['horses'][0]['horse_num'] == "1"
    assert race_data['horses'][0]['horse_name'] == "馬名1"
    assert race_data['horses'][0]['jockey'] == "騎手1"
    assert race_data['horses'][1]['horse_num'] == "2"
    assert race_data['horses'][1]['horse_name'] == "馬名2"
    assert race_data['horses'][1]['jockey'] == "騎手2"

@pytest.mark.asyncio
async def test_keibabook_scraper_scrape_method():
    settings = load_settings()
    scraper = KeibaBookScraper(settings)

    # モックのHTMLコンテンツ
    mock_html = """
    <html>
    <body>
        <div class="RaceName">
            <h1>第1回福島競馬 第1日目 1R</h1>
            <p>サラ系3歳未勝利</p>
        </div>
        <div class="RaceData01">
            <dl>
                <dt>距離</dt><dd>ダート1700m</dd>
                <dt>発走</dt><dd>10:00</dd>
            </dl>
        </div>
        <table class="ShutubaTable">
            <tbody>
                <tr>
                    <td class="HorseNum">1</td>
                    <td class="HorseName">
                        <a href="#">馬名1</a>
                    </td>
                    <td class="Jockey">騎手1</td>
                </tr>
            </tbody>
        </table>
    </body>
    </html>
    """
    
    # _fetch_page_contentと_parse_race_dataをモック化
    # The initial page (shutuba) is fetched using page.goto() / page.content(),
    # so _fetch_page_content handles secondary pages.
    scraper._fetch_page_content = AsyncMock(side_effect=[
        mock_training_html, # 1st fetch by _fetch_page_content (training)
        mock_pedigree_html, # 2nd (pedigree)
        mock_stable_comment_html, # 3rd (stable comment)
        mock_previous_race_comment_html, # 4th (previous race comment)
        mock_horse_past_results_html # optional horse detail page
    ])
    scraper._parse_race_data = MagicMock(return_value={
        'race_name': "第1回福島競馬 第1日目 1R",
        'race_grade': "サラ系3歳未勝利",
        'distance': "ダート1700m",
        'horses': [{'horse_num': "1", 'horse_name': "馬名1", 'jockey': "騎手1", 'horse_name_link': '/db/uma/dummy_link'}]
    })
    scraper._parse_training_data = MagicMock(return_value={
        '1': {'date': '11/5', 'location': '美浦南Ｗ', 'time': '68.9-53.5-38.6-11.9', 'evaluation': '馬ナリ余力'}
    })
    scraper._parse_pedigree_data = MagicMock(return_value=[
        {'father': 'ドレフォン', 'mother': 'セイウンアワード', 'mothers_father': 'タニノギムレット'}
    ])
    scraper._parse_stable_comment_data = MagicMock(return_value={
        '1': 'まだ素質だけで走っている感じ。使いつつ良くなってくれば。'
    })
    scraper._parse_previous_race_comment_data = MagicMock(return_value={
        '1': 'スタートで後手を踏んだのが全て。力負けではない。'
    })
    scraper._parse_horse_past_results_data = MagicMock(return_value=[
        {'date': '2025/10/20', 'venue': '東京', 'race_num': '1', 'finish_position': '1着', 'time': '1:35.0', 'jockey': 'ルメール', 'weight': '55'}
    ])
    # Bypass direct HTML parsing for horse_table in this unit test (mock the result)
    scraper._parse_horse_table_data = MagicMock(return_value={'1': {'past_results': [{'date': '2025/10/20', 'venue': '東京', 'race_num': '1', 'finish_position': '1着', 'time': '1:35.0', 'jockey': 'ルメール', 'weight': '55'}]}})

    with patch('src.scrapers.keibabook.async_playwright') as mock_async_playwright, \
         patch('src.utils.login.KeibaBookLogin.ensure_logged_in', new_callable=AsyncMock) as mock_login:
        # Mock login to always return True
        mock_login.return_value = True
        
        mock_playwright_context = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        mock_async_playwright.return_value.__aenter__.return_value = mock_playwright_context
        mock_playwright_context.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        mock_browser.new_page.return_value = mock_page
        # 初回のページ.content() に対しても mock_html が返るように設定
        mock_page.content = AsyncMock(return_value=mock_html)
        # Mock page.url to avoid the "already on page" check triggering incorrectly
        mock_page.url = "about:blank"

        # scraper._fetch_page_content のモック設定を with ブロックの前に移動
        original_fetch = scraper._fetch_page_content
        # Ensure the mocked side effects align with actual fetch usage
        # First call is for shutuba page, then training, pedigree, stable_comment, previous_race_comment
        scraper._fetch_page_content = AsyncMock(side_effect=[
            mock_html,  # shutuba page (now fetched via _fetch_page_content)
            mock_training_html,
            mock_pedigree_html,
            mock_stable_comment_html,
            mock_previous_race_comment_html,
            mock_horse_past_results_html
        ])

        scraped_data = await scraper.scrape()

        expected_shutuba_url = settings['shutuba_url']
        base_url = '/'.join(settings['shutuba_url'].split('/')[:4])
        expected_training_url = f"{base_url}/cyokyo/0/{settings['race_id']}"
        expected_pedigree_url = f"{base_url}/kettou/{settings['race_id']}"
        expected_stable_comment_url = f"{base_url}/danwa/0/{settings['race_id']}"
        expected_previous_race_comment_url = f"{base_url}/syoin/{settings['race_id']}"
        expected_horse_detail_url = f"https://s.keibabook.co.jp/db/uma/dummy_link"

        # The initial shutuba page is fetched via `page.goto` and `page.content()`,
        # subsequent pages should be fetched via `_fetch_page_content`.
        expected_urls = [
            expected_shutuba_url,  # shutuba page is now fetched via _fetch_page_content
            expected_training_url,
            expected_pedigree_url,
            expected_stable_comment_url,
            expected_previous_race_comment_url,
        ]
        # At least these URLs should have been used in calls to _fetch_page_content
        called_urls = [c.args[1] for c in scraper._fetch_page_content.mock_calls]
        for u in expected_urls:
            assert u in called_urls, f"Expected URL {u} not found in _fetch_page_content calls: {called_urls}"
        # Ensure parse was called once (content argument may vary depending on test harness)
        assert scraper._parse_race_data.call_count == 1
        scraper._parse_training_data.assert_called_once_with(mock_training_html)
        scraper._parse_pedigree_data.assert_called_once_with(mock_pedigree_html)
        scraper._parse_stable_comment_data.assert_called_once_with(mock_stable_comment_html)
        scraper._parse_previous_race_comment_data.assert_called_once_with(mock_previous_race_comment_html)
        # For JRA (default race_type), individual horse pages are not fetched
        # so _parse_horse_past_results_data is not expected to be called here.

        assert scraped_data['race_name'] == "第1回福島競馬 第1日目 1R"
        assert scraped_data['distance'] == "ダート1700m"
        assert len(scraped_data['horses']) == 1
        assert scraped_data['horses'][0]['horse_num'] == "1"
        assert scraped_data['horses'][0]['horse_name'] == "馬名1"
        assert scraped_data['horses'][0]['jockey'] == "騎手1"
        assert scraped_data['horses'][0]['horse_name_link'] == '/db/uma/dummy_link'
        assert scraped_data['horses'][0]['training_data'] == {
            'date': '11/5',
            'location': '美浦南Ｗ',
            'time': '68.9-53.5-38.6-11.9',
            'evaluation': '馬ナリ余力'
        }
        assert scraped_data['horses'][0]['pedigree_data'] == {
            'father': 'ドレフォン',
            'mother': 'セイウンアワード',
            'mothers_father': 'タニノギムレット'
        }
        assert scraped_data['horses'][0]['stable_comment'] == 'まだ素質だけで走っている感じ。使いつつ良くなってくれば。'
        assert scraped_data['horses'][0]['previous_race_comment'] == 'スタートで後手を踏んだのが全て。力負けではない。'
        assert scraped_data['horses'][0]['past_results'] == [
            {'date': '2025/10/20', 'venue': '東京', 'race_num': '1', 'finish_position': '1着', 'time': '1:35.0', 'jockey': 'ルメール', 'weight': '55'}
        ]
        scraper._fetch_page_content = original_fetch

@pytest.mark.asyncio
async def test_keibabook_scraper_parse_horse_past_results_data():
    settings = load_settings()
    scraper = KeibaBookScraper(settings)

    mock_horse_past_results_html = """
    <html>
    <body>
        <div class="HorsePastResultsTable">
            <table>
                <thead>
                    <tr>
                        <th>日付</th>
                        <th>開催</th>
                        <th>R</th>
                        <th>着順</th>
                        <th>タイム</th>
                        <th>騎手</th>
                        <th>斤量</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>2025/10/20</td>
                        <td>東京</td>
                        <td>1</td>
                        <td>1着</td>
                        <td>1:35.0</td>
                        <td>ルメール</td>
                        <td>55</td>
                    </tr>
                    <tr>
                        <td>2025/09/15</td>
                        <td>中山</td>
                        <td>5</td>
                        <td>3着</td>
                        <td>1:22.5</td>
                        <td>武豊</td>
                        <td>54</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """

    horse_past_results_data = scraper._parse_horse_past_results_data(mock_horse_past_results_html)

    assert len(horse_past_results_data) == 2
    assert horse_past_results_data[0]['date'] == "2025/10/20"
    assert horse_past_results_data[0]['venue'] == "東京"
    assert horse_past_results_data[0]['race_num'] == "1"
    assert horse_past_results_data[0]['finish_position'] == "1着"
    assert horse_past_results_data[0]['time'] == "1:35.0"
    assert horse_past_results_data[0]['jockey'] == "ルメール"
    assert horse_past_results_data[0]['weight'] == "55"
    assert horse_past_results_data[1]['date'] == "2025/09/15"
    assert horse_past_results_data[1]['venue'] == "中山"
    assert horse_past_results_data[1]['race_num'] == "5"
    assert horse_past_results_data[1]['finish_position'] == "3着"
    assert horse_past_results_data[1]['time'] == "1:22.5"
    assert horse_past_results_data[1]['jockey'] == "武豊"
    assert horse_past_results_data[1]['weight'] == "54"


@pytest.mark.asyncio
async def test_keibabook_scraper_parse_previous_race_comment_data():
    settings = load_settings()
    scraper = KeibaBookScraper(settings)

    mock_previous_race_comment_html = """
    <html>
    <body>
        <div class="PreviousRaceCommentTable">
            <div class="HorseComment">
                <p class="HorseNum">1</p>
                <p class="Comment">スタートで後手を踏んだのが全て。力負けではない。</p>
            </div>
            <div class="HorseComment">
                <p class="HorseNum">2</p>
                <p class="Comment">展開が向かなかった。次走に期待。</p>
            </div>
        </div>
    </body>
    </html>
    """

    previous_race_comment_data = scraper._parse_previous_race_comment_data(mock_previous_race_comment_html)

    assert len(previous_race_comment_data) == 2
    assert previous_race_comment_data['1'] == "スタートで後手を踏んだのが全て。力負けではない。"
    assert previous_race_comment_data['2'] == "展開が向かなかった。次走に期待。"


@pytest.mark.asyncio
async def test_keibabook_scraper_parse_stable_comment_data():
    settings = load_settings()
    scraper = KeibaBookScraper(settings)

    mock_stable_comment_html = """
    <html>
    <body>
        <div class="StableCommentTable">
            <div class="HorseComment">
                <p class="HorseNum">1</p>
                <p class="Comment">まだ素質だけで走っている感じ。使いつつ良くなってくれば。</p>
            </div>
            <div class="HorseComment">
                <p class="HorseNum">2</p>
                <p class="Comment">前走は不完全燃焼。今回は巻き返しを期待したい。</p>
            </div>
        </div>
    </body>
    </html>
    """

    stable_comment_data = scraper._parse_stable_comment_data(mock_stable_comment_html)

    assert len(stable_comment_data) == 2
    assert stable_comment_data['1'] == "まだ素質だけで走っている感じ。使いつつ良くなってくれば。"
    assert stable_comment_data['2'] == "前走は不完全燃焼。今回は巻き返しを期待したい。"


@pytest.mark.asyncio
async def test_keibabook_scraper_parse_pedigree_data():
    settings = load_settings()
    scraper = KeibaBookScraper(settings)

    # Pedigree parser expects table.kettou.sandai with 14 a.umalink_clicks per table
    mock_pedigree_html = """
    <html>
    <body>
        <table class="kettou sandai">
            <tbody>
                <tr>
                    <td>
                        <!-- 14 anchors for full 3-generation pedigree -->
                        {}
                    </td>
                </tr>
            </tbody>
        </table>
        <table class="kettou sandai">
            <tbody>
                <tr>
                    <td>
                        {}
                    </td>
                </tr>
            </tbody>
        </table>
    </body>
    </html>
    """.format(''.join([f'<a class="umalink_click">name{i}</a>' for i in range(14)]), ''.join([f'<a class="umalink_click">name{i}</a>' for i in range(14,28)]))

    pedigree_data = scraper._parse_pedigree_data(mock_pedigree_html)

    assert len(pedigree_data) == 2
    assert pedigree_data[0]['father'] == 'name0'
    assert pedigree_data[0]['mother'] == 'name3'
    assert pedigree_data[0]['mothers_father'] == 'name4'
    assert pedigree_data[1]['father'] == 'name14'
    assert pedigree_data[1]['mother'] == 'name17'
    assert pedigree_data[1]['mothers_father'] == 'name18'


@pytest.mark.asyncio
async def test_keibabook_scraper_parse_training_data():
    settings = load_settings()
    scraper = KeibaBookScraper(settings)

    # debug_training.htmlから取得した実際のHTML構造をモックとして使用
    mock_training_html = """
    <html>
    <body>
        <table class="default cyokyo">
            <tbody>
                <tr>
                    <td class="waku"><p class="waku1">1</p></td>
                    <td class="umaban">1</td>
                    <td class="kbamei"><a href="/db/uma/0945958">セイウンレガーメ</a></td>
                    <td class="tanpyo">直線の伸びひと息</td>
                    <td class="yajirusi"><span>→</span></td>
                </tr>
                <tr>
                    <td colspan="5">
                        <dl class="dl-table">
                            <dt>(前回)</dt>
                            <dt class="left">8/6&nbsp;美Ｗ&nbsp;良</dt>
                            <dt class="right">一杯に追う</dt>
                        </dl>
                        <table class="default cyokyodata">
                            <tbody>
                                <tr class="time">
                                    <td class="roku_furlong">84.5</td><td>68.2</td><td>52.7</td><td>37.8</td><td>11.9</td><td class="mawariiti">［５］</td>
                                </tr>
                            </tbody>
                        </table>
                        <dl class="dl-table">
                            <dt>助手</dt>
                            <dt class="left">10/29&nbsp;美Ｗ&nbsp;良</dt>
                            <dt class="right">一杯に追う</dt>
                        </dl>
                        <table class="default cyokyodata">
                            <tbody>
                                <tr class="time">
                                    <td class="roku_furlong"></td><td>67.0</td><td>52.3</td><td>37.9</td><td>11.7</td><td class="mawariiti">［６］</td>
                                </tr>
                                <tr class="awase">
                                    <td class="left" colspan="6">リナクィーンアスク（新馬）馬なりの内0.5秒追走同入</td>
                                </tr>
                            </tbody>
                        </table>
                        <dl class="dl-table">
                            <dt>助手</dt>
                            <dt class="left">11/2&nbsp;美Ｗ&nbsp;良</dt>
                            <dt class="right">馬なり余力</dt>
                        </dl>
                        <table class="default cyokyodata">
                            <tbody>
                                <tr class="time">
                                    <td class="roku_furlong"></td><td></td><td>60.0</td><td>44.6</td><td>14.7</td><td class="mawariiti">［７］</td>
                                </tr>
                            </tbody>
                        </table>
                        <dl class="dl-table">
                            <dt>助手</dt>
                            <dt class="left">11/5&nbsp;美Ｐ&nbsp;良</dt>
                            <dt class="right">G前仕掛け</dt>
                        </dl>
                        <table class="default cyokyodata">
                            <tbody>
                                <tr class="time">
                                    <td class="roku_furlong"></td><td>68.0</td><td>53.3</td><td>39.9</td><td>11.8</td><td class="mawariiti">［７］</td>
                                </tr>
                                <tr class="awase">
                                    <td class="left" colspan="6">アサクサダイアナ（新馬）強めの外同入</td>
                                </tr>
                            </tbody>
                        </table>
                    </td>
                </tr>
            </tbody>
        </table>
    </body>
    </html>
    """

    training_data = scraper._parse_training_data(mock_training_html)

    assert '1' in training_data
    horse_1_data = training_data['1']
    assert horse_1_data['horse_name'] == 'セイウンレガーメ'
    assert horse_1_data['tanpyo'] == '直線の伸びひと息'
    
    assert len(horse_1_data['details']) == 4

    detail_1 = horse_1_data['details'][0]
    assert detail_1['date_location'] == '8/6\xa0美Ｗ\xa0良'
    assert detail_1['追い切り方'] == '一杯に追う'
    assert detail_1['times'] == ['84.5', '68.2', '52.7', '37.8', '11.9', '［５］']
    assert detail_1['awase'] == ''

    detail_2 = horse_1_data['details'][1]
    assert detail_2['date_location'] == '10/29\xa0美Ｗ\xa0良'
    assert detail_2['追い切り方'] == '一杯に追う'
    assert detail_2['times'] == ['67.0', '52.3', '37.9', '11.7', '［６］']
    assert detail_2['awase'] == 'リナクィーンアスク（新馬）馬なりの内0.5秒追走同入'

    detail_3 = horse_1_data['details'][2]
    assert detail_3['date_location'] == '11/2\xa0美Ｗ\xa0良'
    assert detail_3['追い切り方'] == '馬なり余力'
    assert detail_3['times'] == ['60.0', '44.6', '14.7', '［７］']
    assert detail_3['awase'] == ''

    detail_4 = horse_1_data['details'][3]
    assert detail_4['date_location'] == '11/5\xa0美Ｐ\xa0良'
    assert detail_4['追い切り方'] == 'G前仕掛け'
    assert detail_4['times'] == ['68.0', '53.3', '39.9', '11.8', '［７］']
    assert detail_4['awase'] == 'アサクサダイアナ（新馬）強めの外同入'
