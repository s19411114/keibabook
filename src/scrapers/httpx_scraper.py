"""
================================================================================
httpxベース軽量スクレイパー
================================================================================

Playwrightの代わりにhttpxを使用した軽量版スクレイパー。
Streamlit環境でも安定して動作します。

【主な変更点】
- Playwright → httpx（同期/非同期両対応）
- ブラウザ起動不要で高速
- Cookieベースの認証をそのまま使用

【互換性】
- 既存のパーサーロジックはそのまま使用
- 既存のCookieファイル（cookies.json）をそのまま使用
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import httpx
from bs4 import BeautifulSoup

from src.utils.config import load_settings
from src.utils.logger import get_logger
from src.utils.rate_limiter import RateLimiter

logger = get_logger(__name__)


class HttpxKeibaBookScraper:
    """
    httpxを使用した軽量スクレイパー
    
    Playwrightを使わないため、Streamlit環境でもクラッシュしない
    """
    
    # ユーザーエージェント（スマホ版サイト用）
    USER_AGENT = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
    
    # タイムアウト設定
    DEFAULT_TIMEOUT = 30.0
    
    def __init__(self, settings: Dict, db_manager=None):
        """
        Args:
            settings: 設定辞書
            db_manager: CSVDBManagerインスタンス（オプション）
        """
        self.settings = settings
        self.shutuba_url = settings.get('shutuba_url', '')
        self.race_type = settings.get('race_type', 'jra')
        self.skip_duplicate_check = settings.get('skip_duplicate_check', False)
        self.db_manager = db_manager
        self.rate_limiter = RateLimiter(settings.get('rate_limit_base'))
        
        # Cookie管理
        self.cookie_file = settings.get('cookie_file', 'cookies.json')
        self.cookies = self._load_cookies()
        
        # HTTPクライアント設定
        self.timeout = httpx.Timeout(
            settings.get('httpx_timeout', self.DEFAULT_TIMEOUT),
            connect=10.0
        )
        
        # デバッグ情報
        self._last_fetches = []
        
        # ベースURL
        if self.race_type == 'nar':
            self.base_url_pattern = "https://s.keibabook.co.jp/chihou"
        else:
            self.base_url_pattern = "https://s.keibabook.co.jp/cyuou"
    
    def _load_cookies(self) -> Dict[str, str]:
        """Cookieファイルから読み込み"""
        cookie_path = Path(self.cookie_file)
        
        if not cookie_path.exists():
            logger.warning(f"Cookieファイルが存在しません: {cookie_path}")
            return {}
        
        try:
            with open(cookie_path, 'r', encoding='utf-8') as f:
                cookie_list = json.load(f)
            
            # Playwright形式からhttpx形式に変換
            # [{"name": "tk", "value": "xxx", "domain": ".keibabook.co.jp"}, ...]
            cookies = {}
            for c in cookie_list:
                name = c.get('name', '')
                value = c.get('value', '')
                if name and value:
                    cookies[name] = value
            
            logger.info(f"Cookie読み込み完了: {len(cookies)}個")
            return cookies
            
        except Exception as e:
            logger.error(f"Cookie読み込みエラー: {e}")
            return {}
    
    def is_cookie_valid(self) -> Tuple[bool, str]:
        """Cookieの有効性を確認"""
        cookie_path = Path(self.cookie_file)
        
        if not cookie_path.exists():
            return False, "Cookieファイルが存在しません"
        
        try:
            with open(cookie_path, 'r', encoding='utf-8') as f:
                cookie_list = json.load(f)
            
            if not cookie_list:
                return False, "Cookieが空です"
            
            # tkクッキーを確認
            now = int(time.time())
            for c in cookie_list:
                if c.get('name') == 'tk':
                    exp = c.get('expires', 0)
                    if exp and exp < now:
                        return False, "tkクッキーの期限切れです"
                    
                    remaining_days = (exp - now) / 86400 if exp else 0
                    return True, f"残り{remaining_days:.1f}日"
            
            return False, "tkクッキーが見つかりません"
            
        except Exception as e:
            return False, f"エラー: {e}"
    
    async def _fetch_page(self, url: str, retry_count: int = 3) -> str:
        """
        ページを取得（非同期版）
        
        Args:
            url: 取得するURL
            retry_count: リトライ回数
            
        Returns:
            HTMLコンテンツ
        """
        headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
        }
        
        for attempt in range(retry_count):
            try:
                t_start = time.perf_counter()
                
                async with httpx.AsyncClient(
                    timeout=self.timeout,
                    cookies=self.cookies,
                    follow_redirects=True
                ) as client:
                    response = await client.get(url, headers=headers)
                
                t_end = time.perf_counter()
                
                # ステータスコードをチェック
                if response.status_code == 429:
                    wait_seconds = min(10 * (attempt + 1), 30)
                    logger.warning(f"429 Too Many Requests: {wait_seconds}秒待機")
                    await asyncio.sleep(wait_seconds)
                    continue
                
                response.raise_for_status()
                
                # デバッグ情報を記録
                self._last_fetches.append({
                    'url': url,
                    'status': response.status_code,
                    'time_ms': (t_end - t_start) * 1000
                })
                
                logger.info(f"ページ取得成功: {url} ({response.status_code})")
                return response.text
                
            except httpx.TimeoutException:
                logger.warning(f"タイムアウト（リトライ {attempt + 1}/{retry_count}）: {url}")
                if attempt < retry_count - 1:
                    await asyncio.sleep(2 * (attempt + 1))
                    
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTPエラー: {e.response.status_code} - {url}")
                raise
                
            except Exception as e:
                logger.error(f"取得エラー: {e}")
                if attempt < retry_count - 1:
                    await asyncio.sleep(2 * (attempt + 1))
                else:
                    raise
        
        raise Exception(f"ページ取得に失敗しました: {url}")
    
    def fetch_page_sync(self, url: str, retry_count: int = 3) -> str:
        """
        ページを取得（同期版）
        
        Streamlitのイベントループ問題を回避するための同期版
        """
        headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
        }
        
        for attempt in range(retry_count):
            try:
                t_start = time.perf_counter()
                
                with httpx.Client(
                    timeout=self.timeout,
                    cookies=self.cookies,
                    follow_redirects=True
                ) as client:
                    response = client.get(url, headers=headers)
                
                t_end = time.perf_counter()
                
                if response.status_code == 429:
                    wait_seconds = min(10 * (attempt + 1), 30)
                    logger.warning(f"429 Too Many Requests: {wait_seconds}秒待機")
                    time.sleep(wait_seconds)
                    continue
                
                response.raise_for_status()
                
                self._last_fetches.append({
                    'url': url,
                    'status': response.status_code,
                    'time_ms': (t_end - t_start) * 1000
                })
                
                logger.info(f"ページ取得成功: {url} ({response.status_code})")
                return response.text
                
            except httpx.TimeoutException:
                logger.warning(f"タイムアウト（リトライ {attempt + 1}/{retry_count}）: {url}")
                if attempt < retry_count - 1:
                    time.sleep(2 * (attempt + 1))
                    
            except Exception as e:
                logger.error(f"取得エラー: {e}")
                if attempt < retry_count - 1:
                    time.sleep(2 * (attempt + 1))
                else:
                    raise
        
        raise Exception(f"ページ取得に失敗しました: {url}")
    
    def verify_login_by_horse_count(self, html_content: str) -> Tuple[bool, int]:
        """
        HTMLから馬の数でログイン状態を確認
        
        - 3頭以下 = 未ログイン
        - 6頭以上 = ログイン済み
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        horse_count = 0
        
        # パターン1: 出馬表テーブル
        rows = soup.select('.syutuba_sp tbody tr')
        if rows:
            # 馬番がある行だけカウント
            horse_count = len([r for r in rows if r.select_one('.umaban')])
        
        # パターン2: 馬名リンク
        if horse_count == 0:
            links = soup.select('a.kbamei, a[href*="/uma/"]')
            if links:
                horse_count = len(links)
        
        logger.info(f"検出された馬の数: {horse_count}")
        
        is_logged_in = horse_count >= 6
        return is_logged_in, horse_count
    
    def _parse_race_data(self, html_content: str) -> Dict:
        """
        出馬表ページをパース
        
        既存のKeibaBookScraperと同じロジック
        """
        import re
        soup = BeautifulSoup(html_content, 'html.parser')
        race_data = {}
        
        # レース名とグレード
        racemei_p_elements = soup.select(".racemei p")
        if len(racemei_p_elements) > 1:
            race_data['race_name'] = racemei_p_elements[0].get_text(strip=True)
            race_data['race_grade'] = racemei_p_elements[1].get_text(strip=True)
        
        # 距離・コース条件
        racetitle_sub_p_elements = soup.select(".racetitle_sub p")
        if len(racetitle_sub_p_elements) > 1:
            full_condition = racetitle_sub_p_elements[1].get_text(strip=True)
            race_data['full_condition'] = full_condition
            
            distance_match = re.search(r'(\d+m)', full_condition)
            race_data['distance'] = distance_match.group(1) if distance_match else full_condition.split(' ')[0]
            
            course_match = re.search(r'\((.*?)\)', full_condition)
            race_data['course'] = course_match.group(1) if course_match else ''
            
            weather_match = re.search(r'\)\s*(.+)$', full_condition)
            race_data['weather_track'] = weather_match.group(1) if weather_match else ''
        
        if len(racetitle_sub_p_elements) > 0:
            race_data['race_class'] = racetitle_sub_p_elements[0].get_text(strip=True)
        
        # 馬リスト
        horses = []
        shutuba_table = soup.select_one(".syutuba_sp tbody")
        
        if shutuba_table:
            for row in shutuba_table.find_all('tr'):
                horse_num_elem = row.select_one(".umaban")
                horse_name_elem = row.select_one(".kbamei a")
                
                if not (horse_num_elem and horse_name_elem):
                    continue
                
                horse_data = {}
                
                # 枠番
                waku_elem = row.select_one(".waku p")
                horse_data['waku'] = waku_elem.get_text(strip=True) if waku_elem else ""
                
                # 馬番
                horse_data['horse_num'] = horse_num_elem.get_text(strip=True)
                
                # 予想印
                mark_elem = row.select_one(".tmyoso")
                if mark_elem:
                    myuma_mark = mark_elem.select_one(".myumamark")
                    yoso_show = mark_elem.select_one(".js-yoso-show")
                    star_mark = myuma_mark.get_text(strip=True) if myuma_mark else ""
                    num_mark = yoso_show.get_text(strip=True) if yoso_show else ""
                    horse_data['prediction_mark'] = f"{star_mark}{num_mark}".strip()
                else:
                    horse_data['prediction_mark'] = ""
                
                # 馬名
                horse_data['horse_name'] = horse_name_elem.get_text(strip=True)
                horse_data['horse_name_link'] = horse_name_elem.get('href', '')
                
                # 騎手情報
                kisyu_p = row.select_one(".kisyu")
                jockey_elem = row.select_one(".kisyu a")
                
                if kisyu_p:
                    kisyu_text = kisyu_p.get_text(separator=' ', strip=True)
                    age_match = re.search(r'([牡牝セ騸])(\d+)', kisyu_text)
                    horse_data['sex'] = age_match.group(1) if age_match else ""
                    horse_data['age'] = age_match.group(2) if age_match else ""
                    horse_data['jockey'] = jockey_elem.get_text(strip=True) if jockey_elem else ""
                    
                    weight_match = re.search(r'\s(\d{2}(?:\.\d)?)\s*$', kisyu_text)
                    horse_data['weight'] = weight_match.group(1) if weight_match else ""
                else:
                    horse_data['jockey'] = jockey_elem.get_text(strip=True) if jockey_elem else ""
                    horse_data['sex'] = ""
                    horse_data['age'] = ""
                    horse_data['weight'] = ""
                
                # 短評
                tanpyo_elem = row.select_one(".tanpyo")
                horse_data['comment'] = tanpyo_elem.get_text(strip=True) if tanpyo_elem else ""
                
                # オッズ
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
                
                horse_data['odds_text'] = f"{horse_data.get('odds', '')} {horse_data.get('popularity', '')}人気" if horse_data.get('odds') else ""
                
                horses.append(horse_data)
        
        race_data['horses'] = horses
        
        return race_data
    
    def _parse_pedigree_data(self, html_content: str) -> List[Dict]:
        """血統データをパース"""
        soup = BeautifulSoup(html_content, 'html.parser')
        pedigree_list = []
        
        pedigree_tables = soup.select("table.kettou.sandai")
        
        for table in pedigree_tables:
            links = table.select("a.umalink_click")
            
            if len(links) >= 14:
                # 三代血統完全版
                pedigree_data = {
                    'father': links[0].get_text(strip=True).replace('\n', ' '),
                    'mother': links[3].get_text(strip=True).replace('\n', ' '),
                    'father_father': links[1].get_text(strip=True).replace('\n', ' '),
                    'father_mother': links[2].get_text(strip=True).replace('\n', ' '),
                    'mothers_father': links[4].get_text(strip=True).replace('\n', ' '),
                    'mothers_mother': links[5].get_text(strip=True).replace('\n', ' '),
                }
                pedigree_list.append(pedigree_data)
            elif len(links) >= 6:
                # 二代血統
                pedigree_data = {
                    'father': links[0].get_text(strip=True).replace('\n', ' '),
                    'mother': links[3].get_text(strip=True).replace('\n', ' '),
                    'father_father': links[1].get_text(strip=True).replace('\n', ' '),
                    'father_mother': links[2].get_text(strip=True).replace('\n', ' '),
                    'mothers_father': links[4].get_text(strip=True).replace('\n', ' '),
                    'mothers_mother': links[5].get_text(strip=True).replace('\n', ' '),
                }
                pedigree_list.append(pedigree_data)
            elif len(links) >= 2:
                # 最低限（父、母のみ）
                mother_links = table.select("td.hinba a.umalink_click")
                mother = mother_links[0].get_text(strip=True) if mother_links else ''
                mothers_father = mother_links[1].get_text(strip=True) if len(mother_links) > 1 else ''
                
                pedigree_data = {
                    'father': links[0].get_text(strip=True).replace('\n', ' '),
                    'mother': mother,
                    'mothers_father': mothers_father,
                }
                pedigree_list.append(pedigree_data)
        
        return pedigree_list
    
    def _parse_training_data(self, html_content: str) -> Dict:
        """調教データをパース"""
        from src.utils.training_converter import convert_training_data
        
        soup = BeautifulSoup(html_content, 'html.parser')
        training_data = {}
        
        # TrainingTableパターン
        training_table = soup.select_one("table.TrainingTable tbody")
        if training_table:
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
                
                times = [t for t in times_str.split('-') if t and t != '-']
                
                if horse_num not in training_data:
                    training_data[horse_num] = {
                        'horse_name': '',
                        'tanpyo': '',
                        'details': []
                    }
                
                detail = {
                    'date_location': f"{date} {location}",
                    '追い切り方': evaluation,
                    'times': times,
                    'positions': [''] * len(times),
                    'awase': '',
                    'comment': ''
                }
                
                training_data[horse_num]['details'].append(detail)
        
        # 調教タイム変換を適用
        if training_data:
            training_data = convert_training_data(training_data)
        
        return training_data
    
    def scrape_sync(self) -> Dict:
        """
        スクレイピング実行（同期版）
        
        Streamlitから直接呼び出せる同期版
        """
        race_key = self.settings.get('race_key', 'unknown')
        race_id = self.settings.get('race_id', '')
        
        try:
            # Cookie有効性チェック
            is_valid, status = self.is_cookie_valid()
            if not is_valid:
                logger.warning(f"Cookie問題: {status}")
            
            # 出馬表ページを取得
            logger.info(f"出馬表取得開始: {self.shutuba_url}")
            html_content = self.fetch_page_sync(self.shutuba_url)
            
            # ログイン状態確認
            is_logged_in, horse_count = self.verify_login_by_horse_count(html_content)
            if not is_logged_in:
                logger.warning(f"⚠️ 未ログイン状態（{horse_count}頭のみ）。全頭データを取得するにはログインが必要です。")
            else:
                logger.info(f"✅ ログイン確認済（{horse_count}頭）")
            
            # デバッグ用HTML保存
            if not self.settings.get('skip_debug_files', False):
                with open(f"debug_page_{race_key}.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
            
            # 出馬表をパース
            race_data = self._parse_race_data(html_content)
            race_data['login_status'] = 'logged_in' if is_logged_in else 'not_logged_in'
            race_data['horse_count'] = horse_count
            
            # URL記録
            if self.db_manager:
                self.db_manager.log_url(self.shutuba_url, race_id, 'shutuba', 'success')
            
            # 血統ページを取得
            base_url = '/'.join(self.shutuba_url.split('/')[:4])
            pedigree_url = f"{base_url}/kettou/{race_id}"
            
            if not self.settings.get('skip_pedigree', False):
                try:
                    time.sleep(1)  # レート制御
                    pedigree_html = self.fetch_page_sync(pedigree_url)
                    
                    if not self.settings.get('skip_debug_files', False):
                        with open(f"debug_pedigree_{race_key}.html", "w", encoding="utf-8") as f:
                            f.write(pedigree_html)
                    
                    pedigree_list = self._parse_pedigree_data(pedigree_html)
                    
                    # 血統データをマージ
                    for idx, horse in enumerate(race_data.get('horses', [])):
                        if idx < len(pedigree_list):
                            horse['pedigree_data'] = pedigree_list[idx]
                        else:
                            horse['pedigree_data'] = {}
                    
                    if self.db_manager:
                        self.db_manager.log_url(pedigree_url, race_id, 'pedigree', 'success')
                    
                    logger.info(f"血統データ取得成功: {len(pedigree_list)}頭")
                    
                except Exception as e:
                    logger.warning(f"血統データ取得エラー: {e}")
            
            # 調教ページを取得（中央競馬のみ）
            if self.race_type != 'nar' and not self.settings.get('skip_training', False):
                training_url = f"{base_url}/cyokyo/0/{race_id}"
                
                try:
                    time.sleep(1)  # レート制御
                    training_html = self.fetch_page_sync(training_url)
                    
                    if not self.settings.get('skip_debug_files', False):
                        with open(f"debug_training_{race_key}.html", "w", encoding="utf-8") as f:
                            f.write(training_html)
                    
                    training_data = self._parse_training_data(training_html)
                    
                    # 調教データをマージ
                    for horse in race_data.get('horses', []):
                        horse_num = horse.get('horse_num')
                        if horse_num in training_data:
                            horse['training_data'] = training_data[horse_num]
                        else:
                            horse['training_data'] = {}
                    
                    if self.db_manager:
                        self.db_manager.log_url(training_url, race_id, 'training', 'success')
                    
                    logger.info(f"調教データ取得成功: {len(training_data)}頭")
                    
                except Exception as e:
                    logger.warning(f"調教データ取得エラー: {e}")
            
            logger.info(f"スクレイピング完了: {len(race_data.get('horses', []))}頭")
            return race_data
            
        except Exception as e:
            logger.error(f"スクレイピングエラー: {e}")
            raise
    
    async def scrape(self, context=None, page=None) -> Dict:
        """
        スクレイピング実行（非同期版）
        
        既存のKeibaBookScraperとの互換性のため
        """
        # 同期版を呼び出し（httpxは同期/非同期両対応だが、シンプルに同期版を使う）
        return self.scrape_sync()


# 互換性のためのエイリアス
def create_httpx_scraper(settings: Dict, db_manager=None) -> HttpxKeibaBookScraper:
    """httpxスクレイパーを作成"""
    return HttpxKeibaBookScraper(settings, db_manager)
