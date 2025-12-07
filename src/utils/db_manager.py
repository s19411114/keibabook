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
        self.schedule_table_path = self.db_dir / "schedules.csv"  # スケジュールテーブル追加
        self.track_bias_table_path = self.db_dir / "track_bias_history.csv"  # トラックバイアス履歴テーブル
        
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
        
        # スケジュールテーブル（新規追加）
        if not self.schedule_table_path.exists():
            pd.DataFrame(columns=[
                'date', 'venue', 'race_type', 'race_num', 'race_time', 
                'race_id', 'created_at', 'updated_at'
            ]).to_csv(self.schedule_table_path, index=False, encoding='utf-8-sig')
        
        # トラックバイアス履歴テーブル（新規追加）
        if not self.track_bias_table_path.exists():
            pd.DataFrame(columns=[
                'race_id', 'race_name', 'venue', 'date', 'distance', 'track_condition',
                'bias_type', 'overall_bias_score', 'confidence',
                'inner_lane_score', 'outer_lane_score',
                'front_runner_score', 'closer_score',
                'created_at', 'updated_at'
            ]).to_csv(self.track_bias_table_path, index=False, encoding='utf-8-sig')
    
    def is_url_fetched(self, url: str, max_age_seconds: Optional[int] = None) -> bool:
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
            rows = df[df['url'] == url]
            if len(rows) == 0:
                return False
            if max_age_seconds is None or max_age_seconds == 0:
                return True
            # Check the most recent fetched_at
            try:
                latest = rows.sort_values('fetched_at', ascending=False).iloc[0]
                fetched_at = datetime.fromisoformat(latest['fetched_at'])
                age = (datetime.now() - fetched_at).total_seconds()
                return age <= max_age_seconds
            except Exception:
                # Fallback: if parsing fails, treat as fetched to avoid extra fetches
                return True
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
            # 明示的にデータ型を変換してFutureWarning回避
            for key, value in race_row.items():
                if value == '':
                    value = None  # 空文字をNoneに変換
                race_df.loc[race_df['race_id'] == race_id, key] = value
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
                # 明示的にデータ型を変換してFutureWarning回避
                for key, value in horse_row.items():
                    if value == '':
                        value = None  # 空文字をNoneに変換
                    horse_df.loc[
                        (horse_df['race_id'] == race_id) & (horse_df['horse_num'] == horse_num),
                        key
                    ] = value
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
    
    def is_race_fetched(self, race_id: str, max_age_seconds: Optional[int] = None) -> bool:
        """
        指定されたレースIDのデータが取得済みかチェック
        
        Args:
            race_id: レースID
            max_age_seconds: 指定した秒数以内に取得された場合はTrueを返す（Noneは無効）
            
        Returns:
            取得済みの場合True
        """
        if not self.url_log_path.exists():
            return False
        
        try:
            df = pd.read_csv(self.url_log_path, encoding='utf-8-sig')
            # 出馬表ページで成功したもののみを対象
            rows = df[(df['race_id'] == race_id) & (df['page_type'] == 'shutuba') & (df['status'] == 'success')]
            if len(rows) == 0:
                return False
            if max_age_seconds is None or max_age_seconds == 0:
                return True
            try:
                latest = rows.sort_values('fetched_at', ascending=False).iloc[0]
                fetched_at = datetime.fromisoformat(latest['fetched_at'])
                age = (datetime.now() - fetched_at).total_seconds()
                return age <= max_age_seconds
            except Exception:
                # 解析失敗時は fetched とみなす（保守的）
                return True
        except Exception as e:
            logger.warning(f"レース取得状況確認エラー: {e}")
            return False
    
    def get_fetched_races_for_date(self, date_str: str, race_type: str = 'jra') -> Dict[str, List[int]]:
        """
        指定日付の取得済みレース情報を取得
        
        Args:
            date_str: 日付文字列（YYYYMMDD形式）
            race_type: 'jra' or 'nar'
            
        Returns:
            会場ごとの取得済みレース番号の辞書
            例: {"東京": [1, 2, 3], "中山": [1]}
        """
        result = {}
        
        if not self.url_log_path.exists():
            return result
        
        try:
            df = pd.read_csv(self.url_log_path, encoding='utf-8-sig')
            # 出馬表ページで成功したもののみ
            success_df = df[(df['page_type'] == 'shutuba') & (df['status'] == 'success')]
            
            for _, row in success_df.iterrows():
                race_id = str(row['race_id'])
                # race_idから日付を抽出（先頭8文字）
                if len(race_id) >= 8 and race_id[:8] == date_str:
                    # race_idから会場コードとレース番号を抽出
                    # フォーマット: YYYYMMDDVVNN （日付8桁 + 会場2桁 + レース番号2桁）
                    if len(race_id) >= 12:
                        venue_code = race_id[8:10]
                        race_num = int(race_id[10:12])
                        
                        # 会場コードを会場名に変換
                        venue_name = self._venue_code_to_name(venue_code, race_type)
                        
                        if venue_name not in result:
                            result[venue_name] = []
                        if race_num not in result[venue_name]:
                            result[venue_name].append(race_num)
            
            # ソート
            for venue in result:
                result[venue].sort()
            
            return result
        except Exception as e:
            logger.warning(f"取得済みレース情報取得エラー: {e}")
            return result
    
    def _venue_code_to_name(self, code: str, race_type: str) -> str:
        """会場コードを会場名に変換"""
        jra_codes = {
            "01": "札幌", "02": "函館", "03": "福島", "04": "新潟",
            "05": "東京", "06": "中山", "07": "中京", "08": "京都",
            "09": "阪神", "10": "小倉"
        }
        nar_codes = {
            "36": "大井", "37": "川崎", "38": "船橋", "39": "浦和",
            "40": "金沢", "41": "名古屋", "42": "園田", "43": "姫路",
            "44": "福山", "45": "高知", "46": "佐賀", "47": "荒尾",
            "48": "水沢", "49": "盛岡", "50": "門別", "51": "帯広"
        }
        
        if race_type == 'nar':
            return nar_codes.get(code, code)
        else:
            return jra_codes.get(code, code)
    
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
    
    def save_schedule(self, schedule_data: List[Dict[str, Any]], target_date: str):
        """
        スケジュールデータをCSVに保存
        
        Args:
            schedule_data: スケジュールリスト [{'venue': '東京', 'races': [...]}, ...]
            target_date: 対象日付 (YYYY-MM-DD形式)
        """
        try:
            # 既存データを読み込み
            if self.schedule_table_path.exists():
                df = pd.read_csv(self.schedule_table_path, encoding='utf-8-sig')
            else:
                df = pd.DataFrame(columns=[
                    'date', 'venue', 'race_type', 'race_num', 'race_time', 
                    'race_id', 'created_at', 'updated_at'
                ])
            
            # 新規レコードを作成
            new_records = []
            now = datetime.now().isoformat()
            
            for venue_data in schedule_data:
                venue = venue_data.get('venue', '不明')
                race_type = venue_data.get('race_type', 'unknown')
                races = venue_data.get('races', [])
                
                for race in races:
                    race_num = race.get('race_num', 0)
                    race_time = race.get('time', '')
                    race_id = race.get('race_id', '')
                    
                    # 重複チェック（同じ日付・会場・レース番号）
                    existing = df[
                        (df['date'] == target_date) & 
                        (df['venue'] == venue) & 
                        (df['race_num'] == race_num)
                    ]
                    
                    if len(existing) == 0:
                        new_records.append({
                            'date': target_date,
                            'venue': venue,
                            'race_type': race_type,
                            'race_num': race_num,
                            'race_time': race_time,
                            'race_id': race_id,
                            'created_at': now,
                            'updated_at': now
                        })
            
            # 新規レコードを追加
            if new_records:
                new_df = pd.DataFrame(new_records)
                df = pd.concat([df, new_df], ignore_index=True)
                df.to_csv(self.schedule_table_path, index=False, encoding='utf-8-sig')
                logger.info(f"✅ スケジュール保存完了: {len(new_records)}件追加")
            else:
                logger.info("ℹ️ 新規スケジュールなし（全て既存データ）")
                
        except Exception as e:
            logger.error(f"スケジュール保存エラー: {e}", exc_info=True)

    def save_track_bias(self, race_id: str, bias_data: Dict[str, Any], race_info: Dict[str, Any]):
        """
        トラックバイアスデータをCSVに保存
        
        Args:
            race_id: レースID
            bias_data: トラックバイアス指数データ（track_bias.pyの出力）
            race_info: レース基本情報（race_name, venue, date, distance, track_condition）
        """
        try:
            # 既存データを読み込み
            if self.track_bias_table_path.exists():
                df = pd.read_csv(self.track_bias_table_path, encoding='utf-8-sig')
            else:
                df = pd.DataFrame(columns=[
                    'race_id', 'race_name', 'venue', 'date', 'distance', 'track_condition',
                    'bias_type', 'overall_bias_score', 'confidence',
                    'inner_lane_score', 'outer_lane_score',
                    'front_runner_score', 'closer_score',
                    'created_at', 'updated_at'
                ])
            
            # 重複チェック（同じrace_idが既に存在する場合は更新）
            now = datetime.now().isoformat()
            existing_index = df[df['race_id'] == race_id].index
            
            new_record = {
                'race_id': race_id,
                'race_name': race_info.get('race_name', ''),
                'venue': race_info.get('venue', ''),
                'date': race_info.get('date', ''),
                'distance': race_info.get('distance', ''),
                'track_condition': race_info.get('track_condition', ''),
                'bias_type': bias_data.get('bias_type', ''),
                'overall_bias_score': bias_data.get('overall_bias_score', 0.0),
                'confidence': bias_data.get('confidence', 0.0),
                'inner_lane_score': bias_data.get('inner_lane_score', 0.0),
                'outer_lane_score': bias_data.get('outer_lane_score', 0.0),
                'front_runner_score': bias_data.get('front_runner_score', 0.0),
                'closer_score': bias_data.get('closer_score', 0.0),
                'created_at': now if len(existing_index) == 0 else df.loc[existing_index[0], 'created_at'],
                'updated_at': now
            }
            
            if len(existing_index) > 0:
                # 既存レコードを更新
                for col, val in new_record.items():
                    df.loc[existing_index[0], col] = val
                logger.info(f"✅ トラックバイアス更新: {race_id}")
            else:
                # 新規レコード追加
                new_df = pd.DataFrame([new_record])
                df = pd.concat([df, new_df], ignore_index=True)
                logger.info(f"✅ トラックバイアス保存: {race_id}")
            
            # CSVに保存
            df.to_csv(self.track_bias_table_path, index=False, encoding='utf-8-sig')
                
        except Exception as e:
            logger.error(f"トラックバイアス保存エラー: {e}", exc_info=True)
    
    def get_track_bias_history(self, venue: Optional[str] = None, days: int = 30) -> List[Dict[str, Any]]:
        """
        トラックバイアス履歴を取得（アーカイブとして活用）
        
        Args:
            venue: 会場名でフィルタ（Noneの場合は全会場）
            days: 過去何日分取得するか
            
        Returns:
            トラックバイアス履歴のリスト
        """
        try:
            if not self.track_bias_table_path.exists():
                return []
            
            df = pd.read_csv(self.track_bias_table_path, encoding='utf-8-sig')
            
            # 会場フィルタ
            if venue:
                df = df[df['venue'] == venue]
            
            # 日付フィルタ（過去N日）
            if 'date' in df.columns:
                cutoff_date = (datetime.now() - pd.Timedelta(days=days)).strftime('%Y-%m-%d')
                df = df[df['date'] >= cutoff_date]
            
            # 日付降順でソート
            if 'date' in df.columns:
                df = df.sort_values('date', ascending=False)
            
            # 辞書リストに変換
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"トラックバイアス履歴取得エラー: {e}")
            return []
