"""
オッズデータベース管理
オッズの変化を記録・分析
"""
import os
import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger(__name__)


class OddsDBManager:
    """オッズデータベース管理クラス"""
    
    def __init__(self, db_dir: str = "data/db"):
        """
        Args:
            db_dir: データベースディレクトリ
        """
        self.db_dir = Path(db_dir)
        self.db_dir.mkdir(parents=True, exist_ok=True)
        
        # オッズテーブルのファイルパス
        self.odds_table_path = self.db_dir / "odds_history.csv"
        
        # テーブルを初期化
        self._init_table()
    
    def _init_table(self):
        """オッズテーブルを初期化"""
        if not self.odds_table_path.exists():
            pd.DataFrame(columns=[
                'race_id', 'horse_num', 'win_odds', 'place_odds', 'popularity',
                'fetched_at', 'timestamp'
            ]).to_csv(self.odds_table_path, index=False, encoding='utf-8-sig')
    
    def save_odds(self, odds_data: Dict[str, Any]):
        """
        オッズデータを保存
        
        Args:
            odds_data: オッズデータ（fetched_at, race_id, horsesを含む）
        """
        if not odds_data or 'horses' not in odds_data:
            return
        
        try:
            df = pd.read_csv(self.odds_table_path, encoding='utf-8-sig')
            
            fetched_at = odds_data.get('fetched_at', datetime.now().isoformat())
            race_id = odds_data.get('race_id', '')
            timestamp = datetime.now().timestamp()
            
            for horse in odds_data['horses']:
                new_row = pd.DataFrame([{
                    'race_id': race_id,
                    'horse_num': horse.get('horse_num', ''),
                    'win_odds': self._parse_odds_value(horse.get('win_odds', '')),
                    'place_odds': self._parse_odds_value(horse.get('place_odds', '')),
                    'popularity': horse.get('popularity', ''),
                    'fetched_at': fetched_at,
                    'timestamp': timestamp
                }])
                df = pd.concat([df, new_row], ignore_index=True)
            
            df.to_csv(self.odds_table_path, index=False, encoding='utf-8-sig')
            logger.info(f"オッズデータを保存: {race_id} ({len(odds_data['horses'])}頭)")
            
        except Exception as e:
            logger.error(f"オッズデータ保存エラー: {e}")
    
    def _parse_odds_value(self, odds_str: str) -> Optional[float]:
        """オッズ文字列を数値に変換"""
        if not odds_str:
            return None
        try:
            # "10.5" -> 10.5, "200.0" -> 200.0
            return float(str(odds_str).replace(',', '').replace('倍', ''))
        except Exception as e:
            logger.debug(f"オッズ文字列解析失敗: {odds_str} -> {e}")
            return None
    
    def get_odds_history(self, race_id: str, horse_num: Optional[str] = None) -> pd.DataFrame:
        """
        オッズ履歴を取得
        
        Args:
            race_id: レースID
            horse_num: 馬番（指定しない場合は全頭）
            
        Returns:
            オッズ履歴のDataFrame
        """
        if not self.odds_table_path.exists():
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(self.odds_table_path, encoding='utf-8-sig')
            df = df[df['race_id'] == race_id]
            
            if horse_num:
                df = df[df['horse_num'] == str(horse_num)]
            
            # タイムスタンプでソート
            df = df.sort_values('timestamp')
            
            return df
            
        except Exception as e:
            logger.error(f"オッズ履歴取得エラー: {e}")
            return pd.DataFrame()
    
    def analyze_odds_movement(self, race_id: str) -> Dict[str, Any]:
        """
        オッズの動きを分析
        
        Args:
            race_id: レースID
            
        Returns:
            分析結果
        """
        df = self.get_odds_history(race_id)
        
        if df.empty:
            return {}
        
        analysis = {}
        
        for horse_num in df['horse_num'].unique():
            horse_df = df[df['horse_num'] == horse_num]
            
            if len(horse_df) < 2:
                continue
            
            # 最初と最後のオッズ
            first_odds = horse_df.iloc[0]['win_odds']
            last_odds = horse_df.iloc[-1]['win_odds']
            
            # オッズの変化率
            if first_odds and last_odds:
                change_rate = ((last_odds - first_odds) / first_odds) * 100
            else:
                change_rate = 0
            
            # 最大・最小オッズ
            max_odds = horse_df['win_odds'].max()
            min_odds = horse_df['win_odds'].min()
            
            analysis[horse_num] = {
                'first_odds': first_odds,
                'last_odds': last_odds,
                'max_odds': max_odds,
                'min_odds': min_odds,
                'change_rate': change_rate,
                'data_points': len(horse_df)
            }
        
        return analysis
    
    def detect_suspicious_movement(self, race_id: str, threshold: float = 50.0) -> List[Dict[str, Any]]:
        """
        不審なオッズの動きを検出（八百長検出のヒント）
        
        Args:
            race_id: レースID
            threshold: 変化率の閾値（%）
            
        Returns:
            不審な動きのリスト
        """
        analysis = self.analyze_odds_movement(race_id)
        suspicious = []
        
        for horse_num, data in analysis.items():
            # 急激なオッズの変化（下落）を検出
            if data['change_rate'] < -threshold:
                suspicious.append({
                    'horse_num': horse_num,
                    'change_rate': data['change_rate'],
                    'first_odds': data['first_odds'],
                    'last_odds': data['last_odds'],
                    'reason': f"オッズが{abs(data['change_rate']):.1f}%急落"
                })
        
        return suspicious

