"""
CSVデータベース管理モジュール
重複チェック、差分取得、データ保存を担当
"""
import os
import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CSVDBManager:
    """CSV形式のデータベース管理クラス"""
    
    def __init__(self, db_dir: str = "data/db"):
        """
        Args:
            db_dir: データベースCSVファイルの保存ディレクトリ
        """
        self.db_dir = Path(db_dir)
        self.db_dir.mkdir(parents=True, exist_ok=True)
        
        # 各テーブルのファイルパス
        self.race_table_path = self.db_dir / "races.csv"
        self.horse_table_path = self.db_dir / "horses.csv"
        self.training_table_path = self.db_dir / "trainings.csv"
        self.pedigree_table_path = self.db_dir / "pedigrees.csv"
        self.comment_table_path = self.db_dir / "comments.csv"
        self.past_result_table_path = self.db_dir / "past_results.csv"
        self.url_log_path = self.db_dir / "url_log.csv"
        
        # テーブルを初期化
        self._init_tables()
    
    def _init_tables(self):
        """各テーブルファイルを初期化（存在しない場合）"""
        # URLログテーブル（重複チェック用）
        if not self.url_log_path.exists():
            pd.DataFrame(columns=[
                'url', 'race_id', 'page_type', 'fetched_at', 'status'
            ]).to_csv(self.url_log_path, index=False, encoding='utf-8-sig')
        
        # レーステーブル
        if not self.race_table_path.exists():
            pd.DataFrame(columns=[
                'race_id', 'race_key', 'race_name', 'race_grade', 'distance',
                'venue', 'date', 'created_at', 'updated_at'
            ]).to_csv(self.race_table_path, index=False, encoding='utf-8-sig')
        
        # 馬テーブル
        if not self.horse_table_path.exists():
            pd.DataFrame(columns=[
                'race_id', 'horse_num', 'horse_name', 'jockey', 'created_at', 'updated_at'
            ]).to_csv(self.horse_table_path, index=False, encoding='utf-8-sig')
    
    def is_url_fetched(self, url: str) -> bool:
        """
        URLが既に取得済みかチェック
        
        Args:
            url: チェックするURL
            
        Returns:
            取得済みの場合True
        """
        if not self.url_log_path.exists():
            return False
        
        try:
            df = pd.read_csv(self.url_log_path, encoding='utf-8-sig')
            return url in df['url'].values
        except Exception as e:
            logger.warning(f"URLログ読み込みエラー: {e}")
            return False
    
    def log_url(self, url: str, race_id: str, page_type: str, status: str = "success"):
        """
        URL取得をログに記録
        
        Args:
            url: 取得したURL
            race_id: レースID
            page_type: ページタイプ（shutuba, training, pedigree等）
            status: 取得ステータス（success, error等）
        """
        try:
            df = pd.read_csv(self.url_log_path, encoding='utf-8-sig')
            new_row = pd.DataFrame([{
                'url': url,
                'race_id': race_id,
                'page_type': page_type,
                'fetched_at': datetime.now().isoformat(),
                'status': status
            }])
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(self.url_log_path, index=False, encoding='utf-8-sig')
        except Exception as e:
            logger.error(f"URLログ記録エラー: {e}")
    
    def save_race_data(self, race_data: Dict[str, Any], race_id: str, race_key: str):
        """
        レースデータをCSVに保存（差分更新）
        
        Args:
            race_data: スクレイピングしたレースデータ
            race_id: レースID
            race_key: レースキー
        """
        now = datetime.now().isoformat()
        
        # レース基本情報を保存
        race_df = pd.read_csv(self.race_table_path, encoding='utf-8-sig')
        race_row = {
            'race_id': race_id,
            'race_key': race_key,
            'race_name': race_data.get('race_name', ''),
            'race_grade': race_data.get('race_grade', ''),
            'distance': race_data.get('distance', ''),
            'venue': '',  # 後で追加可能
            'date': '',  # 後で追加可能
            'updated_at': now
        }
        
        # 既存レコードを更新、なければ追加
        existing = race_df[race_df['race_id'] == race_id]
        if len(existing) > 0:
            race_df.loc[race_df['race_id'] == race_id, list(race_row.keys())] = list(race_row.values())
        else:
            race_row['created_at'] = now
            race_df = pd.concat([race_df, pd.DataFrame([race_row])], ignore_index=True)
        
        race_df.to_csv(self.race_table_path, index=False, encoding='utf-8-sig')
        
        # 馬データを保存
        if 'horses' in race_data:
            self._save_horses(race_data['horses'], race_id, now)
        
        logger.info(f"レースデータを保存: {race_id}")
    
    def _save_horses(self, horses: List[Dict[str, Any]], race_id: str, timestamp: str):
        """馬データをCSVに保存"""
        if not self.horse_table_path.exists():
            return
        
        horse_df = pd.read_csv(self.horse_table_path, encoding='utf-8-sig')
        
        for horse in horses:
            horse_num = horse.get('horse_num', '')
            horse_row = {
                'race_id': race_id,
                'horse_num': horse_num,
                'horse_name': horse.get('horse_name', ''),
                'jockey': horse.get('jockey', ''),
                'updated_at': timestamp
            }
            
            # 既存レコードを更新、なければ追加
            existing = horse_df[(horse_df['race_id'] == race_id) & (horse_df['horse_num'] == horse_num)]
            if len(existing) > 0:
                horse_df.loc[
                    (horse_df['race_id'] == race_id) & (horse_df['horse_num'] == horse_num),
                    list(horse_row.keys())
                ] = list(horse_row.values())
            else:
                horse_row['created_at'] = timestamp
                horse_df = pd.concat([horse_df, pd.DataFrame([horse_row])], ignore_index=True)
        
        horse_df.to_csv(self.horse_table_path, index=False, encoding='utf-8-sig')
    
    def get_race_ids(self) -> List[str]:
        """保存済みの全レースIDを取得"""
        if not self.race_table_path.exists():
            return []
        try:
            df = pd.read_csv(self.race_table_path, encoding='utf-8-sig')
            return df['race_id'].unique().tolist()
        except Exception as e:
            logger.warning(f"レースID取得エラー: {e}")
            return []
    
    def export_for_ai(self, race_id: str, output_dir: str = "data/json") -> Optional[str]:
        """
        AI用にJSON形式でエクスポート
        
        Args:
            race_id: レースID
            output_dir: 出力ディレクトリ
            
        Returns:
            出力ファイルパス（失敗時None）
        """
        try:
            # CSVからデータを読み込んでJSON形式に変換
            race_df = pd.read_csv(self.race_table_path, encoding='utf-8-sig')
            race_row = race_df[race_df['race_id'] == race_id]
            
            if len(race_row) == 0:
                logger.warning(f"レースIDが見つかりません: {race_id}")
                return None
            
            horse_df = pd.read_csv(self.horse_table_path, encoding='utf-8-sig')
            horses = horse_df[horse_df['race_id'] == race_id].to_dict('records')
            
            # JSON形式に整形
            json_data = {
                'race_id': race_id,
                'race_name': race_row.iloc[0]['race_name'],
                'race_grade': race_row.iloc[0]['race_grade'],
                'distance': race_row.iloc[0]['distance'],
                'horses': horses
            }
            
            # 出力ディレクトリを作成
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # JSONファイルに保存
            json_file = output_path / f"{race_id}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"AI用JSONをエクスポート: {json_file}")
            return str(json_file)
            
        except Exception as e:
            logger.error(f"JSONエクスポートエラー: {e}")
            return None

