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


    @staticmethod
    def _is_low_traffic_time() -> bool:
        """現在がアクセスが少ない時間帯かチェック"""
        current_hour = datetime.now().hour
        return current_hour in RateLimiter.LOW_TRAFFIC_HOURS
    
    @staticmethod
    def is_low_traffic_time() -> bool:
        """現在がアクセスが少ない時間帯かチェック（外部から呼び出し用）"""
        return RateLimiter._is_low_traffic_time()

