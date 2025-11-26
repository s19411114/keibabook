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
            
        Returns:
            CPU予想データ
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        cpu_data = {
            'horses': [],
            'summary': {}
        }
        
        # CPU予想テーブルを探す
        # 様々なセレクタパターンを試す
        cpu_table = soup.select_one("table.cpu, table.CPU, table[class*='cpu'], .cpu_table tbody, .CPUTable tbody")
        
        if not cpu_table:
            # 別のパターン: 出馬表ページ内のCPU予想セクション
            cpu_section = soup.select_one(".cpu_section, .CPUSection, [class*='cpu']")
            if cpu_section:
                cpu_table = cpu_section.find('table')
        
        if not cpu_table:
            # syutuba_sp テーブルからCPU関連データを探す
            cpu_table = soup.select_one(".syutuba_sp tbody")
        
        if cpu_table:
            for row in cpu_table.find_all('tr'):
                horse_data = self._parse_cpu_row(row)
                if horse_data and horse_data.get('horse_num'):
                    cpu_data['horses'].append(horse_data)
        
        # サマリー情報（ページ全体のコメント等）
        summary_section = soup.select_one(".cpu_summary, .CPUSummary, .summary")
        if summary_section:
            cpu_data['summary']['comment'] = summary_section.get_text(strip=True)
        
        logger.info(f"CPU予想取得: {len(cpu_data['horses'])}頭")
        return cpu_data
    
    def _parse_cpu_row(self, row) -> Optional[Dict[str, Any]]:
        """CPU予想の1行をパース"""
        horse_data = {}
        
        # 馬番
        horse_num_elem = row.select_one(".umaban")
        if horse_num_elem:
            horse_data['horse_num'] = horse_num_elem.get_text(strip=True)
        
        # 馬名
        horse_name_elem = row.select_one(".kbamei a, .horse_name a")
        if horse_name_elem:
            horse_data['horse_name'] = horse_name_elem.get_text(strip=True)
        
        # レーティング
        rating_elem = row.select_one(".rating, .Rating, [class*='rating'], td[class*='rating']")
        if rating_elem:
            rating_text = rating_elem.get_text(strip=True)
            try:
                horse_data['rating'] = float(rating_text) if rating_text else None
            except ValueError:
                horse_data['rating'] = rating_text
        
        # スピード指数
        speed_elem = row.select_one(".speed, .Speed, .speed_index, [class*='speed']")
        if speed_elem:
            speed_text = speed_elem.get_text(strip=True)
            try:
                horse_data['speed_index'] = float(speed_text) if speed_text else None
            except ValueError:
                horse_data['speed_index'] = speed_text
        
        # 調教印
        training_mark_elem = row.select_one(".training_mark, .cyokyo_mark, [class*='cyokyo']")
        if training_mark_elem:
            horse_data['training_mark'] = training_mark_elem.get_text(strip=True)
        
        # 血統印
        pedigree_mark_elem = row.select_one(".pedigree_mark, .kettou_mark, [class*='kettou']")
        if pedigree_mark_elem:
            horse_data['pedigree_mark'] = pedigree_mark_elem.get_text(strip=True)
        
        # 総合印（ファクター印）
        factor_mark_elem = row.select_one(".factor_mark, .total_mark, [class*='mark']")
        if factor_mark_elem:
            horse_data['factor_mark'] = factor_mark_elem.get_text(strip=True)
        
        # CPU指数
        cpu_index_elem = row.select_one(".cpu_index, .CPUIndex, [class*='index']")
        if cpu_index_elem:
            cpu_text = cpu_index_elem.get_text(strip=True)
            try:
                horse_data['cpu_index'] = float(cpu_text) if cpu_text else None
            except ValueError:
                horse_data['cpu_index'] = cpu_text
        
        return horse_data if horse_data else None
    
    def parse_girigiri_info(self, html_content: str) -> Dict[str, Any]:
        """
        ギリギリ情報（重賞）を解析
        
        レース直前の最新情報
        - 馬体重変動
        - パドック情報
        - 直前の仕上がり
        - 騎手コメント
        
        Args:
            html_content: ギリギリ情報ページのHTML
            
        Returns:
            ギリギリ情報データ
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        girigiri_data = {
            'horses': [],
            'overall_comment': '',
            'paddock_comment': '',
            'last_update': ''
        }
        
        # ギリギリ情報セクション
        girigiri_section = soup.select_one(".girigiri, .Girigiri, .tyokuzen, [class*='girigiri']")
        
        if girigiri_section:
            # 馬ごとの情報
            for item in girigiri_section.select(".horse_info, .HorseInfo, tr, .item"):
                horse_info = self._parse_girigiri_horse(item)
                if horse_info and horse_info.get('horse_num'):
                    girigiri_data['horses'].append(horse_info)
            
            # 全体コメント
            overall_elem = girigiri_section.select_one(".overall_comment, .OverallComment, .comment")
            if overall_elem:
                girigiri_data['overall_comment'] = overall_elem.get_text(strip=True)
        
        # パドック情報
        paddock_section = soup.select_one(".paddock, .Paddock, [class*='paddock']")
        if paddock_section:
            girigiri_data['paddock_comment'] = paddock_section.get_text(strip=True)
        
        # 最終更新時刻
        update_elem = soup.select_one(".update_time, .UpdateTime, .last_update")
        if update_elem:
            girigiri_data['last_update'] = update_elem.get_text(strip=True)
        
        logger.info(f"ギリギリ情報取得: {len(girigiri_data['horses'])}頭")
        return girigiri_data
    
    def _parse_girigiri_horse(self, item) -> Optional[Dict[str, Any]]:
        """ギリギリ情報の馬データをパース"""
        horse_data = {}
        
        # 馬番
        horse_num_elem = item.select_one(".umaban, .horse_num")
        if horse_num_elem:
            horse_data['horse_num'] = horse_num_elem.get_text(strip=True)
        
        # 馬名
        horse_name_elem = item.select_one(".kbamei a, .horse_name")
        if horse_name_elem:
            horse_data['horse_name'] = horse_name_elem.get_text(strip=True)
        
        # 馬体重変動
        weight_elem = item.select_one(".weight_change, .WeightChange, [class*='weight']")
        if weight_elem:
            horse_data['weight_change'] = weight_elem.get_text(strip=True)
        
        # パドック評価
        paddock_elem = item.select_one(".paddock_eval, .PaddockEval")
        if paddock_elem:
            horse_data['paddock_eval'] = paddock_elem.get_text(strip=True)
        
        # 直前コメント
        comment_elem = item.select_one(".comment, .Comment, .tyokuzen_comment")
        if comment_elem:
            horse_data['girigiri_comment'] = comment_elem.get_text(strip=True)
        
        return horse_data if horse_data else None
    
    def parse_special_feature(self, html_content: str) -> Dict[str, Any]:
        """
        特集ページ（重賞）を解析
        
        重賞レースの詳細分析:
        - 過去の傾向分析
        - 血統傾向
        - コース適性
        - 本命・対抗・穴馬分析
        
        Args:
            html_content: 特集ページのHTML
            
        Returns:
            特集ページデータ
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        feature_data = {
            'title': '',
            'analysis': [],
            'trends': {},
            'picks': {
                'honmei': [],  # 本命
                'taikou': [],  # 対抗
                'anaba': []    # 穴馬
            },
            'pedigree_trends': [],
            'course_analysis': ''
        }
        
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
        
        # 傾向データ
        trends_section = soup.select_one(".trends, .Trends, .trend_data")
        if trends_section:
            for item in trends_section.select(".trend_item, .TrendItem, li"):
                key_elem = item.select_one(".key, .label")
                value_elem = item.select_one(".value, .data")
                if key_elem and value_elem:
                    feature_data['trends'][key_elem.get_text(strip=True)] = value_elem.get_text(strip=True)
        
        # 本命・対抗・穴馬
        picks_section = soup.select_one(".picks, .Picks, .yosou")
        if picks_section:
            for category in ['honmei', 'taikou', 'anaba']:
                cat_elem = picks_section.select_one(f".{category}, .{category.capitalize()}")
                if cat_elem:
                    for horse in cat_elem.select(".horse, .Horse, li"):
                        feature_data['picks'][category].append(horse.get_text(strip=True))
        
        # 血統傾向
        pedigree_section = soup.select_one(".pedigree_trend, .PedigreeTrend, [class*='kettou']")
        if pedigree_section:
            for item in pedigree_section.select("li, .item"):
                feature_data['pedigree_trends'].append(item.get_text(strip=True))
        
        # コース分析
        course_section = soup.select_one(".course_analysis, .CourseAnalysis, [class*='course']")
        if course_section:
            feature_data['course_analysis'] = course_section.get_text(strip=True)
        
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
