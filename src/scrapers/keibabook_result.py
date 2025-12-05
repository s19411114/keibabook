"""
競馬ブック レース後ページスクレイパー
レース後コメント・次走へのメモを取得
"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from typing import Dict, List, Any
from src.utils.logger import get_logger

logger = get_logger(__name__)


class KeibaBookResultScraper:
    """競馬ブック レース後ページスクレイパー"""
    
    def __init__(self, headless: bool = True):
        """
        初期化
        
        Args:
            headless: ヘッドレスモードで実行するか
        """
        self.headless = headless
    
    async def fetch_result(self, race_id: str, cookies_path: str = "cookies.json") -> Dict[str, Any]:
        """
        レース後コメント・次走へのメモを取得
        
        Args:
            race_id: レースID（例: "2025113004"）
            cookies_path: クッキーファイルパス
            
        Returns:
            {
                'race_id': レースID,
                'race_name': レース名,
                'result_comments': [  # 馬ごとのレース後コメント
                    {
                        'horse_num': 馬番,
                        'horse_name': 馬名,
                        'rank': 着順,
                        'comment': レース後コメント,
                        'next_race_memo': 次走へのメモ
                    },
                    ...
                ]
            }
        """
        url = f"https://s.keibabook.co.jp/cyuou/kekka/{race_id}"
        logger.info(f"競馬ブック レース後取得開始: {url}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context()
            
            # クッキーを読み込み
            try:
                import json
                from pathlib import Path
                cookie_file = Path(cookies_path)
                if cookie_file.exists():
                    with open(cookie_file, 'r', encoding='utf-8') as f:
                        cookies = json.load(f)
                    await context.add_cookies(cookies)
                    logger.info(f"クッキー読み込み完了: {len(cookies)}件")
            except Exception as e:
                logger.warning(f"クッキー読み込みエラー: {e}")
            
            page = await context.new_page()
            
            try:
                # ページ取得
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(2)  # レンダリング待機
                
                # HTMLを取得
                html_content = await page.content()
                
                # デバッグ用にHTML保存
                with open(Path("debug_files") / f"debug_result_{race_id}.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                
                # パース
                result_data = self._parse_result_page(html_content, race_id)
                
                logger.info(f"レース後コメント取得完了: {len(result_data['result_comments'])}頭")
                return result_data
                
            except Exception as e:
                logger.error(f"レース後取得エラー: {e}")
                return {'race_id': race_id, 'result_comments': []}
            finally:
                await browser.close()
    
    def _parse_result_page(self, html_content: str, race_id: str) -> Dict[str, Any]:
        """
        レース後ページをパース
        
        Args:
            html_content: HTML
            race_id: レースID
            
        Returns:
            パース済みデータ
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        result_data = {
            'race_id': race_id,
            'race_name': '',
            'result_comments': []
        }
        
        # レース名を取得
        race_name_elem = soup.select_one(".racemei p, .race_name, h1.race_title")
        if race_name_elem:
            result_data['race_name'] = race_name_elem.get_text(strip=True)
        
        # レース後コメントテーブルを探す
        # 複数のセレクタパターンを試す
        comment_table = soup.select_one("table.result_comment, table.kekka, table.syutuba")
        
        if not comment_table:
            # tbody内を直接探す
            tbodies = soup.find_all('tbody')
            for tbody in tbodies:
                # コメント用のクラスまたは構造を持つテーブルを探す
                if tbody.find('td', class_='comment') or tbody.find('div', class_='comment'):
                    comment_table = tbody.parent
                    break
        
        if comment_table:
            rows = comment_table.find_all('tr')
            
            for row in rows:
                # 馬番を探す
                horse_num_elem = row.select_one(".umaban, td.umaban")
                if not horse_num_elem:
                    continue
                
                horse_num = horse_num_elem.get_text(strip=True)
                
                # 馬名
                horse_name_elem = row.select_one(".kbamei a, td.horse_name a, a.horse_link")
                horse_name = horse_name_elem.get_text(strip=True) if horse_name_elem else ''
                
                # 着順
                rank_elem = row.select_one(".chakujyun, td.rank, td.finish")
                rank = rank_elem.get_text(strip=True) if rank_elem else ''
                
                # レース後コメント
                comment_elem = row.select_one(".race_comment, td.comment, div.comment")
                comment = comment_elem.get_text(strip=True) if comment_elem else ''
                
                # 次走へのメモ（別のセルまたは次の行にある可能性）
                next_memo_elem = row.select_one(".next_memo, td.next_race_memo, div.next_memo")
                if not next_memo_elem:
                    # 次の行を探す
                    next_row = row.find_next_sibling('tr')
                    if next_row and next_row.get('class') and 'memo_row' in next_row.get('class', []):
                        next_memo_elem = next_row.select_one("td, div")
                
                next_memo = next_memo_elem.get_text(strip=True) if next_memo_elem else ''
                
                result_data['result_comments'].append({
                    'horse_num': horse_num,
                    'horse_name': horse_name,
                    'rank': rank,
                    'comment': comment,
                    'next_race_memo': next_memo
                })
                
                logger.debug(f"{horse_num}番 {horse_name}: コメント={comment[:20]}...")
        else:
            logger.warning("レース後コメントテーブルが見つかりません")
        
        return result_data


# テスト用
if __name__ == "__main__":
    async def test():
        scraper = KeibaBookResultScraper(headless=False)
        result = await scraper.fetch_result("2025113004")  # 東京11R ジャパンC
        print(f"レース名: {result['race_name']}")
        print(f"コメント数: {len(result['result_comments'])}")
        for comment in result['result_comments'][:3]:
            print(f"  {comment['horse_num']}番 {comment['horse_name']} ({comment['rank']}着)")
            print(f"    コメント: {comment['comment']}")
            print(f"    次走メモ: {comment['next_race_memo']}")
    
    asyncio.run(test())
