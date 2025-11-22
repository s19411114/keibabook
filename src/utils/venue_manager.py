"""
会場管理機能
南関4会場とその他会場の管理
"""
from typing import Dict, List, Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)


class VenueManager:
    """会場管理クラス"""
    
    # 南関4会場
    MINAMI_KANTO_VENUES = {
        "大井": "oai",
        "川崎": "kawasaki",
        "船橋": "funabashi",
        "浦和": "urawa"
    }
    
    # その他会場（たまに開催される重賞レース会場）
    OTHER_VENUES = {
        "門別": "monbetsu",
        "盛岡": "morioka",
        "名古屋": "nagoya",
        "園田": "sonoda",
        "金沢": "kanazawa",
        "高知": "kochi",
        "佐賀": "saga",
        "荒尾": "arao"
    }
    
    # 全会場
    ALL_VENUES = {**MINAMI_KANTO_VENUES, **OTHER_VENUES}
    
    @classmethod
    def get_venue_code(cls, venue_name: str) -> Optional[str]:
        """
        会場名から会場コードを取得
        
        Args:
            venue_name: 会場名
            
        Returns:
            会場コード（見つからない場合はNone）
        """
        return cls.ALL_VENUES.get(venue_name)
    
    @classmethod
    def is_minami_kanto(cls, venue_name: str) -> bool:
        """
        南関4会場かチェック
        
        Args:
            venue_name: 会場名
            
        Returns:
            南関4会場の場合True
        """
        return venue_name in cls.MINAMI_KANTO_VENUES
    
    @classmethod
    def get_minami_kanto_venues(cls) -> List[str]:
        """南関4会場のリストを取得"""
        return list(cls.MINAMI_KANTO_VENUES.keys())
    
    @classmethod
    def get_other_venues(cls) -> List[str]:
        """その他会場のリストを取得"""
        return list(cls.OTHER_VENUES.keys())
    
    @classmethod
    def get_all_venues(cls) -> List[str]:
        """全会場のリストを取得"""
        return list(cls.ALL_VENUES.keys())
    
    @classmethod
    def build_url(cls, venue_name: str, race_id: str, page_type: str = "syutuba") -> Optional[str]:
        """
        URLを構築
        
        Args:
            venue_name: 会場名
            race_id: レースID
            page_type: ページタイプ（syutuba, seiseki, cyokyo, kettou等）
            
        Returns:
            URL（構築できない場合はNone）
        """
        venue_code = cls.get_venue_code(venue_name)
        if not venue_code:
            logger.warning(f"会場コードが見つかりません: {venue_name}")
            return None
        
        # URL構造は実際のサイト構造に応じて調整が必要
        # 南関4会場とその他会場でURL構造が異なる可能性がある
        if cls.is_minami_kanto(venue_name):
            # 南関4会場の場合
            base_url = "https://s.keibabook.co.jp/chihou"
        else:
            # その他会場の場合
            base_url = "https://s.keibabook.co.jp/chihou"
        
        # ページタイプに応じたURLを構築
        if page_type == "syutuba":
            return f"{base_url}/syutuba/{race_id}"
        elif page_type == "seiseki":
            return f"{base_url}/seiseki/{race_id}"
        elif page_type == "cyokyo":
            return f"{base_url}/cyokyo/0/{race_id}"
        elif page_type == "kettou":
            return f"{base_url}/kettou/{race_id}"
        elif page_type == "point":
            return f"{base_url}/point/{race_id}"
        else:
            return f"{base_url}/{page_type}/{race_id}"

