"""
中央競馬専用パーサー
CPU予想、ギリギリ情報（重賞）、特集ページ（重賞）、AI指数を取得
"""
import re
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)


class JRASpecialParser:
    """中央競馬専用パーサー - サイト最重要ページの解析"""
    
    def parse_cpu_prediction(self, html_content: str) -> Dict[str, Any]:
        """
        CPU予想ページを解析（最重要ページ）
        
        取得項目:
        - レーティング
        - スピード指数
        - 調教印
        - 血統印
        - その他の印
        
        Args:
            html_content: CPU予想ページのHTML
        
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        cpu_data = {
            'horses': [],
            'summary': {}
        }

        # CPU予想テーブルを探す
        cpu_table = soup.select_one("table.cpu, table.CPU, table[class*='cpu'], .cpu_table tbody, .CPUTable tbody")
        if not cpu_table:
            cpu_section = soup.select_one(".cpu_section, .CPUSection, [class*='cpu']")
            if cpu_section:
                cpu_table = cpu_section.find('table')
        if not cpu_table:
            cpu_table = soup.select_one(".syutuba_sp tbody")

        if cpu_table:
            for row in cpu_table.find_all('tr'):
                horse_data = self._parse_cpu_row(row)
                if horse_data and horse_data.get('horse_num'):
                    cpu_data['horses'].append(horse_data)

        # summary
        summary_section = soup.select_one(".cpu_summary, .CPUSummary, .summary")
        if summary_section:
            cpu_data['summary']['comment'] = summary_section.get_text(strip=True)

        logger.info(f"CPU予想取得: {len(cpu_data['horses'])}頭")
        return cpu_data

    def _parse_cpu_row(self, row) -> Optional[Dict[str, Any]]:
        """CPU予想の1行をパース"""
        horse_data = {}
        horse_num_elem = row.select_one(".umaban")
        if horse_num_elem:
            horse_data['horse_num'] = horse_num_elem.get_text(strip=True)

        horse_name_elem = row.select_one(".kbamei a, .horse_name a")
        if horse_name_elem:
            horse_data['horse_name'] = horse_name_elem.get_text(strip=True)

        rating_elem = row.select_one(".rating, .Rating, [class*='rating'], td[class*='rating']")
        if rating_elem:
            rating_text = rating_elem.get_text(strip=True)
            try:
                horse_data['rating'] = float(rating_text) if rating_text else None
            except ValueError:
                horse_data['rating'] = rating_text

        speed_elem = row.select_one(".speed, .Speed, .speed_index, [class*='speed']")
        if speed_elem:
            speed_text = speed_elem.get_text(strip=True)
            try:
                horse_data['speed_index'] = float(speed_text) if speed_text else None
            except Exception:
                horse_data['speed_index'] = speed_text

        training_mark_elem = row.select_one(".training_mark, .cyokyo_mark, [class*='cyokyo']")
        if training_mark_elem:
            horse_data['training_mark'] = training_mark_elem.get_text(strip=True)

        pedigree_mark_elem = row.select_one(".pedigree_mark, .kettou_mark, [class*='kettou']")
        if pedigree_mark_elem:
            horse_data['pedigree_mark'] = pedigree_mark_elem.get_text(strip=True)

        factor_mark_elem = row.select_one(".factor_mark, .total_mark, [class*='mark']")
        if factor_mark_elem:
            horse_data['factor_mark'] = factor_mark_elem.get_text(strip=True)

        cpu_index_elem = row.select_one(".cpu_index, .CPUIndex, [class*='index']")
        if cpu_index_elem:
            cpu_text = cpu_index_elem.get_text(strip=True)
            try:
                horse_data['cpu_index'] = float(cpu_text) if cpu_text else None
            except ValueError:
                horse_data['cpu_index'] = cpu_text

        return horse_data if horse_data else None
    
    # NOTE: ギリギリ（直前）情報のパースは運用方針により廃止しました（2025-12-10）。
    # 以前は馬体重変動・パドック・直前コメント等を取得していましたが、
    # これらの情報は運用上収集しないため削除しています。
    
    # (girigiri per-horse parser removed)
    
    def parse_special_feature(self, html_content: str) -> Dict[str, Any]:
        """
        特集ページ（重賞）を解析
        
        特集ページから取得するのは主にタイトルと自由形式の解析セクション（テキストラベル）です。
        特集ページからの「血統傾向」「コース適性」「本命・対抗・穴馬」の抽出は行わず、
        それぞれ専用のデータソース（血統ページ、コースデータ、AI推論）で扱います。
        
        Args:
            html_content: 特集ページのHTML
            
        Returns:
            特集ページデータ（新版）
            - labels: dict mapping arbitrary label titles to their textual content
            - '血統' と表記されるラベルは自動的に除外されます
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        feature_data = {
            'title': '',
            'analysis': [],
            # Free-form label dictionary (label -> content). Only generic labels are preserved.
            'labels': {}
        }
        # A general-purpose label dictionary (label name -> content string)
        feature_data['labels'] = {}
        
        # 特集タイトル
        title_elem = soup.select_one(".feature_title, .FeatureTitle, h1, h2")
        if title_elem:
            feature_data['title'] = title_elem.get_text(strip=True)
        
        # 分析セクション
        analysis_sections = soup.select(".analysis_section, .AnalysisSection, .section, article")
        for section in analysis_sections:
            section_title = section.select_one("h2, h3, .title")
            section_content = section.select_one(".content, p")
            if section_title and section_content:
                feature_data['analysis'].append({
                    'title': section_title.get_text(strip=True),
                    'content': section_content.get_text(strip=True)
                })

        # Generic label extraction: find heading-like nodes and capture following sibling
        # content blocks. This catches arbitrary labels we want to preserve.
        for heading in soup.select('h1, h2, h3, h4, .label, .label-title, .section-title'):
            title = heading.get_text(strip=True)
            if not title:
                continue
            lower_title = title.lower()
            # Skip any '血統' labeled sections and course analysis labels
            if ('血統' in title or '血統' in lower_title or 'kettou' in lower_title or 'コース' in title or 'コース' in lower_title or 'course' in lower_title):
                # Do not extract bloodline-labeled section into generic labels
                continue
            # Aggregate textual content until the next heading
            parts = []
            node = heading.find_next_sibling()
            while node and node.name not in ['h1', 'h2', 'h3', 'h4']:
                # Avoid capturing navigation or unrelated lists such as new registration pages
                try:
                    text = node.get_text(separator=' ', strip=True)
                except Exception:
                    node = node.find_next_sibling()
                    continue
                if text:
                    parts.append(text)
                node = node.find_next_sibling()
            # Save label content if present
            if parts:
                feature_data['labels'][title] = ' '.join(parts)
        
        # Note: 特集ページからの傾向分析（trends）や本命/対抗/穴馬の抽出は実施しません.
        # これらは専用のコースデータ/血統データ/AI推論で扱います.
        
        # 血統傾向 - do not populate from special pages. Pedigree is obtained separately
        # via dedicated pedigree endpoints; leaving pedigree_trends empty by design.
        
        # コース分析 - do not populate from special pages (may create biased insights)
        
        logger.info(f"特集ページ取得: {feature_data['title']}")

        return feature_data
        
    
    def parse_ai_index(self, html_content: str) -> Dict[str, Any]:
        """
        AI指数を解析（出馬表ページ内）
        
        出馬表ページ内のAI指数とレース展開予想
        
        Args:
            html_content: 出馬表ページのHTML
            
        Returns:
            AI指数データ
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        ai_data = {
            'horses': [],
            'race_prediction': '',
            'ai_comment': ''
        }
        
        # 出馬表からAI指数を抽出
        shutuba_table = soup.select_one(".syutuba_sp tbody")
        if shutuba_table:
            for row in shutuba_table.find_all('tr'):
                horse_ai = self._parse_ai_row(row)
                if horse_ai and horse_ai.get('horse_num'):
                    ai_data['horses'].append(horse_ai)
        
        # AI予想セクション
        ai_section = soup.select_one(".ai_prediction, .AIPrediction, [class*='ai']")
        if ai_section:
            ai_data['ai_comment'] = ai_section.get_text(strip=True)
        
        # レース展開予想（boxsectionから）
        for section in soup.select(".boxsection"):
            title = section.select_one(".title")
            if title and "展開" in title.get_text():
                content = section.get_text(separator=' ', strip=True)
                ai_data['race_prediction'] = content
        
        logger.info(f"AI指数取得: {len(ai_data['horses'])}頭")
        return ai_data

    def parse_course_jockey_stats(self, html_content: str) -> Dict[str, Any]:
        """
        Parse course data page to extract jockey statistics for that course.

        Returns a dict mapping jockey name to a dict containing 'win_rate', 'top2_rate', 'rides' where available.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        jockey_stats = {}

        # Try to find tables that include '騎手' as a header
        tables = soup.find_all('table')
        candidate_tables = []
        for tbl in tables:
            ths = tbl.select('th')
            headers = [th.get_text(strip=True) for th in ths]
            if any('騎手' in h or 'Jockey' in h or '騎手名' in h for h in headers):
                candidate_tables.append(tbl)

        # If no table candidates, try to find sections with '騎手' in title
        if not candidate_tables:
            for section in soup.select('[class*="jockey"], [id*="jockey"], .jockey_stats, .course_jockey'):
                table = section.find('table')
                if table:
                    candidate_tables.append(table)

        for tbl in candidate_tables:
            # Determine header column indexes
            headers = [th.get_text(strip=True) for th in tbl.select('th')]
            hidx = {h: i for i, h in enumerate(headers)}
            # Match common column names
            jockey_idx = None
            win_idx = None
            top2_idx = None
            rides_idx = None
            for i, h in enumerate(headers):
                if '騎手' in h or 'Jockey' in h or '騎手名' in h:
                    jockey_idx = i
                if '勝率' in h or '勝率(%)' in h:
                    win_idx = i
                if '連対' in h or '連対率' in h or '連対率(%)' in h:
                    top2_idx = i
                if '騎乗数' in h or '回数' in h or '出走数' in h:
                    rides_idx = i

            rows = tbl.select('tbody tr') or tbl.select('tr')
            for row in rows:
                cols = row.find_all(['td', 'th'])
                if not cols:
                    continue
                jockey_name = ''
                if jockey_idx is not None and jockey_idx < len(cols):
                    jockey_name = cols[jockey_idx].get_text(strip=True)
                else:
                    # fall back to first column
                    jockey_name = cols[0].get_text(strip=True)
                if not jockey_name:
                    continue
                # Parse numbers
                def parse_pct(text):
                    if not text:
                        return None
                    text = text.replace('%', '').replace('％', '').strip()
                    try:
                        return float(text)
                    except Exception:
                        return None

                win_pct = None
                top2_pct = None
                rides_n = None
                if win_idx is not None and win_idx < len(cols):
                    win_pct = parse_pct(cols[win_idx].get_text(strip=True))
                if top2_idx is not None and top2_idx < len(cols):
                    top2_pct = parse_pct(cols[top2_idx].get_text(strip=True))
                if rides_idx is not None and rides_idx < len(cols):
                    try:
                        rides_n = int(cols[rides_idx].get_text(strip=True))
                    except Exception:
                        rides_n = None

                jockey_stats[jockey_name] = {
                    'win_rate': win_pct,
                    'top2_rate': top2_pct,
                    'rides': rides_n
                }

        return jockey_stats
    
    def _parse_ai_row(self, row) -> Optional[Dict[str, Any]]:
        """AI指数の1行をパース"""
        horse_data = {}
        
        # 馬番
        horse_num_elem = row.select_one(".umaban")
        if horse_num_elem:
            horse_data['horse_num'] = horse_num_elem.get_text(strip=True)
        
        # 馬名
        horse_name_elem = row.select_one(".kbamei a")
        if horse_name_elem:
            horse_data['horse_name'] = horse_name_elem.get_text(strip=True)
        
        # AI指数（複数のセレクタパターン）
        ai_selectors = [
            ".ai_index", ".AIIndex", ".ai", "[class*='ai']",
            "td[data-ai]", ".js-ai-value"
        ]
        for selector in ai_selectors:
            ai_elem = row.select_one(selector)
            if ai_elem:
                ai_text = ai_elem.get_text(strip=True)
                if ai_text:
                    try:
                        horse_data['ai_index'] = float(ai_text)
                    except ValueError:
                        horse_data['ai_index'] = ai_text
                    break
        
        # AI評価（S/A/B/C等）
        ai_rank_elem = row.select_one(".ai_rank, .AIRank, [class*='rank']")
        if ai_rank_elem:
            horse_data['ai_rank'] = ai_rank_elem.get_text(strip=True)
        
        return horse_data if horse_data else None
