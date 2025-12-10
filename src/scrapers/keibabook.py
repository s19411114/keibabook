import os
import json
import time
import asyncio
from pathlib import Path
from src.utils.config import load_settings
from src.utils.logger import get_logger
from src.utils.rate_limiter import RateLimiter
from src.scrapers.result_parser import ResultPageParser
from src.scrapers.local_racing_parser import LocalRacingParser
from src.scrapers.jra_special_parser import JRASpecialParser
from src.scrapers.fetcher import fetch_page_content
from src.scrapers.comment_aggregator import aggregate_individual_comments
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

"""
keibabook.py - KeibaBook スクレイパー

このモジュールは KeibaBook のスクレイピングを担う主要クラスを定義します。
実装上の注意点（将来のメンテ用）:
- `KeibaBookScraper.scrape()` が長くネストが深いのは、ログイン/重複チェック/レート制御/取得/パース/マージ
    の各フェーズが順次実行されるためです。各フェーズは個別に失敗する可能性がある
    ため try/except や分岐が多く、結果としてインデントが深くなっています。
- 将来的な保守性向上のため、主要フェーズ（fetch, parse, aggregate）を小さな関数
    に分割し、内部の try/except を減らすことを推奨します（既に一部分割済み）。
- 注意: 「特集ページ」は2種類あります: ① レース個別の特集（race-level feature）と
    ② 当日ベースの特集/一覧（daily feature）。当日ベースの特集は全レースに必ず
    存在するわけではないため、取得は設定 `fetch_daily_special_pages` を有効化した場合のみ
    試行するようになっています（デフォルトは無効）。
"""

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
        # Ensure debug dir exists
        self.debug_dir = Path("debug_files")
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        self._comments_concurrency = int(self.settings.get('comments_concurrency', 1))
        self._parallel_page_fetch = bool(self.settings.get('parallel_page_fetch', False))
        # Skip opening individual horse pages by default (safety and site load)
        self.skip_individual_pages = bool(self.settings.get('skip_individual_pages', True))
        # 重複チェックを行う場合の TTL（秒）。0 又は未設定で無効（常に skip 判定）
        self.duplicate_check_ttl = int(self.settings.get('duplicate_check_ttl_seconds', 0) or 0)
        
        # 競馬種別に応じたベースURL設定
        if self.race_type == 'nar':
            # 地方競馬の場合のURLパターン（実際のURL構造に応じて調整が必要）
            self.base_url_pattern = "https://s.keibabook.co.jp/chihou"
        else:
            # 中央競馬の場合
            self.base_url_pattern = "https://s.keibabook.co.jp/cyuou"
        # Base URL derived from provided shutuba_url (used across many fetches)
        if self.shutuba_url:
            try:
                self.base_url = '/'.join(self.shutuba_url.split('/')[:4])
            except Exception as e:
                logger.debug(f"base_urlの計算に失敗しました: {e}")
                self.base_url = ''
        else:
            self.base_url = ''
        # Course jockey stats fetching (course data page) - default True for JRA
        self.fetch_course_jockey_stats = bool(self.settings.get('fetch_course_jockey_stats', True))
        # Fetch girigiri/paddock/直前 info (default: False) — do not fetch unless explicitly enabled
        self.fetch_girigiri = bool(self.settings.get('fetch_girigiri', False))
        # TM (トラックマン直前情報) is not fetched by default and currently unimplemented.
        # The previous setting `fetch_tm` has been removed to avoid confusion.
        # Special pages: optionally limit heavy fetches by grade (e.g., 'GI,G1')
        self.special_fetch_grades = self.settings.get('special_fetch_grades', '')

    def _get_race_number(self):
        """Return race number if available in settings (race_num, race_key, race_id)."""
        try:
            rn = self.settings.get('race_num')
            if rn:
                return int(rn)
        except Exception:
            pass
        rid = self.settings.get('race_id', '')
        # coercively convert to string to avoid TypeError when an int is stored in settings
        rid_str = str(rid) if rid is not None else ''
        if rid_str and len(rid_str) >= 2 and rid_str[-2:].isdigit():
            try:
                return int(rid_str[-2:])
            except Exception:
                pass
        rk = self.settings.get('race_key', '') or ''
        import re
        m = re.search(r'(\d{1,2})R$', rk or '')
        if m:
            try:
                return int(m.group(1))
            except Exception:
                pass
        return None

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
        # Delegate to centralized fetcher
        return await fetch_page_content(page, url, self.settings, rate_limiter=self.rate_limiter, last_fetches=self._last_fetches, retry_count=retry_count, retry_delay=retry_delay, wait_until=wait_until)

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

    def _should_skip_due_to_dup(self, url):
        """
        重複チェック（db_manager による）を判定するヘルパ。
        設定 `skip_duplicate_check` が True の場合は常に False を返す。
        """
        try:
            if self.skip_duplicate_check:
                return False
            if not self.db_manager:
                return False
            # TTL が 0 の場合は従来通り URL の存在で判定
            if self.duplicate_check_ttl and self.duplicate_check_ttl > 0:
                return bool(self.db_manager.is_url_fetched(url, max_age_seconds=self.duplicate_check_ttl))
            else:
                return bool(self.db_manager.is_url_fetched(url))
        except Exception as e:
            # 判定に失敗してもフェールセーフとして再取得を許す
            logger.debug(f"重複チェック判定エラー（再取得許可）: {e}")
            return False

    def _log_url(self, url, tag, status='success'):
        """
        db_manager にログを残すユーティリティ（安全に実行）。
        """
        try:
            if self.db_manager:
                self.db_manager.log_url(url, self.settings.get('race_id'), tag, status)
        except Exception as e:
            logger.debug(f"URL記録エラー（無視）: {e}")

    def _parse_training_simple(self, training_table):
        """
        シンプルな調教テーブルをパース（TrainingTableパターン）
        
        構造:
        <tr>
            <td class="HorseNum">1</td>
            <td class="TrainingDate">11/5</td>
            <td class="TrainingLocation">美浦南Ｗ</td>
            <td class="TrainingTime">68.9-53.5-38.6-11.9</td>
            <td class="TrainingEvaluation">馬ナリ余力</td>
        </tr>
        """
        from src.utils.training_converter import convert_training_data
        
        training_data = {}
        
        for row in training_table.find_all('tr'):
            horse_num_elem = row.select_one("td.HorseNum")
            if not horse_num_elem:
                continue
            
            horse_num = horse_num_elem.get_text(strip=True)
            date_elem = row.select_one("td.TrainingDate")
            location_elem = row.select_one("td.TrainingLocation")
            time_elem = row.select_one("td.TrainingTime")
            evaluation_elem = row.select_one("td.TrainingEvaluation")
            
            date = date_elem.get_text(strip=True) if date_elem else ''
            location = location_elem.get_text(strip=True) if location_elem else ''
            times_str = time_elem.get_text(strip=True) if time_elem else ''
            evaluation = evaluation_elem.get_text(strip=True) if evaluation_elem else ''
            
            # タイムを分割（例: "68.9-53.5-38.6-11.9" → ["68.9", "53.5", "38.6", "11.9"]）
            times = times_str.split('-') if times_str else []
            # ラスト4ハロン分を取得（通常は4つ）
            times = [t for t in times if t and t != '-']
            
            if horse_num not in training_data:
                training_data[horse_num] = {
                    'horse_name': '',  # シンプル版では馬名なし
                    'tanpyo': '',
                    'details': []
                }
            
            # 調教詳細を追加
            detail = {
                'date_location': f"{date} {location}",
                '追い切り方': evaluation,
                'times': times,
                'positions': [''] * len(times),  # シンプル版では位置情報なし
                'awase': '',
                'comment': ''
            }
            
            training_data[horse_num]['details'].append(detail)
        
        logger.info(f"シンプルパターンで{len(training_data)}頭の調教データを取得")
        
        # 調教タイム変換を適用
        training_data = convert_training_data(training_data)
        
        return training_data
    
    def _parse_training_data(self, html_content):
        """
        調教データをパース（強化版 + タイム変換）
        
        取得データ:
        - 馬番、馬名、短評（調教全体の評価コメント）
        - 調教詳細（最大4回分）:
          - 日付・場所（例: "11/28 栗東C"）
          - 追い切り方（例: "強め", "一杯に追う"）
          - 4回分のタイム（例: ["13.0", "12.8", "12.5", "12.3"]）
          - 変換後タイム（栗東・美浦の差を補正した共通タイム）
          - 枠位置[n]（中心からの距離）
          - 併せ馬情報
          - コメント
        
        Returns:
            調教データ辞書（馬番がキー）
        """
        from src.utils.training_converter import convert_training_data
        
        soup = BeautifulSoup(html_content, 'html.parser')
        training_data = {}

        # KeibaBookの調教テーブルを探す（複数のパターンに対応）
        training_table = soup.select_one("table.TrainingTable tbody")
        
        # TrainingTableパターン（シンプル版）
        if training_table:
            logger.info("TrainingTableパターンで調教データをパース")
            return self._parse_training_simple(training_table)
        
        # 従来のパターン（詳細版）
        training_table = soup.select_one("table.default.cyokyo tbody")
        if not training_table:
            training_table = soup.select_one("table.cyokyo tbody")
        
        if not training_table:
            logger.warning("調教テーブルが見つかりません（TrainingTable/default.cyokyo/cyokyo）")
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
                        current_detail['positions'] = []  # 枠位置[n]を格納
                        current_detail['awase'] = ''
                        current_detail['comment'] = ''  # コメントを格納

                    elif elem.name == 'table' and 'cyokyodata' in elem.get('class', []):
                        if current_detail:
                            # タイム行を取得
                            time_row = elem.select_one("tr.time")
                            if time_row:
                                time_tds = time_row.find_all('td')
                                for td in time_tds:
                                    text = td.get_text(strip=True)
                                    if text and text != '-':
                                        # タイムと枠位置を分離（例: "12.5[3]" → "12.5", "[3]"）
                                        import re
                                        match = re.match(r'([\d.:]+)(\[[\d\-]+\])?', text)
                                        if match:
                                            time_val = match.group(1)
                                            position_val = match.group(2) if match.group(2) else ''
                                            current_detail['times'].append(time_val)
                                            current_detail['positions'].append(position_val)
                                        else:
                                            current_detail['times'].append(text)
                                            current_detail['positions'].append('')
                            
                            # 併せ馬情報
                            awase_row = elem.select_one("tr.awase td.left")
                            if awase_row:
                                current_detail['awase'] = awase_row.get_text(strip=True)
                            
                            # コメント行（次のp要素またはdiv要素を探す）
                            comment_elem = elem.find_next_sibling(['p', 'div'])
                            if comment_elem and comment_elem.get('class'):
                                # コメント用のクラス名を探す（例: "comment", "cyokyo_comment"）
                                if any(cls in ['comment', 'cyokyo_comment', 'cyoukyo_comment'] for cls in comment_elem.get('class', [])):
                                    current_detail['comment'] = comment_elem.get_text(strip=True)
                
                if current_detail:
                    training_data[current_horse_num]['details'].append(current_detail)
                
                i += 1
            else:
                i += 1
        
        # 調教タイム変換を適用（栗東・美浦の差を補正）
        training_data = convert_training_data(training_data)
        
        return training_data

    async def _ensure_authenticated(self, context, page):
        """
        Ensure Playwright page is authenticated using KeibaBookAuth.
        Returns (login_ok, page) and leaves page pointing at target.
        """
        from src.utils.keibabook_auth import KeibaBookAuth
        cookie_file = self.settings.get('cookie_file', 'cookies.json')
        login_id = self.settings.get('login_id')
        password = self.settings.get('login_password')
        url = self.shutuba_url
        try:
            login_ok, page = await KeibaBookAuth.ensure_authenticated(
                context=context,
                page=page,
                login_id=login_id,
                password=password,
                cookie_file=cookie_file,
                target_url=url
            )
            return login_ok, page
        except Exception as e:
            logger.debug(f"_ensure_authenticated エラー: {e}")
            return False, page

    async def _fetch_and_parse_training(self, page, race_key):
        """
        Fetch training page and parse; returns parsed_training_data or {}.
        """
        base_url = self.base_url
        training_url = f"{base_url}/cyokyo/0/{self.settings['race_id']}"
        if not training_url or self.settings.get('skip_training', False):
            return {}
        await self.rate_limiter.wait()
        if not self._should_skip_due_to_dup(training_url):
            training_html_content = await self._fetch_page_content(page, training_url)
            self._log_url(training_url, 'training', 'success')
            if not self.settings.get('skip_debug_files', False):
                with open(self.debug_dir / f"debug_training_{race_key}.html", "w", encoding='utf-8') as f:
                    f.write(training_html_content)
        else:
            logger.info(f"スキップ（既取得）: {training_url}")
            training_html_content = ""
        parsed_training_data = self._parse_training_data(training_html_content) if training_html_content else {}
        if parsed_training_data:
            from src.utils.training_converter import convert_training_data
            parsed_training_data = convert_training_data(parsed_training_data)
            logger.info(f"調教タイム換算完了: {len(parsed_training_data)}頭分")
        else:
            parsed_training_data = {}
            logger.info("調教データをスキップまたは未検出")
        return parsed_training_data

    async def _fetch_generic_page_and_parse(self, page, page_url, debug_name, parser_func=None, tag_name=None, skip_flag=False):
        """
        Generic fetch-and-parse helper for pages like pedigree, stable_comment, previous_race_comment.
        `parser_func` should be a function that takes HTML and returns parsed data.
        """
        if not page_url or skip_flag:
            return {} if parser_func else []
        await self.rate_limiter.wait()
        if not self._should_skip_due_to_dup(page_url):
            content = await self._fetch_page_content(page, page_url)
            if tag_name:
                self._log_url(page_url, tag_name, 'success')
            if not self.settings.get('skip_debug_files', False):
                with open(self.debug_dir / f"debug_{debug_name}_{self.settings.get('race_key','unknown')}.html", 'w', encoding='utf-8') as f:
                    f.write(content)
        else:
            logger.info(f"スキップ（既取得）: {page_url}")
            content = ""
        if content and parser_func:
            try:
                return parser_func(content)
            except Exception as e:
                logger.debug(f"parser_func 例外: {e}")
                return {} if isinstance({}, type({})) else []
        return {} if parser_func else []

    async def _fetch_cpu_prediction(self, page, race_key):
        """
        Fetch CPU prediction and parse with JRA parser; returns cpu_data or {}.
        """
        if self.settings.get('skip_cpu_prediction', False):
            return {}
        base_url = self.base_url
        cpu_url = f"{base_url}/cpu/{self.settings['race_id']}"
        await self.rate_limiter.wait()
        if not self._should_skip_due_to_dup(cpu_url):
            try:
                cpu_html = await self._fetch_page_content(page, cpu_url)
                self._log_url(cpu_url, 'cpu_prediction', 'success')
                if not self.settings.get('skip_debug_files', False):
                    with open(self.debug_dir / f"debug_cpu_{race_key}.html", "w", encoding='utf-8') as f:
                        f.write(cpu_html)
                cpu_data = self.jra_parser.parse_cpu_prediction(cpu_html)
                return cpu_data
            except Exception as e:
                logger.debug(f"CPU予想取得エラー: {e}")
                return {}
        else:
            logger.info(f"スキップ（既取得）: {cpu_url}")
            return {}

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

    # NOTE: 馬の過去走データ（馬柱/成績表）取得機能は運用方針により削除されました。
    # 以前は _parse_horse_past_results_data()/ _parse_horse_table_data() が出馬表HTML
    # や個別馬ページの能力表から過去成績を抽出していましたが、現在は不要であるため
    # 削除済みです（2025-12-10）。
    
    # (functionality removed)
    
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
            if self._should_skip_due_to_dup(self.seiseki_url):
                logger.info(f"スキップ（既取得）: {self.seiseki_url}")
                return None
            
            # 結果ページを取得
            result_html_content = await self._fetch_page_content(page, self.seiseki_url)
            
            # URL取得をログに記録
            self._log_url(self.seiseki_url, 'result', 'success')
            
            # デバッグ用にHTMLを保存
            with open(self.debug_dir / "debug_result.html", "w", encoding="utf-8") as f:
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
        # Only fetch local point pages for late-card races (11,12) where they exist
        race_num = self._get_race_number()
        if race_num not in (11, 12):
            logger.info(f"スキップ（ポイントページ対象外のレース番号: {race_num}）")
            return None
        
        try:
            # ポイントページのURL（実際のURL構造に応じて調整が必要）
            point_url = f"{base_url}/point/{self.settings['race_id']}"
            
            # 重複チェック
            if self._should_skip_due_to_dup(point_url):
                logger.info(f"スキップ（既取得）: {point_url}")
                return None
            
            # レート制御
            await self.rate_limiter.wait()
            
            # ポイントページを取得
            point_html_content = await self._fetch_page_content(page, point_url)
            
            # URL取得をログに記録
            self._log_url(point_url, 'point', 'success')
            
            # デバッグ用にHTMLを保存
            with open(self.debug_dir / "debug_point.html", "w", encoding="utf-8") as f:
                f.write(point_html_content)
            
            # ポイントページをパース
            point_data = self.local_parser.parse_point_page(point_html_content)
            
            logger.info(f"ポイント情報取得成功: {len(point_data.get('big_upset_horses', []))}頭の大穴情報など")
            return point_data
            
        except Exception as e:
            logger.error(f"ポイントページ取得エラー: {e}")
            return None

    async def _fetch_special_pages(self, page, base_url, race_key, race_grade=None):
        """
        重賞用のギリギリ・特集ページを取得してパースするヘルパ。
        この処理は非常に重くなり得るため、独立した関数で明示的に呼び出す。
        Args:
            race_grade: optional grade string (e.g. 'GI' or 'GIII') to control fetching by grade

        Return: dict with possible keys 'girigiri_info', 'special_feature' and 'daily_feature'
        """
        special_data = {}
        # Collect all extracted labels to allow top-level processing
        special_data['labels'] = {}
        # Respect settings to limit special page fetches by grade (comma-separated or list)
        special_grades_setting = self.settings.get('special_fetch_grades', '')
        if isinstance(special_grades_setting, str):
            allowed_grades = [g.strip() for g in special_grades_setting.split(',') if g.strip()]
        elif isinstance(special_grades_setting, (list, tuple)):
            allowed_grades = [g.strip() for g in special_grades_setting]
        else:
            allowed_grades = []

        if allowed_grades and race_grade:
            # Normalise common grade tokens (G1/GI etc.) for comparison
            rg = race_grade.upper().replace(' ', '')
            allowed = any((rg == g.upper().replace(' ', '')) or (g.upper().replace(' ', '') in rg) for g in allowed_grades)
            if not allowed:
                logger.info(f"特集ページ取得をスキップ（グレード除外）: {race_grade}")
                return special_data
        try:
            # ギリギリ情報（直前情報）は運用方針により現在取得対象外です。
            # (fetch_girigiri 設定は存在しますが、デフォルトでは False です)

            # 特集ページ（レース個別: 現行の取り方）
            feature_url = f"{base_url}/tokusyu/{self.settings['race_id']}"
            await self.rate_limiter.wait()
            if not self._should_skip_due_to_dup(feature_url):
                try:
                    # Skip fetching pages that are clearly registry pages (新規登録/特別登録)
                    if 'tourokuba' in feature_url or 'touroku' in feature_url or 'tourok' in feature_url or '登録' in feature_url:
                        logger.info(f"スキップ（登録ページ）: {feature_url}")
                        feature_html = ''
                    else:
                        feature_html = await self._fetch_page_content(page, feature_url)
                    self._log_url(feature_url, 'feature', 'success')
                    if not self.settings.get('skip_debug_files', False):
                        with open(self.debug_dir / f"debug_feature_{race_key}.html", "w", encoding="utf-8") as f:
                            f.write(feature_html)
                    feature_data = self.jra_parser.parse_special_feature(feature_html)
                    special_data['special_feature'] = feature_data
                    # Merge any labels from feature into the cumulative label map
                    if feature_data.get('labels'):
                        special_data['labels'].update(feature_data.get('labels', {}))
                    logger.info(f"特集ページ取得成功: {feature_data.get('title', '')}")
                except Exception as e:
                    logger.warning(f"特集ページ取得エラー（重賞以外は正常）: {e}")
            else:
                logger.info(f"スキップ（既取得）: {feature_url}")

            # ===== 日付ベースの特集ページ（その日の特集ページ/一覧）をオプションで取得 =====
            # 設定 `fetch_daily_special_pages` が True の場合、以下の候補URLを順に試行します:
            #  - {base_url}/tokusyu                      (一覧/日別のトップ)
            #  - {base_url}/tokusyu/{race_key}           (日別/キーが使える場合)
            #  - {base_url}/tokusyu/{race_date}         (設定で日付が明示されている場合)
            if bool(self.settings.get('fetch_daily_special_pages', False)):
                # Build a candidate list
                candidates = [f"{base_url}/tokusyu"]
                race_key_candidate = race_key or self.settings.get('race_key')
                race_date = self.settings.get('race_date')
                if race_key_candidate:
                    candidates.append(f"{base_url}/tokusyu/{race_key_candidate}")
                if race_date:
                    candidates.append(f"{base_url}/tokusyu/{race_date}")

                for idx, day_url in enumerate(candidates):
                    try:
                        await self.rate_limiter.wait()
                        if self._should_skip_due_to_dup(day_url):
                            logger.info(f"スキップ（既取得）: {day_url}")
                            continue
                        try:
                            day_html = await self._fetch_page_content(page, day_url)
                            self._log_url(day_url, 'daily_feature', 'success')
                            if not self.settings.get('skip_debug_files', False):
                                # Save each candidate's debug content with incremental suffix
                                with open(self.debug_dir / f"debug_daily_feature_{race_key}_{idx}.html", "w", encoding="utf-8") as f:
                                    f.write(day_html)
                            # Try parsing using existing special feature parser
                            # Skip registration pages and similar non-feature pages by URL
                            if 'tourokuba' in day_url or 'touroku' in day_url or '登録' in day_url:
                                logger.info(f"スキップ（登録ページ）: {day_url}")
                                continue
                            day_feature_data = self.jra_parser.parse_special_feature(day_html)
                            # merge or append to special_data.daily_feature list
                            if 'daily_feature' not in special_data:
                                special_data['daily_feature'] = []
                            special_data['daily_feature'].append({
                                'url': day_url,
                                'data': day_feature_data
                            })
                            # Merge labels
                            if isinstance(day_feature_data, dict) and day_feature_data.get('labels'):
                                special_data['labels'].update(day_feature_data.get('labels', {}))
                            logger.info(f"日別特集ページ取得成功: {day_url}")
                        except Exception as e:
                            logger.warning(f"日別特集ページ取得エラー: {day_url}: {e}")
                    except Exception as e:
                        # Rate limiter or other transient error; continue to next candidate
                        logger.debug(f"日別特集試行中に一時エラー、次の候補へ: {day_url}: {e}")
        except Exception as e:
            logger.warning(f"特集ページ全体の取得処理でエラーが発生しました: {e}")
        return special_data

    async def _fetch_course_data_and_parse_jockey_stats(self, page, base_url, race_key):
        """
        Fetch course data page and parse jockey stats. Returns dict mapping jockey -> stats.
        """
        if not base_url or not self.fetch_course_jockey_stats:
            return {}
        course_url = f"{base_url}/data/{self.settings.get('race_id')}"
        if self._should_skip_due_to_dup(course_url):
            logger.info(f"スキップ（既取得）: {course_url}")
            return {}
        try:
            await self.rate_limiter.wait()
            course_html = await self._fetch_page_content(page, course_url)
            self._log_url(course_url, 'course', 'success')
            if not self.settings.get('skip_debug_files', False):
                with open(self.debug_dir / f"debug_course_{race_key}.html", "w", encoding="utf-8") as f:
                    f.write(course_html)
            # Parse using jra parser
            course_stats = self.jra_parser.parse_course_jockey_stats(course_html)
            return course_stats
        except Exception as e:
            logger.warning(f"コースデータ取得エラー: {e}")
            return {}

    def _aggregate_individual_comments(self, horses, stable_comment_data, previous_race_comment_data, training_data, point_data=None):
        """
        出馬表/調教/厩舎/前走/ポイントページから取得したコメントやヒントを
        結合して `individual_comment` に格納する。個別馬ページを開いて取得する方法は使わない。

        Args:
            horses: list of horse dicts
            stable_comment_data: dict 馬番 -> 厩舎のコメント
            previous_race_comment_data: dict 馬番 -> 前走コメント
            training_data: dict 馬番 -> 調教データ（details[]内のコメントを結合）
            point_data: dict ポイントページのデータ（地方競馬向けのヒントなど）
        """
        # Delegate aggregation to the central aggregator module
        tag_sources = bool(self.settings.get('tag_comment_sources', False))
        aggregate_individual_comments(horses, stable_comment_data or {}, previous_race_comment_data or {}, training_data or {}, point_data or {}, tag_sources=tag_sources)

    async def scrape(self, context=None, page=None, force: bool = False):
        """
        メインのスクレイプ制御（オーケストレーション）

        Args:
            context: optional Playwright context
            page: optional Playwright page
            force: if True, bypasses race TTL skip even if the race was recently fetched

        役割（順序は重視）:
        1. ログイン確認（KeibaBook は一部データがログイン時にのみ取得可能）
        2. 重複チェック（DB ログに基づきページ取得をスキップ）
        3. 出馬表ページ取得・パース
        4. 関連ページ（調教/血統/厩舎/前走等）を必要に応じて取得しパース
        5. 個別馬のコメント集約 & CPU 予想や結果のマージ
        6. 結果の保存とデバッグ情報の出力

        なぜインデントが深いか:
        - 各ステップでスキップ条件（race_type, skip_* フラグ, dup check など）や
            レート制御が異なるため、処理の順序を崩せない組み合わせが多く、
            条件分岐と try/except のネストが増えています。
        - 将来的には `fetch_and_parse_shutuba()`, `fetch_training()`, `fetch_pedigree()` 等の
            小さなヘルパに切り出すことでインデントは浅くなり、可読性とテスト性が向上します。
        """
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
        
        # NOTE: This `scrape` method is intentionally structured as a linear orchestrator
        # for several dependent scraping steps. Each step depends on the previous one's
        # outcome (e.g., login -> duplicate check -> fetch shutuba -> parse -> fetch
        # dependent pages like training/pedigree -> aggregate -> optionally fetch
        # CPU/special/result pages). The nesting/indentation grows because of many
        # conditional guards (race type checks, skip flags, duplicate checks, rate limiting)
        # that must execute in order to preserve site-friendly behavior and correct
        # merging logic.
        #
        # Guiding refactor notes for maintainers:
        # - Keep the order of operations; it is important for correct dedupe, rate
        #   limiting, and for avoiding unnecessary page loads.
        # - Prefer extracting small helper methods (login(), fetch_and_parse_shutuba(),
        #   fetch_training(), fetch_pedigree(), merge_cpu_predictions(), aggregate_comments())
        #   rather than flattening this function in one pass. See `src/scrapers/fetcher.py`
        #   and `src/scrapers/comment_aggregator.py` for examples of delegated responsibilities.
        # - Routing decisions are primarily based on `self.race_type` and the `skip_*`
        #   configuration flags; keep the skip flag checks to avoid regressions.
        # - For any change that removes or reorders steps, add tests that confirm
        #   dedupe and rate-limit semantics are preserved, and that `cpu_prediction` and
        #   `result` fields are merged correctly into horse objects.
        try:
            perf_enabled = self.settings.get('perf', False)
            if perf_enabled:
                overall_start = time.perf_counter()
            # タイムアウト設定（任意）
            timeout_ms = self.settings.get("playwright_timeout")
            if timeout_ms:
                page.set_default_timeout(timeout_ms)

            # ================================================================================
            # ⚠️ 重要: ログイン処理 - このセクションを削除しないでください
            # ================================================================================
            # Delegate to helper
            login_ok, page = await self._ensure_authenticated(context, page)
            url = self.shutuba_url
            if not login_ok:
                logger.warning("⚠️ ログインに失敗しました。無料範囲（3頭まで）のデータのみ取得されます。")
            else:
                logger.info("✅ ログイン確認成功。全頭のプレミアムデータを取得します。")
            # ================================================================================
            
            # 重複チェック（DBマネージャーが設定されている場合）
            if self._should_skip_due_to_dup(url):
                logger.info(f"スキップ（既取得）: {url}")
                return {}

            # レース単位の取得済みスキップ（TTL指定）
            race_ttl = int(self.settings.get('skip_race_if_fetched_within_seconds', 0) or 0)
            force_effective = bool(force or self.settings.get('force_recheck_on_scrape', False))
            if self.db_manager and race_ttl > 0 and not force_effective and self.db_manager.is_race_fetched(self.settings.get('race_id'), max_age_seconds=race_ttl):
                logger.info(f"スキップ（レース取得済み、TTL内）: {self.settings.get('race_id')}")
                return {}
            
            # レート制御: サイト負担を軽減
            await self.rate_limiter.wait()
            
            # 現在のページURLを確認し、必要なら出馬表URLに遷移（ミニマル実装）
            current_url = page.url
            if url in current_url or current_url in url:
                logger.debug(f"既に対象ページにいます: {current_url}")
                html_content = await page.content()
            else:
                html_content = await self._fetch_page_content(page, url)
            
            # URL取得をログに記録
            self._log_url(url, 'shutuba', 'success')
            
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
            except Exception as e:
                logger.debug(f"html_content 文字列変換中に例外: {e}")
                html_text = str(html_content)
            race_key = self.settings.get('race_key', 'unknown')
            if not self.settings.get('skip_debug_files', False):
                with open(self.debug_dir / f"debug_page_{race_key}.html", "w", encoding="utf-8") as f:
                    f.write(html_text)
            # ------------------------------------

            race_data = self._parse_race_data(html_content)

            # 地方競馬の場合は最小限のデータのみ取得（馬柱、出馬表、血統）
            # 中央競馬の場合は全データを取得
            
            # 調教データの取得/マージ
            parsed_training_data = await self._fetch_and_parse_training(page, race_key)

            for horse in race_data.get('horses', []):
                horse_num = horse.get('horse_num')
                if horse_num in parsed_training_data:
                    horse['training_data'] = parsed_training_data[horse_num]
                else:
                    horse['training_data'] = {}

            # 血統データの取得/マージ
            base_url = self.base_url
            pedigree_url = f"{base_url}/kettou/{self.settings['race_id']}"
            parsed_pedigree_data = await self._fetch_generic_page_and_parse(
                page, pedigree_url, 'pedigree', parser_func=self._parse_pedigree_data, tag_name='pedigree', skip_flag=self.settings.get('skip_pedigree', False)
            )

            # 血統データをインデックスでマッチング（血統ページには馬番がないため）
            horses = race_data.get('horses', [])
            for idx, horse in enumerate(horses):
                if idx < len(parsed_pedigree_data):
                    horse['pedigree_data'] = parsed_pedigree_data[idx]
                else:
                    horse['pedigree_data'] = {}

            # 厩舎の話データの取得/マージ（地方競馬はスキップ）
            if self.race_type != 'nar' and not self.settings.get('skip_stable_comment', False):
                stable_comment_url = f"{base_url}/danwa/0/{self.settings['race_id']}"
                parsed_stable_comment_data = await self._fetch_generic_page_and_parse(
                    page, stable_comment_url, 'stable_comment', parser_func=self._parse_stable_comment_data, tag_name='stable_comment', skip_flag=self.settings.get('skip_stable_comment', False)
                )
            else:
                parsed_stable_comment_data = {}
                logger.info("地方競馬のため厩舎コメントをスキップ")

            for horse in race_data.get('horses', []):
                horse_num = horse.get('horse_num')
                if horse_num in parsed_stable_comment_data:
                    horse['stable_comment'] = parsed_stable_comment_data[horse_num]
                else:
                    horse['stable_comment'] = ""

            # 前走コメントデータの取得/マージ（地方競馬はスキップ）
            if self.race_type != 'nar' and not self.settings.get('skip_previous_race_comment', False):
                previous_race_comment_url = f"{base_url}/syoin/{self.settings['race_id']}"
                parsed_previous_race_comment_data = await self._fetch_generic_page_and_parse(
                    page, previous_race_comment_url, 'previous_race_comment', parser_func=self._parse_previous_race_comment_data, tag_name='previous_race_comment', skip_flag=self.settings.get('skip_previous_race_comment', False)
                )
            else:
                parsed_previous_race_comment_data = {}
                logger.info("地方競馬のため前走コメントをスキップ")

            for horse in race_data.get('horses', []):
                horse_num = horse.get('horse_num')
                if horse_num in parsed_previous_race_comment_data:
                    horse['previous_race_comment'] = parsed_previous_race_comment_data[horse_num]
                else:
                    horse['previous_race_comment'] = ""

            # 馬柱データ（出馬表ページから）は運用方針により取得しません
            # (skip_past_results デフォルト true)。過去走データはJSON/DBに含めない設計です。
            horse_table_data = {}
            for horse in race_data.get('horses', []):
                # Past results are intentionally omitted per operational policy
                horse['past_results'] = []
            
            # ===== 中央競馬専用ページの取得: CPU予想など =====
            if self.race_type == 'jra':
                # Course data: jockey stats (optional)
                if self.fetch_course_jockey_stats and self.settings.get('race_id'):
                    course_stats = await self._fetch_course_data_and_parse_jockey_stats(page, base_url, race_key)
                    if course_stats:
                        race_data['course_jockey_stats'] = course_stats
                cpu_data = await self._fetch_cpu_prediction(page, race_key)
                if cpu_data:
                    race_data['cpu_prediction'] = cpu_data
                
                # 重賞の場合、ギリギリ情報と特集ページを取得
                is_graded = any(g in race_data.get('race_grade', '') for g in ['GI', 'GII', 'GIII', 'G1', 'G2', 'G3', '重賞'])
                
                fetch_daily = bool(self.settings.get('fetch_daily_special_pages', False))
                if (is_graded or fetch_daily) and not self.settings.get('skip_special_pages', False):
                    special = await self._fetch_special_pages(page, base_url, race_key, race_data.get('race_grade'))
                    # ギリギリ情報は取得しない設計のため race_data へはマージしません
                    if 'special_feature' in special:
                        race_data['special_feature'] = special['special_feature']
                    if 'daily_feature' in special:
                        race_data['daily_feature'] = special['daily_feature']
                    # aggregate labels collected across special/daily features (excluding '血統')
                    if special.get('labels'):
                        race_data['special_labels'] = special.get('labels')
                
                # AI指数は出馬表ページから既に取得済み（parse_race_dataで処理）
            
            # 個別馬ページは開かない（デフォルト）
            # 調教/厩舎/前走から集約した個別コメントを作成する（ポイントは後で再集約する）
            if not self.settings.get('skip_horse_comments', False):
                    self._aggregate_individual_comments(race_data.get('horses', []), parsed_stable_comment_data, parsed_previous_race_comment_data, parsed_training_data, None)
            # ===== 地方競馬専用ページの取得 =====
            if self.race_type == 'nar':
                # ポイントページを取得（地方競馬の11R/12Rのみ）
                point_data = await self._scrape_point_page(page, base_url)
                if point_data:
                    race_data['point_info'] = point_data
                    # ポイントデータがある場合は、ポイント由来のヒントを含めて再集約する
                    self._aggregate_individual_comments(race_data.get('horses', []), parsed_stable_comment_data, parsed_previous_race_comment_data, parsed_training_data, point_data)
                
                # 特定の馬のコメントを取得（穴馬のヒント）
                # 地方競馬では個別馬ページを開かない（point等のみ取得）
            
            # ===== レース結果ページの取得（レース終了後のみ） =====
            if self.settings.get('fetch_result', False) and self.seiseki_url:
                result_url = self.seiseki_url
                if not result_url:
                    # 結果ページURLを構築
                    result_url = f"{base_url}/seiseki/{self.settings['race_id']}"
                
                await self.rate_limiter.wait()
                
                try:
                    result_html = await self._fetch_page_content(page, result_url)
                    self._log_url(result_url, 'result', 'success')
                    if not self.settings.get('skip_debug_files', False):
                        with open(self.debug_dir / f"debug_result_{race_key}.html", "w", encoding="utf-8") as f:
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
                    with open(self.debug_dir / f"debug_fetches_{race_key}.json", "w", encoding="utf-8") as f:
                        import json
                        json.dump(self._last_fetches, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    logger.debug(f"debug_fetches JSON保存エラー: {e}")
            return race_data
        finally:
            if created_browser and browser:
                try:
                    await browser.close()
                except Exception as e:
                    logger.debug(f"ブラウザクローズ時のエラー: {e}")
                try:
                    await self._playwright.__aexit__(None, None, None)
                except Exception as e:
                    logger.debug(f"playwright __aexit__ エラー: {e}")