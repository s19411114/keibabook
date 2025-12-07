import os
import json
import time
import asyncio
from src.utils.config import load_settings
from src.utils.logger import get_logger
from src.utils.rate_limiter import RateLimiter
from src.scrapers.result_parser import ResultPageParser
from src.scrapers.local_racing_parser import LocalRacingParser
from src.scrapers.jra_special_parser import JRASpecialParser
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
        self.jra_parser = JRASpecialParser()  # 中央競馬専用パーサー（CPU予想等）
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
        """
        出馬表ページから全データを取得
        
        取得データ:
        - レース情報: レース名、グレード、距離、コース条件（天候・馬場含む）
        - レース条件テキスト: クラス、斤量条件、賞金など（そのまま文字列として保存）
        - 馬情報: 枠番、馬番、予想印（個別予想家印含む）、馬名、年齢、騎手、斤量、短評/見解、オッズ、人気
        - 展開予想: ペース、隊列予想（逃げ/好位/中位/後方）、展開コメント
        - 全体コメント: レース全体の予想コメント
        """
        import re
        soup = BeautifulSoup(html_content, 'html.parser')
        race_data = {}

        # レース名とグレード
        racemei_p_elements = soup.select(".racemei p")
        if len(racemei_p_elements) > 1:
            race_data['race_name'] = racemei_p_elements[0].get_text(strip=True)
            race_data['race_grade'] = racemei_p_elements[1].get_text(strip=True)

        # 距離・コース条件（例: "2000m (ダート・左) 晴・良"）
        racetitle_sub_p_elements = soup.select(".racetitle_sub p")
        if len(racetitle_sub_p_elements) > 1:
            full_condition = racetitle_sub_p_elements[1].get_text(strip=True)
            race_data['full_condition'] = full_condition
            # 距離を抽出
            distance_match = re.search(r'(\d+m)', full_condition)
            race_data['distance'] = distance_match.group(1) if distance_match else full_condition.split(' ')[0]
            # コース条件を抽出（ダート/芝、左右、天候・馬場）
            course_match = re.search(r'\((.*?)\)', full_condition)
            race_data['course'] = course_match.group(1) if course_match else ''
            weather_match = re.search(r'\)\s*(.+)$', full_condition)
            race_data['weather_track'] = weather_match.group(1) if weather_match else ''
        
        # レース条件テキスト（クラス、斤量条件、特別指定など）- そのまま文字列保存
        if len(racetitle_sub_p_elements) > 0:
            race_data['race_class'] = racetitle_sub_p_elements[0].get_text(strip=True)
        
        # 追加条件要素を探す（.racebaseなど）- 賞金含む
        racebase = soup.select_one(".racebase")
        if racebase:
            race_data['race_base_info'] = racebase.get_text(strip=True)
        
        # 発走時刻
        time_elem = soup.select_one(".racetitle_sub .time, .starttime")
        if time_elem:
            race_data['start_time'] = time_elem.get_text(strip=True)

        # 出馬表
        horses = []
        shutuba_table = soup.select_one(".syutuba_sp tbody")
        if shutuba_table:
            for row in shutuba_table.find_all('tr'):
                horse_num_elem = row.select_one(".umaban")
                horse_name_elem = row.select_one(".kbamei a")
                jockey_elem = row.select_one(".kisyu a")
                
                if not (horse_num_elem and horse_name_elem):
                    continue
                
                horse_data = {}
                
                # 枠番
                waku_elem = row.select_one(".waku p")
                horse_data['waku'] = waku_elem.get_text(strip=True) if waku_elem else ""
                
                # 馬番
                horse_data['horse_num'] = horse_num_elem.get_text(strip=True)
                
                # 予想印 (tmyoso) - 総合印
                mark_elem = row.select_one(".tmyoso")
                if mark_elem:
                    # ★マークと数字印を両方取得
                    myuma_mark = mark_elem.select_one(".myumamark")
                    yoso_show = mark_elem.select_one(".js-yoso-show")
                    star_mark = myuma_mark.get_text(strip=True) if myuma_mark else ""
                    num_mark = yoso_show.get_text(strip=True) if yoso_show else ""
                    horse_data['prediction_mark'] = f"{star_mark}{num_mark}".strip()
                    
                    # 個別予想家印を取得（js-yoso-detail内）
                    yoso_detail = mark_elem.select_one(".js-yoso-detail, .yoso-detail")
                    if yoso_detail:
                        individual_marks = {}
                        mark_rows = yoso_detail.select("tr, li, .yoso-item")
                        for mrow in mark_rows:
                            name_elem = mrow.select_one("th, .yoso-name, .name")
                            mark_cell = mrow.select_one("td, .yoso-mark, .mark")
                            if name_elem and mark_cell:
                                predictor_name = name_elem.get_text(strip=True)
                                predictor_mark = mark_cell.get_text(strip=True)
                                if predictor_name and predictor_mark:
                                    individual_marks[predictor_name] = predictor_mark
                        horse_data['individual_marks'] = individual_marks
                    else:
                        horse_data['individual_marks'] = {}
                else:
                    horse_data['prediction_mark'] = ""
                    horse_data['individual_marks'] = {}
                
                # 馬名とリンク
                horse_data['horse_name'] = horse_name_elem.get_text(strip=True)
                horse_data['horse_name_link'] = horse_name_elem['href'] if horse_name_elem.has_attr('href') else ""
                
                # 騎手情報（年齢、騎手名、斤量が含まれる）
                kisyu_p = row.select_one(".kisyu")
                if kisyu_p:
                    kisyu_text = kisyu_p.get_text(separator=' ', strip=True)
                    # "牡7 藤本現 56" のような形式をパース
                    age_match = re.search(r'([牡牝セ騸])(\d+)', kisyu_text)
                    horse_data['sex'] = age_match.group(1) if age_match else ""
                    horse_data['age'] = age_match.group(2) if age_match else ""
                    
                    # 騎手名
                    horse_data['jockey'] = jockey_elem.get_text(strip=True) if jockey_elem else ""
                    
                    # 斤量: 数字のみ（2桁数字）
                    weight_match = re.search(r'\s(\d{2}(?:\.\d)?)\s*$', kisyu_text)
                    if not weight_match:
                        weight_match = re.search(r'(\d{2}(?:\.\d)?)', kisyu_text.split(horse_data['jockey'])[-1] if horse_data['jockey'] else "")
                    horse_data['weight'] = weight_match.group(1) if weight_match else ""
                else:
                    horse_data['jockey'] = jockey_elem.get_text(strip=True) if jockey_elem else ""
                    horse_data['sex'] = ""
                    horse_data['age'] = ""
                    horse_data['weight'] = ""
                
                # 短評/見解 (tanpyo)
                tanpyo_elem = row.select_one(".tanpyo")
                if tanpyo_elem:
                    horse_data['comment'] = tanpyo_elem.get_text(strip=True)
                else:
                    horse_data['comment'] = ""
                
                # オッズ・人気（最後のtdセル）
                all_tds = row.find_all('td')
                if all_tds:
                    last_td = all_tds[-1]
                    td_ps = last_td.find_all('p')
                    if len(td_ps) >= 2:
                        odds_text = td_ps[1].get_text(strip=True) if len(td_ps) > 1 else ""
                        pop_text = td_ps[2].get_text(strip=True) if len(td_ps) > 2 else ""
                        
                        odds_match = re.search(r'([\d.]+)', odds_text)
                        horse_data['odds'] = float(odds_match.group(1)) if odds_match else None
                        
                        pop_match = re.search(r'(\d+)', pop_text)
                        horse_data['popularity'] = int(pop_match.group(1)) if pop_match else None
                    else:
                        horse_data['odds'] = None
                        horse_data['popularity'] = None
                
                # 旧フィールド互換性
                horse_data['odds_text'] = f"{horse_data.get('odds', '')} {horse_data.get('popularity', '')}人気" if horse_data.get('odds') else ""
                
                horses.append(horse_data)
        
        race_data['horses'] = horses
        
        # 展開予想セクション
        boxsections = soup.select(".boxsection")
        for section in boxsections:
            title_elem = section.select_one(".title")
            if not title_elem:
                continue
            title = title_elem.get_text(strip=True)
            
            if title == "展開":
                # ペース
                pace_elem = section.select_one("p:not(.title)")
                if pace_elem and "ペース" in pace_elem.get_text():
                    race_data['pace'] = pace_elem.get_text(strip=True).replace("ペース", "").strip()
                
                # 隊列予想（逃げ/好位/中位/後方）
                formation = {}
                table = section.select_one("table")
                if table:
                    for row in table.find_all('tr'):
                        ths = row.find_all('th')
                        tds = row.find_all('td')
                        for i, th in enumerate(ths):
                            if i < len(tds):
                                position = th.get_text(strip=True)
                                horses_text = tds[i].get_text(strip=True)
                                formation[position] = horses_text
                race_data['formation'] = formation
                
                # 展開コメント（テーブルの後のp要素）
                all_ps = section.find_all('p')
                for p in all_ps:
                    text = p.get_text(strip=True)
                    if text and "ペース" not in text and len(text) > 30:
                        race_data['formation_comment'] = text
                        break
            else:
                # 展開以外のセクション（レース全体コメント）
                ps = section.find_all('p')
                for p in ps:
                    text = p.get_text(strip=True)
                    if text and len(text) > 50:  # 長めのテキストはコメント
                        if 'race_comment' not in race_data:
                            race_data['race_comment'] = text
                        break
        
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
            # 重要: pageを渡して、ログイン処理後も同じページを使い続ける（ページを閉じない）
            from src.utils.login import KeibaBookLogin
            cookie_file = self.settings.get('cookie_file', 'cookies.json')
            login_id = self.settings.get('login_id')
            password = self.settings.get('login_password')
            url = self.shutuba_url
            
            # pageを渡すことで、ensure_logged_in内でページが閉じられず、
            # ログイン状態が適用されたページをそのまま使える
            login_ok = await KeibaBookLogin.ensure_logged_in(
                context, login_id, password, 
                cookie_file=cookie_file, 
                save_cookies=True, 
                test_url=url,
                page=page  # ← これが重要！ページを渡して再利用
            )
            if not login_ok:
                logger.warning("ログインに失敗しました。無料範囲のデータのみ取得されます。")
            else:
                logger.info("ログイン確認成功。プレミアムデータを取得します。")
            
            # 重複チェック（DBマネージャーが設定されている場合）
            if not self.skip_duplicate_check and self.db_manager and self.db_manager.is_url_fetched(url):
                logger.info(f"スキップ（既取得）: {url}")
                # 既存データを返すか、空データを返すかは要件次第
                # ここでは空データを返す（差分取得が必要な場合は別途実装）
                return {}
            
            # レート制御: サイト負担を軽減
            await self.rate_limiter.wait()
            
            # ログイン後に出馬表URLに遷移してコンテンツを取得
            # 注: ensure_logged_in()で既にURLに遷移している場合があるが、
            # 確実性のため再度遷移する（Cookieが適用された状態で）
            current_url = page.url
            if url in current_url or current_url in url:
                # 既に対象ページにいる場合は、コンテンツのみ取得
                logger.debug(f"既に対象ページにいます: {current_url}")
                html_content = await page.content()
                self._last_fetches.append({
                    'requested_url': url,
                    'actual_url': current_url,
                    'status': 'cached',
                    'goto_ms': 0,
                    'content_ms': 0,
                    'total_ms': 0
                })
            else:
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
            
            # ===== 中央競馬専用ページの取得 =====
            if self.race_type == 'jra':
                # CPU予想ページを取得（最重要ページ：レーティング、スピード指数、印）
                if not self.settings.get('skip_cpu_prediction', False):
                    cpu_url = f"{base_url}/cpu/{self.settings['race_id']}"
                    
                    await self.rate_limiter.wait()
                    
                    if not (not self.skip_duplicate_check and self.db_manager and self.db_manager.is_url_fetched(cpu_url)):
                        try:
                            cpu_html = await self._fetch_page_content(page, cpu_url)
                            if self.db_manager:
                                self.db_manager.log_url(cpu_url, self.settings['race_id'], 'cpu_prediction', 'success')
                            if not self.settings.get('skip_debug_files', False):
                                with open(f"debug_cpu_{race_key}.html", "w", encoding="utf-8") as f:
                                    f.write(cpu_html)
                            
                            cpu_data = self.jra_parser.parse_cpu_prediction(cpu_html)
                            race_data['cpu_prediction'] = cpu_data
                            
                            # CPU予想データを各馬にマージ
                            cpu_horses_dict = {h.get('horse_num'): h for h in cpu_data.get('horses', [])}
                            for horse in race_data.get('horses', []):
                                horse_num = horse.get('horse_num')
                                if horse_num in cpu_horses_dict:
                                    cpu_horse = cpu_horses_dict[horse_num]
                                    horse['rating'] = cpu_horse.get('rating')
                                    horse['speed_index'] = cpu_horse.get('speed_index')
                                    horse['cpu_training_mark'] = cpu_horse.get('training_mark')
                                    horse['cpu_pedigree_mark'] = cpu_horse.get('pedigree_mark')
                                    horse['cpu_index'] = cpu_horse.get('cpu_index')
                            
                            logger.info(f"CPU予想取得成功: {len(cpu_data.get('horses', []))}頭")
                        except Exception as e:
                            logger.warning(f"CPU予想取得エラー: {e}")
                    else:
                        logger.info(f"スキップ（既取得）: {cpu_url}")
                
                # 重賞の場合、ギリギリ情報と特集ページを取得
                is_graded = any(g in race_data.get('race_grade', '') for g in ['GI', 'GII', 'GIII', 'G1', 'G2', 'G3', '重賞'])
                
                if is_graded and not self.settings.get('skip_special_pages', False):
                    # ギリギリ情報（直前情報）
                    girigiri_url = f"{base_url}/girigiri/{self.settings['race_id']}"
                    
                    await self.rate_limiter.wait()
                    
                    try:
                        girigiri_html = await self._fetch_page_content(page, girigiri_url)
                        if self.db_manager:
                            self.db_manager.log_url(girigiri_url, self.settings['race_id'], 'girigiri', 'success')
                        if not self.settings.get('skip_debug_files', False):
                            with open(f"debug_girigiri_{race_key}.html", "w", encoding="utf-8") as f:
                                f.write(girigiri_html)
                        
                        girigiri_data = self.jra_parser.parse_girigiri_info(girigiri_html)
                        race_data['girigiri_info'] = girigiri_data
                        logger.info(f"ギリギリ情報取得成功")
                    except Exception as e:
                        logger.warning(f"ギリギリ情報取得エラー（重賞以外は正常）: {e}")
                    
                    # 特集ページ
                    feature_url = f"{base_url}/tokusyu/{self.settings['race_id']}"
                    
                    await self.rate_limiter.wait()
                    
                    try:
                        feature_html = await self._fetch_page_content(page, feature_url)
                        if self.db_manager:
                            self.db_manager.log_url(feature_url, self.settings['race_id'], 'feature', 'success')
                        if not self.settings.get('skip_debug_files', False):
                            with open(f"debug_feature_{race_key}.html", "w", encoding="utf-8") as f:
                                f.write(feature_html)
                        
                        feature_data = self.jra_parser.parse_special_feature(feature_html)
                        race_data['special_feature'] = feature_data
                        logger.info(f"特集ページ取得成功: {feature_data.get('title', '')}")
                    except Exception as e:
                        logger.warning(f"特集ページ取得エラー（重賞以外は正常）: {e}")
                
                # AI指数は出馬表ページから既に取得済み（parse_race_dataで処理）
            
            # ===== 地方競馬専用ページの取得 =====
            if self.race_type == 'nar':
                # ポイントページを取得
                point_data = await self._scrape_point_page(page, base_url)
                if point_data:
                    race_data['point_info'] = point_data
                
                # 個別馬のコメントを取得（穴馬のヒント）
                # Keep sequential by default (comments_concurrency defaults to 1)
                await self._scrape_horse_comments(page, race_data.get('horses', []), base_url)
            
            # ===== レース結果ページの取得（レース終了後のみ） =====
            if self.settings.get('fetch_result', False) and self.seiseki_url:
                result_url = self.seiseki_url
                if not result_url:
                    # 結果ページURLを構築
                    result_url = f"{base_url}/seiseki/{self.settings['race_id']}"
                
                await self.rate_limiter.wait()
                
                try:
                    result_html = await self._fetch_page_content(page, result_url)
                    if self.db_manager:
                        self.db_manager.log_url(result_url, self.settings['race_id'], 'result', 'success')
                    if not self.settings.get('skip_debug_files', False):
                        with open(f"debug_result_{race_key}.html", "w", encoding="utf-8") as f:
                            f.write(result_html)
                    
                    result_data = self.result_parser.parse_result_page(result_html)
                    race_data['result'] = result_data
                    
                    # ラップタイム（トラックバイアス分析用）
                    race_data['lap_times'] = result_data.get('lap_times', [])
                    race_data['corner_positions'] = result_data.get('corner_positions', {})
                    race_data['payouts'] = result_data.get('payouts', {})
                    race_data['race_review'] = result_data.get('race_comment', '')
                    
                    # 結果データを各馬にマージ
                    result_horses_dict = {h.get('horse_num'): h for h in result_data.get('horses', [])}
                    for horse in race_data.get('horses', []):
                        horse_num = horse.get('horse_num')
                        if horse_num in result_horses_dict:
                            rh = result_horses_dict[horse_num]
                            horse['result_rank'] = rh.get('rank')
                            horse['result_rank_num'] = rh.get('rank_num')
                            horse['result_time'] = rh.get('time')
                            horse['result_margin'] = rh.get('margin')
                            horse['result_passing'] = rh.get('passing')
                            horse['result_last_3f'] = rh.get('last_3f')
                            horse['result_comment'] = rh.get('race_comment', '')
                            horse['next_race_memo'] = rh.get('next_race_memo', '')
                    
                    logger.info(f"レース結果取得成功: {len(result_data.get('horses', []))}頭")
                except Exception as e:
                    logger.warning(f"レース結果取得エラー（レース未終了の場合は正常）: {e}")

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