import os
import json
import time
import asyncio
from src.utils.config import load_settings
from src.utils.logger import get_logger
from src.utils.rate_limiter import RateLimiter
from src.scrapers.result_parser import ResultPageParser
from src.scrapers.local_racing_parser import LocalRacingParser
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

logger = get_logger(__name__)

class KeibaBookScraper:
    BASE_URL = "https://race.netkeiba.com/race/shutuba.html"

    def __init__(self, settings, db_manager=None):
        """
        Args:
            settings: 設定辞書
            db_manager: CSVDBManagerインスタンス（オプション、重複チェック用）
        """
        self.settings = settings
        self.shutuba_url = settings.get('shutuba_url', '')
        self.seiseki_url = settings.get('seiseki_url', '')  # 結果ページURL
        self.race_type = settings.get('race_type', 'jra')  # 'jra' or 'nar'
        self.skip_duplicate_check = settings.get('skip_duplicate_check', False)  # 重複チェックをスキップするか
        self.db_manager = db_manager
        self.result_parser = ResultPageParser()  # 結果ページパーサー
        self.local_parser = LocalRacingParser()  # 地方競馬専用パーサー
        self.rate_limiter = RateLimiter(self.settings.get('rate_limit_base'))  # レート制御
        # record fetch details for debugging and perf analysis
        self._last_fetches = []
        self._comments_concurrency = int(self.settings.get('comments_concurrency', 1))
        self._parallel_page_fetch = bool(self.settings.get('parallel_page_fetch', False))
        
        # 競馬種別に応じたベースURL設定
        if self.race_type == 'nar':
            # 地方競馬の場合のURLパターン（実際のURL構造に応じて調整が必要）
            self.base_url_pattern = "https://s.keibabook.co.jp/chihou"
        else:
            # 中央競馬の場合
            self.base_url_pattern = "https://s.keibabook.co.jp/cyuou"

    async def _fetch_page_content(self, page, url, retry_count=3, retry_delay=2, wait_until=None):
        """
        ページコンテンツを取得（リトライ機能付き）
        
        Args:
            page: Playwrightのページオブジェクト
            url: 取得するURL
            retry_count: リトライ回数
            retry_delay: リトライ間隔（秒）
            
        Returns:
            HTMLコンテンツ
        """
        for attempt in range(retry_count):
            try:
                t_start = time.perf_counter()
                wu = wait_until if wait_until else self.settings.get('playwright_wait_until', 'domcontentloaded')
                response = await page.goto(url, wait_until=wu, timeout=self.settings.get("playwright_timeout", 30000))
                t_goto = time.perf_counter()
                status = None
                try:
                    if response:
                        status = response.status
                except Exception:
                    status = None
                if status:
                    logger.debug(f"HTTP status for {url}: {status}")
                # If server returns Too Many Requests (429) escalate backoff
                if status == 429:
                    # exponential wait (increase with attempt) - capped at 30s to avoid long waits
                    wait_seconds = min(10 * (attempt + 1), 30)
                    logger.warning(f"429 Too Many Requests detected for {url}: waiting {wait_seconds}s before retrying")
                    await asyncio.sleep(wait_seconds)
                    continue
                content = await page.content()
                t_content = time.perf_counter()
                logger.info(f"ページ取得成功: {url}")
                # Save debug fetch detail
                try:
                    actual_url = response.url if response else getattr(page, 'url', None)
                except Exception:
                    actual_url = None
                self._last_fetches.append({
                    'requested_url': url,
                    'actual_url': actual_url,
                    'status': status,
                    'goto_ms': (t_goto - t_start) * 1000,
                    'content_ms': (t_content - t_goto) * 1000,
                    'total_ms': (t_content - t_start) * 1000
                })
                if self.settings.get('perf'):
                    logger.info(f"PERF page_fetch: {url} goto_ms={(t_goto - t_start)*1000:.0f} content_ms={(t_content - t_goto)*1000:.0f} total_ms={(t_content - t_start)*1000:.0f}")
                return content
            except Exception as e:
                if attempt < retry_count - 1:
                    logger.warning(f"ページ取得失敗（リトライ {attempt + 1}/{retry_count}）: {url} - {e}")
                    await asyncio.sleep(retry_delay * (attempt + 1))  # 指数バックオフ
                else:
                    logger.error(f"ページ取得最終失敗: {url} - {e}")
                    raise

    def _parse_race_data(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        race_data = {}

        # レース名とグレード
        racemei_p_elements = soup.select(".racemei p")
        if len(racemei_p_elements) > 1:
            race_data['race_name'] = racemei_p_elements[0].get_text(strip=True)
            race_data['race_grade'] = racemei_p_elements[1].get_text(strip=True)

        # 距離
        racetitle_sub_p_elements = soup.select(".racetitle_sub p")
        if len(racetitle_sub_p_elements) > 1:
            distance_text = racetitle_sub_p_elements[1].get_text(strip=True)
            # "1150m (ダート・右) 曇・良" のような形式から距離を抽出
            race_data['distance'] = distance_text.split(' ')[0]

        # 出馬表
        horses = []
        shutuba_table = soup.select_one(".syutuba_sp tbody")
        if shutuba_table:
            for row in shutuba_table.find_all('tr'):
                horse_num_elem = row.select_one(".umaban")
                horse_name_elem = row.select_one(".kbamei a")
                jockey_elem = row.select_one(".kisyu a")
                
                # 予想印 (tmyoso)
                mark_elem = row.select_one(".tmyoso")
                mark = mark_elem.get_text(strip=True) if mark_elem else ""
                
                # オッズ・人気 (lh1クラスなどにある場合が多いが、構造が複雑なためテキストから抽出)
                # 例: 436(+20)188.315人気 -> 188.3, 15人気
                odds_pop_elem = row.select_one(".lh1")
                odds = ""
                popularity = ""
                if odds_pop_elem:
                    text = odds_pop_elem.get_text(strip=True)
                    # 簡易的な抽出（正規表現などが望ましいが、まずはテキスト全体を保存）
                    # "人気"で分割してみる
                    if "人気" in text:
                        parts = text.split("人気")
                        if len(parts) > 0:
                            # 直前の数値をオッズ、その前を人気と推定
                            # ここでは単純にテキスト全体を保存しておく
                            pass
                    odds = text # 一旦そのまま保存

                if horse_num_elem and horse_name_elem and jockey_elem:
                    horse_name_link = horse_name_elem['href'] if horse_name_elem.has_attr('href') else ""
                    horses.append({
                        'horse_num': horse_num_elem.get_text(strip=True),
                        'horse_name': horse_name_elem.get_text(strip=True),
                        'jockey': jockey_elem.get_text(strip=True),
                        'horse_name_link': horse_name_link,
                        'prediction_mark': mark,
                        'odds_text': odds # 後で加工できるようにテキスト全体を保存
                    })
        race_data['horses'] = horses
        return race_data

    def _parse_training_data(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        training_data = {}

        training_table = soup.select_one("table.default.cyokyo tbody")
        if not training_table:
            return training_data

        rows = training_table.find_all('tr', recursive=False)
        current_horse_num = None
        
        i = 0
        while i < len(rows):
            row = rows[i]
            
            # 馬番、馬名、短評の行
            if row.select_one(".umaban") and row.select_one(".kbamei a"):
                horse_num_elem = row.select_one(".umaban")
                horse_name_elem = row.select_one(".kbamei a")
                tanpyo_elem = row.select_one(".tanpyo")

                current_horse_num = horse_num_elem.get_text(strip=True)
                training_data[current_horse_num] = {
                    'horse_name': horse_name_elem.get_text(strip=True),
                    'tanpyo': tanpyo_elem.get_text(strip=True) if tanpyo_elem else '',
                    'details': []
                }
                i += 1
                continue

            # 調教詳細の行
            elif current_horse_num and row.find('td', colspan='5'):
                detail_cell = row.find('td', colspan='5')
                
                elements = detail_cell.find_all(recursive=False)
                
                current_detail = None
                for elem in elements:
                    if elem.name == 'dl' and 'dl-table' in elem.get('class', []):
                        if current_detail:
                            training_data[current_horse_num]['details'].append(current_detail)
                        
                        current_detail = {}
                        date_location_elem = elem.select_one("dt.left")
                        oikiri_elem = elem.select_one("dt.right")
                        current_detail['date_location'] = date_location_elem.get_text(strip=True) if date_location_elem else ''
                        current_detail['追い切り方'] = oikiri_elem.get_text(strip=True) if oikiri_elem else ''
                        current_detail['times'] = []
                        current_detail['awase'] = ''

                    elif elem.name == 'table' and 'cyokyodata' in elem.get('class', []):
                        if current_detail:
                            time_elems = elem.select("tr.time td")
                            current_detail['times'] = [t.get_text(strip=True) for t in time_elems if t.get_text(strip=True)]
                            
                            awase_row = elem.select_one("tr.awase td.left")
                            if awase_row:
                                current_detail['awase'] = awase_row.get_text(strip=True)
                
                if current_detail:
                    training_data[current_horse_num]['details'].append(current_detail)
                
                i += 1
            else:
                i += 1
        return training_data

    def _parse_pedigree_data(self, html_content):
        """
        血統データをパース（三代血統完全版）
        実際のHTML構造: table.kettou.sandai
        
        ログイン済みの場合、三代血統全体が取得可能:
        
        1代前 (2頭):
        - links[0]: 父
        - links[3]: 母
        
        2代前 (4頭):
        - links[1]: 父父 (父の父)
        - links[2]: 父母 (父の母)
        - links[4]: 母父 (母の父)
        - links[5]: 母母 (母の母)
        
        3代前 (8頭):
        - links[6]: 父父父
        - links[7]: 父父母
        - links[8]: 父母父
        - links[9]: 父母母
        - links[10]: 母父父
        - links[11]: 母父母
        - links[12]: 母母父
        - links[13]: 母母母
        
        合計: 2 + 4 + 8 = 14頭
        
        注意: 血統ページには馬番が含まれていないため、
        出馬表の馬の順番と血統テーブルの順番が一致していると仮定
        
        Returns:
            リスト形式で血統データを返す（後で馬番とマッチング）
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        pedigree_list = []

        # 実際のHTML構造: table.kettou.sandai
        pedigree_tables = soup.select("table.kettou.sandai")
        
        for table in pedigree_tables:
            # テーブル内のリンクを取得
            links = table.select("a.umalink_click")
            
            if len(links) >= 14:
                # 三代血統完全版（14頭）
                pedigree_data = {
                    # 1代前
                    'father': links[0].get_text(strip=True).replace('\n', ' '),
                    'mother': links[3].get_text(strip=True).replace('\n', ' '),
                    
                    # 2代前
                    'father_father': links[1].get_text(strip=True).replace('\n', ' '),
                    'father_mother': links[2].get_text(strip=True).replace('\n', ' '),
                    'mothers_father': links[4].get_text(strip=True).replace('\n', ' '),
                    'mothers_mother': links[5].get_text(strip=True).replace('\n', ' '),
                    
                    # 3代前
                    'father_father_father': links[6].get_text(strip=True).replace('\n', ' '),
                    'father_father_mother': links[7].get_text(strip=True).replace('\n', ' '),
                    'father_mother_father': links[8].get_text(strip=True).replace('\n', ' '),
                    'father_mother_mother': links[9].get_text(strip=True).replace('\n', ' '),
                    'mothers_father_father': links[10].get_text(strip=True).replace('\n', ' '),
                    'mothers_father_mother': links[11].get_text(strip=True).replace('\n', ' '),
                    'mothers_mother_father': links[12].get_text(strip=True).replace('\n', ' '),
                    'mothers_mother_mother': links[13].get_text(strip=True).replace('\n', ' ')
                }
                
                pedigree_list.append(pedigree_data)
                logger.debug(f"三代血統完全取得(14頭): 父={pedigree_data['father']}, 母={pedigree_data['mother']}")
            elif len(links) >= 6:
                # 二代血統まで（6頭）
                pedigree_data = {
                    # 1代前
                    'father': links[0].get_text(strip=True).replace('\n', ' '),
                    'mother': links[3].get_text(strip=True).replace('\n', ' '),
                    
                    # 2代前
                    'father_father': links[1].get_text(strip=True).replace('\n', ' '),
                    'father_mother': links[2].get_text(strip=True).replace('\n', ' '),
                    'mothers_father': links[4].get_text(strip=True).replace('\n', ' '),
                    'mothers_mother': links[5].get_text(strip=True).replace('\n', ' '),
                    
                    # 3代前（データなし）
                    'father_father_father': '',
                    'father_father_mother': '',
                    'father_mother_father': '',
                    'father_mother_mother': '',
                    'mothers_father_father': '',
                    'mothers_father_mother': '',
                    'mothers_mother_father': '',
                    'mothers_mother_mother': ''
                }
                
                pedigree_list.append(pedigree_data)
                logger.warning(f"二代血統のみ(6頭): 父={pedigree_data['father']}, 母={pedigree_data['mother']}")
            elif len(links) >= 3:
                # ログインしていない場合（父、母、母父のみ）
                # 母馬と母父を取得（hinbaクラス内）
                mother_links = table.select("td.hinba a.umalink_click")
                mother = mother_links[0].get_text(strip=True).replace('\n', ' ') if len(mother_links) > 0 else ''
                mothers_father = mother_links[1].get_text(strip=True).replace('\n', ' ') if len(mother_links) > 1 else ''
                
                pedigree_data = {
                    # 1代前
                    'father': links[0].get_text(strip=True).replace('\n', ' '),
                    'mother': mother,
                    
                    # 2代前
                    'father_father': '',
                    'father_mother': '',
                    'mothers_father': mothers_father,
                    'mothers_mother': '',
                    
                    # 3代前（データなし）
                    'father_father_father': '',
                    'father_father_mother': '',
                    'father_mother_father': '',
                    'father_mother_mother': '',
                    'mothers_father_father': '',
                    'mothers_father_mother': '',
                    'mothers_mother_father': '',
                    'mothers_mother_mother': ''
                }
                
                pedigree_list.append(pedigree_data)
                logger.warning(f"血統データ不完全（ログイン未済?）: 父={pedigree_data['father']}, 母={pedigree_data['mother']}")
            else:
                logger.warning(f"血統データ不足: {len(links)}個のリンクのみ")
        
        logger.debug(f"血統データ取得: {len(pedigree_list)}頭分")
        return pedigree_list

    def _parse_stable_comment_data(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        stable_comment_data = {}

        comment_divs = soup.select(".StableCommentTable .HorseComment")
        for comment_div in comment_divs:
            horse_num_elem = comment_div.select_one(".HorseNum")
            comment_elem = comment_div.select_one(".Comment")

            if horse_num_elem and comment_elem:
                horse_num = horse_num_elem.get_text(strip=True)
                stable_comment_data[horse_num] = comment_elem.get_text(strip=True)
        return stable_comment_data

    def _parse_previous_race_comment_data(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        previous_race_comment_data = {}

        comment_divs = soup.select(".PreviousRaceCommentTable .HorseComment")
        for comment_div in comment_divs:
            horse_num_elem = comment_div.select_one(".HorseNum")
            comment_elem = comment_div.select_one(".Comment")

            if horse_num_elem and comment_elem:
                horse_num = horse_num_elem.get_text(strip=True)
                previous_race_comment_data[horse_num] = comment_elem.get_text(strip=True)
        return previous_race_comment_data

    def _parse_horse_past_results_data(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        past_results = []

        results_table = soup.select_one(".HorsePastResultsTable tbody")
        if results_table:
            for row in results_table.find_all('tr'):
                columns = row.find_all('td')
                if len(columns) >= 7: # 日付, 開催, R, 着順, タイム, 騎手, 斤量
                    past_results.append({
                        'date': columns[0].get_text(strip=True),
                        'venue': columns[1].get_text(strip=True),
                        'race_num': columns[2].get_text(strip=True),
                        'finish_position': columns[3].get_text(strip=True),
                        'time': columns[4].get_text(strip=True),
                        'jockey': columns[5].get_text(strip=True),
                        'weight': columns[6].get_text(strip=True)
                    })
        return past_results
    
    def _parse_horse_table_data(self, html_content):
        """
        馬柱（能力表）HTMLから過去走情報を取得
        出馬表ページに含まれる馬柱情報をパース
        過去3走分を取得（予想に必要）
        
        注意: 個別馬ページを開くのは大変なため、馬柱から取得する方針
        実際のHTML構造に応じてセレクタを調整が必要
        
        Args:
            html_content: 出馬表ページのHTML
            
        Returns:
            馬番をキーとした過去成績データの辞書（過去3走分）
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        horse_table_data = {}
        
        # 出馬表テーブルから各馬の情報を取得
        shutuba_table = soup.select_one(".syutuba_sp tbody")
        if not shutuba_table:
            logger.warning("出馬表テーブルが見つかりません")
            return horse_table_data
        
        for row in shutuba_table.find_all('tr'):
            horse_num_elem = row.select_one(".umaban")
            if not horse_num_elem:
                continue
            
            horse_num = horse_num_elem.get_text(strip=True)
            
            # 馬柱の過去成績を探す
            # 複数のセレクタパターンを試す（実際のHTML構造に応じて調整）
            past_results = []
            
            # パターン1: 同じ行内の過去成績テーブル
            past_results_table = row.select_one(".HorsePastResultsTable, .past_results, table.past_results")
            
            # パターン2: 次の行（展開された詳細行）を探す
            if not past_results_table:
                next_row = row.find_next_sibling('tr')
                if next_row:
                    past_results_table = next_row.select_one(".HorsePastResultsTable, .past_results, table.past_results")
            
            # パターン3: 親要素内を探す
            if not past_results_table:
                parent = row.parent
                if parent:
                    past_results_table = parent.select_one(".HorsePastResultsTable, .past_results")
            
            if past_results_table:
                # テーブル行を取得
                result_rows = past_results_table.find_all('tr')
                if not result_rows:
                    # tbody内を探す
                    tbody = past_results_table.find('tbody')
                    if tbody:
                        result_rows = tbody.find_all('tr')
                
                for result_row in result_rows:
                    cols = result_row.find_all('td')
                    if len(cols) >= 7:  # 日付, 開催, R, 着順, タイム, 騎手, 斤量
                        past_results.append({
                            'date': cols[0].get_text(strip=True),
                            'venue': cols[1].get_text(strip=True),
                            'race_num': cols[2].get_text(strip=True),
                            'finish_position': cols[3].get_text(strip=True),
                            'time': cols[4].get_text(strip=True),
                            'jockey': cols[5].get_text(strip=True),
                            'weight': cols[6].get_text(strip=True)
                        })
                
                # 過去3走分に制限（予想に必要な分）
                past_results = past_results[:3]
                horse_table_data[horse_num] = {
                    'past_results': past_results
                }
                logger.debug(f"馬{horse_num}: {len(past_results)}走分の過去成績を取得")
            else:
                # 馬柱情報が見つからない場合は空のリスト
                horse_table_data[horse_num] = {
                    'past_results': []
                }
                logger.debug(f"馬{horse_num}: 過去成績が見つかりませんでした")
        
        return horse_table_data
    
    async def _scrape_result_page(self, page, base_url):
        """
        結果ページをスクレイピング
        
        Args:
            page: Playwrightのページオブジェクト
            base_url: ベースURL
            
        Returns:
            結果ページのデータ
        """
        if not self.seiseki_url:
            return None
        
        try:
            # 重複チェック
            if not self.skip_duplicate_check and self.db_manager and self.db_manager.is_url_fetched(self.seiseki_url):
                logger.info(f"スキップ（既取得）: {self.seiseki_url}")
                return None
            
            # 結果ページを取得
            result_html_content = await self._fetch_page_content(page, self.seiseki_url)
            
            # URL取得をログに記録
            if self.db_manager:
                self.db_manager.log_url(self.seiseki_url, self.settings['race_id'], 'result', 'success')
            
            # デバッグ用にHTMLを保存
            with open("debug_result.html", "w", encoding="utf-8") as f:
                f.write(result_html_content)
            
            # 結果ページをパース
            result_data = self.result_parser.parse_result_page(result_html_content)
            
            logger.info(f"結果ページ取得成功: {len(result_data.get('horses', []))}頭")
            return result_data
            
        except Exception as e:
            logger.error(f"結果ページ取得エラー: {e}")
            return None
    
    async def _scrape_point_page(self, page, base_url):
        """
        地方競馬のポイントページをスクレイピング
        
        Args:
            page: Playwrightのページオブジェクト
            base_url: ベースURL
            
        Returns:
            ポイント情報データ
        """
        if self.race_type != 'nar':
            return None
        
        try:
            # ポイントページのURL（実際のURL構造に応じて調整が必要）
            point_url = f"{base_url}/point/{self.settings['race_id']}"
            
            # 重複チェック
            if not self.skip_duplicate_check and self.db_manager and self.db_manager.is_url_fetched(point_url):
                logger.info(f"スキップ（既取得）: {point_url}")
                return None
            
            # レート制御
            await self.rate_limiter.wait()
            
            # ポイントページを取得
            point_html_content = await self._fetch_page_content(page, point_url)
            
            # URL取得をログに記録
            if self.db_manager:
                self.db_manager.log_url(point_url, self.settings['race_id'], 'point', 'success')
            
            # デバッグ用にHTMLを保存
            with open("debug_point.html", "w", encoding="utf-8") as f:
                f.write(point_html_content)
            
            # ポイントページをパース
            point_data = self.local_parser.parse_point_page(point_html_content)
            
            logger.info(f"ポイント情報取得成功: {len(point_data.get('big_upset_horses', []))}頭の大穴情報など")
            return point_data
            
        except Exception as e:
            logger.error(f"ポイントページ取得エラー: {e}")
            return None
    
    async def _scrape_horse_comments(self, page, horses, base_url, context=None):
        """
        個別馬のコメントを取得（地方競馬専用、穴馬のヒント）

        Args:
            page: Playwrightのページオブジェクト
            horses: list of horses dicts
            base_url: base URL for local racing
        """
        # Default: sequential fetch to avoid hitting site too fast
        import asyncio
        concurrency = max(1, int(self._comments_concurrency))
        semaphore = asyncio.Semaphore(concurrency)

        async def fetch_comment(horse):
            horse_num = horse.get('horse_num')
            if not horse_num:
                return
            horse_link = horse.get('horse_name_link', '')
            if not horse_link:
                horse['individual_comment'] = ""
                return
            horse_detail_url = f"https://s.keibabook.co.jp{horse_link}"
            comment_key = f"{horse_detail_url}_comment"
            if not self.skip_duplicate_check and self.db_manager and self.db_manager.is_url_fetched(comment_key):
                logger.debug(f"馬{horse_num}のコメントは既取得")
                horse['individual_comment'] = ""
                return
            async with semaphore:
                try:
                    await self.rate_limiter.wait()
                    # If concurrency > 1 and a context is provided, use a dedicated page per task to avoid page navigation collision
                    task_page = page
                    created_task_page = False
                    if concurrency > 1 and context is not None:
                        task_page = await context.new_page()
                        created_task_page = True
                    horse_html_content = await self._fetch_page_content(task_page, horse_detail_url)
                    comment = self.local_parser.parse_horse_comment(horse_html_content, horse_num)
                    if comment:
                        horse['individual_comment'] = comment
                        logger.debug(f"馬{horse_num}のコメント取得: {comment[:50]}...")
                        if self.db_manager:
                            self.db_manager.log_url(comment_key, self.settings['race_id'], 'horse_comment', 'success')
                    else:
                        horse['individual_comment'] = ""
                except Exception as e:
                    logger.warning(f"馬{horse_num}のコメント取得エラー: {e}")
                    horse['individual_comment'] = ""
                finally:
                    if 'created_task_page' in locals() and created_task_page:
                        try:
                            await task_page.close()
                        except Exception:
                            pass

        # If concurrency == 1, run sequentially to maintain original behavior
        if concurrency <= 1:
            for h in horses:
                await fetch_comment(h)
        else:
            tasks = [fetch_comment(h) for h in horses]
            if tasks:
                await asyncio.gather(*tasks)

        logger.info("個別馬のコメント取得完了")

    async def scrape(self, context=None, page=None):
        # If a page/context is provided, use it to avoid launching a new browser.
        created_browser = False
        browser = None
        if page is None or context is None:
            created_browser = True
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().__aenter__()
            browser = await self._playwright.chromium.launch(headless=self.settings.get("playwright_headless", True))
            context = await browser.new_context()
            page = await context.new_page()
        
        try:
            perf_enabled = self.settings.get('perf', False)
            if perf_enabled:
                overall_start = time.perf_counter()
            # タイムアウト設定（任意）
            timeout_ms = self.settings.get("playwright_timeout")
            if timeout_ms:
                page.set_default_timeout(timeout_ms)

            # ログイン確保: コンテキストに cookie をロードした上でログイン済みでなければログインを実行
            from src.utils.login import KeibaBookLogin
            cookie_file = self.settings.get('cookie_file', 'cookies.json')
            login_id = self.settings.get('login_id')
            password = self.settings.get('login_password')
            url = self.shutuba_url
            login_ok = await KeibaBookLogin.ensure_logged_in(context, login_id, password, cookie_file=cookie_file, save_cookies=True, test_url=url)
            if not login_ok:
                logger.warning("ログインに失敗しました。無料範囲のデータのみ取得されます。")
            
            # 重複チェック（DBマネージャーが設定されている場合）
            if not self.skip_duplicate_check and self.db_manager and self.db_manager.is_url_fetched(url):
                logger.info(f"スキップ（既取得）: {url}")
                # 既存データを返すか、空データを返すかは要件次第
                # ここでは空データを返す（差分取得が必要な場合は別途実装）
                return {}
            
            # レート制御: サイト負担を軽減
            await self.rate_limiter.wait()
            
            # ログイン後に出馬表URLに遷移してコンテンツを取得
            html_content = await self._fetch_page_content(page, url)
            
            # URL取得をログに記録
            if self.db_manager:
                self.db_manager.log_url(url, self.settings['race_id'], 'shutuba', 'success')
            
            # --- デバッグ用にHTMLをファイルに保存 ---
            # Debug: ensure what's written is a str to avoid mock coroutine issues
            try:
                if isinstance(html_content, (bytes, bytearray)):
                    html_text = html_content.decode('utf-8', errors='replace')
                elif isinstance(html_content, str):
                    html_text = html_content
                else:
                    # Fallback for mocked objects: convert to str
                    html_text = str(html_content)
            except Exception:
                html_text = str(html_content)
            race_key = self.settings.get('race_key', 'unknown')
            if not self.settings.get('skip_debug_files', False):
                with open(f"debug_page_{race_key}.html", "w", encoding="utf-8") as f:
                    f.write(html_text)
            # ------------------------------------

            race_data = self._parse_race_data(html_content)

            # 地方競馬の場合は最小限のデータのみ取得（馬柱、出馬表、血統）
            # 中央競馬の場合は全データを取得
            
            # 調教データを取得してマージ（地方競馬ではスキップ）
            if self.race_type != 'nar':
                base_url = '/'.join(self.settings['shutuba_url'].split('/')[:4])
                training_url = f"{base_url}/cyokyo/0/{self.settings['race_id']}"
            else:
                training_url = None
            
            # 調教データ取得（地方競馬ではスキップ）
            if training_url and not self.settings.get('skip_training', False):
                # レート制御
                await self.rate_limiter.wait()
                
                # 重複チェック
                if not (not self.skip_duplicate_check and self.db_manager and self.db_manager.is_url_fetched(training_url)):
                    training_html_content = await self._fetch_page_content(page, training_url)
                    if self.db_manager:
                        self.db_manager.log_url(training_url, self.settings['race_id'], 'training', 'success')
                    if not self.settings.get('skip_debug_files', False):
                        with open(f"debug_training_{race_key}.html", "w", encoding="utf-8") as f:
                            f.write(training_html_content)
                else:
                    logger.info(f"スキップ（既取得）: {training_url}")
                    training_html_content = ""
                
                parsed_training_data = self._parse_training_data(training_html_content) if training_html_content else {}
            else:
                parsed_training_data = {}
                logger.info("地方競馬のため調教データをスキップ")

            for horse in race_data.get('horses', []):
                horse_num = horse.get('horse_num')
                if horse_num in parsed_training_data:
                    horse['training_data'] = parsed_training_data[horse_num]
                else:
                    horse['training_data'] = {}

            # 血統データを取得してマージ（馬柱、出馬表、血統は必須）
            base_url = '/'.join(self.settings['shutuba_url'].split('/')[:4])
            pedigree_url = f"{base_url}/kettou/{self.settings['race_id']}"
            
            # レート制御
            await self.rate_limiter.wait()
            
            # 重複チェック
            if not (not self.skip_duplicate_check and self.db_manager and self.db_manager.is_url_fetched(pedigree_url)) and not self.settings.get('skip_pedigree', False):
                pedigree_html_content = await self._fetch_page_content(page, pedigree_url)
                if self.db_manager:
                    self.db_manager.log_url(pedigree_url, self.settings['race_id'], 'pedigree', 'success')
                if not self.settings.get('skip_debug_files', False):
                    with open(f"debug_pedigree_{race_key}.html", "w", encoding="utf-8") as f:
                        f.write(pedigree_html_content)
            else:
                logger.info(f"スキップ（既取得）: {pedigree_url}")
                pedigree_html_content = ""
            
            parsed_pedigree_data = self._parse_pedigree_data(pedigree_html_content) if pedigree_html_content else []

            # 血統データをインデックスでマッチング（血統ページには馬番がないため）
            horses = race_data.get('horses', [])
            for idx, horse in enumerate(horses):
                if idx < len(parsed_pedigree_data):
                    horse['pedigree_data'] = parsed_pedigree_data[idx]
                else:
                    horse['pedigree_data'] = {}

            # 厩舎の話データを取得してマージ（地方競馬ではスキップ）
            if self.race_type != 'nar' and not self.settings.get('skip_stable_comment', False):
                stable_comment_url = f"{base_url}/danwa/0/{self.settings['race_id']}"
                
                # レート制御
                await self.rate_limiter.wait()
                
                # 重複チェック
                if not (not self.skip_duplicate_check and self.db_manager and self.db_manager.is_url_fetched(stable_comment_url)):
                    stable_comment_html_content = await self._fetch_page_content(page, stable_comment_url)
                    if self.db_manager:
                        self.db_manager.log_url(stable_comment_url, self.settings['race_id'], 'stable_comment', 'success')
                    if not self.settings.get('skip_debug_files', False):
                        with open(f"debug_stable_comment_{race_key}.html", "w", encoding="utf-8") as f:
                            f.write(stable_comment_html_content)
                else:
                    logger.info(f"スキップ（既取得）: {stable_comment_url}")
                    stable_comment_html_content = ""
                
                parsed_stable_comment_data = self._parse_stable_comment_data(stable_comment_html_content) if stable_comment_html_content else {}
            else:
                parsed_stable_comment_data = {}
                logger.info("地方競馬のため厩舎コメントをスキップ")

            for horse in race_data.get('horses', []):
                horse_num = horse.get('horse_num')
                if horse_num in parsed_stable_comment_data:
                    horse['stable_comment'] = parsed_stable_comment_data[horse_num]
                else:
                    horse['stable_comment'] = ""

            # 前走コメントデータを取得してマージ（地方競馬ではスキップ）
            if self.race_type != 'nar' and not self.settings.get('skip_previous_race_comment', False):
                previous_race_comment_url = f"{base_url}/syoin/{self.settings['race_id']}"
                
                # レート制御
                await self.rate_limiter.wait()
                
                # 重複チェック
                if not (not self.skip_duplicate_check and self.db_manager and self.db_manager.is_url_fetched(previous_race_comment_url)):
                    previous_race_comment_url_content = await self._fetch_page_content(page, previous_race_comment_url)
                    if self.db_manager:
                        self.db_manager.log_url(previous_race_comment_url, self.settings['race_id'], 'previous_race_comment', 'success')
                    if not self.settings.get('skip_debug_files', False):
                        with open(f"debug_previous_race_comment_{race_key}.html", "w", encoding="utf-8") as f:
                            f.write(previous_race_comment_url_content)
                else:
                    logger.info(f"スキップ（既取得）: {previous_race_comment_url}")
                    previous_race_comment_url_content = ""
                
                parsed_previous_race_comment_data = self._parse_previous_race_comment_data(previous_race_comment_url_content) if previous_race_comment_url_content else {}
            else:
                parsed_previous_race_comment_data = {}
                logger.info("地方競馬のため前走コメントをスキップ")

            for horse in race_data.get('horses', []):
                horse_num = horse.get('horse_num')
                if horse_num in parsed_previous_race_comment_data:
                    horse['previous_race_comment'] = parsed_previous_race_comment_data[horse_num]
                else:
                    horse['previous_race_comment'] = ""

            # 馬柱（能力表）データを取得（出馬表ページから）- 簡易情報として
            if self.settings.get('skip_past_results', False):
                horse_table_data = {}
            else:
                # 個別馬ページへの遷移は行わない（被りが多いため）
                horse_table_data = self._parse_horse_table_data(html_content)
            for horse in race_data.get('horses', []):
                horse_num = horse.get('horse_num')
                if horse_num in horse_table_data:
                    horse['past_results'] = horse_table_data[horse_num].get('past_results', [])
                else:
                    horse['past_results'] = []
            
            # 地方競馬の場合、ポイント情報と個別馬コメントを取得
            if self.race_type == 'nar':
                # ポイントページを取得
                point_data = await self._scrape_point_page(page, base_url)
                if point_data:
                    race_data['point_info'] = point_data
                
                # 個別馬のコメントを取得（穴馬のヒント）
                # Keep sequential by default (comments_concurrency defaults to 1)
                await self._scrape_horse_comments(page, race_data.get('horses', []), base_url)

            # 結果ページから詳細情報を取得（レース終了後のみ）
            # 現時点では予想用データ収集が目的のため、結果ページはスキップ
            # レース終了後、過去データを蓄積する際に結果ページから詳細情報を取得
            # if self.seiseki_url:
            #     result_data = await self._scrape_result_page(page, base_url)
            #     if result_data:
            #         # 結果ページのデータをマージ
            #         race_data['result_info'] = result_data.get('race_info', {})
            #         race_data['result_horses'] = result_data.get('horses', [])
            #         race_data['payouts'] = result_data.get('payouts', {})
            #         
            #         # 結果ページの馬データを出馬表の馬データにマージ
            #         result_horses_dict = {h.get('horse_num'): h for h in result_data.get('horses', [])}
            #         for horse in race_data.get('horses', []):
            #             horse_num = horse.get('horse_num')
            #             if horse_num in result_horses_dict:
            #                 result_horse = result_horses_dict[horse_num]
            #                 # 結果ページの詳細情報をマージ
            #                 horse['result_rank'] = result_horse.get('rank')
            #                 horse['result_time'] = result_horse.get('time')
            #                 horse['result_margin'] = result_horse.get('margin')
            #                 horse['result_passing'] = result_horse.get('passing')
            #                 horse['result_last_3f'] = result_horse.get('last_3f')
            #                 horse['odds'] = result_horse.get('odds')
            #                 horse['popularity'] = result_horse.get('popularity')

            if perf_enabled:
                overall_end = time.perf_counter()
                logger.info(f"PERF total_race_scrape_ms={(overall_end - overall_start)*1000:.0f} for {self.settings.get('race_id')}")
            # Save debug fetch summary
            if not self.settings.get('skip_debug_files', False):
                try:
                    with open(f"debug_fetches_{race_key}.json", "w", encoding="utf-8") as f:
                        import json
                        json.dump(self._last_fetches, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
            return race_data
        finally:
            if created_browser and browser:
                try:
                    await browser.close()
                except Exception:
                    pass
                try:
                    await self._playwright.__aexit__(None, None, None)
                except Exception:
                    pass