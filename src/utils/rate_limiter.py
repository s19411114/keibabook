"""
レート制御機能
サイト負担を軽減するための待機時間管理
"""
import asyncio
import random
from datetime import datetime, time
from typing import Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """レート制御クラス（見えない心遣い）"""
    
    # アクセスが少ない時間帯（深夜〜早朝）
    LOW_TRAFFIC_HOURS = list(range(0, 6)) + list(range(23, 24))
    
    # 通常の待機時間（秒）
    DEFAULT_DELAY = 10
    LOW_TRAFFIC_DELAY = 3
    
    def __init__(self, base_delay: Optional[float] = None):
        """
        Args:
            base_delay: 基本待機時間（秒）。Noneの場合は自動判定
        """
        self.base_delay = base_delay
    
    async def wait(self, randomize: bool = True):
        """
        レート制御: 待機時間を設定
        
        Args:
            randomize: ランダムな待機時間を追加するか
        """
        if self.base_delay is None:
            # 時間帯に応じて自動判定
            current_hour = datetime.now().hour
            if current_hour in self.LOW_TRAFFIC_HOURS:
                base_delay = self.LOW_TRAFFIC_DELAY
            else:
                base_delay = self.DEFAULT_DELAY
        else:
            base_delay = self.base_delay
        
        if randomize:
            # ランダムな待機時間（±50%のばらつき）
            random_factor = random.uniform(0.5, 1.5)
            delay = base_delay * random_factor
        else:
            delay = base_delay
        
        logger.debug(f"レート制御: {delay:.1f}秒待機（時間帯考慮: {self._is_low_traffic_time()}）")
        await asyncio.sleep(delay)
    
    @staticmethod
    def _is_low_traffic_time() -> bool:
        """現在がアクセスが少ない時間帯かチェック"""
        current_hour = datetime.now().hour
        return current_hour in RateLimiter.LOW_TRAFFIC_HOURS
    
    @staticmethod
    def is_low_traffic_time() -> bool:
        """現在がアクセスが少ない時間帯かチェック（外部から呼び出し用）"""
        return RateLimiter._is_low_traffic_time()

