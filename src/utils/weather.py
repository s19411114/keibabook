"""
天気予報取得モジュール
OpenWeatherMap APIで競馬場のピンポイント気温を取得
"""
import os
import json
import asyncio
import aiohttp
from datetime import datetime, timedelta
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger(__name__)

# 競馬場の緯度経度（ピンポイント）
VENUE_COORDINATES = {
    # 中央競馬 (JRA)
    "東京": {"lat": 35.6644, "lon": 139.4794, "name": "東京競馬場"},
    "中山": {"lat": 35.7267, "lon": 139.9567, "name": "中山競馬場"},
    "阪神": {"lat": 34.7589, "lon": 135.3606, "name": "阪神競馬場"},
    "京都": {"lat": 34.9131, "lon": 135.7139, "name": "京都競馬場"},
    "中京": {"lat": 35.0556, "lon": 137.0222, "name": "中京競馬場"},
    "小倉": {"lat": 33.8833, "lon": 130.8333, "name": "小倉競馬場"},
    "新潟": {"lat": 37.8611, "lon": 139.0056, "name": "新潟競馬場"},
    "福島": {"lat": 37.7678, "lon": 140.4256, "name": "福島競馬場"},
    "札幌": {"lat": 43.0525, "lon": 141.4069, "name": "札幌競馬場"},
    "函館": {"lat": 41.7792, "lon": 140.7656, "name": "函館競馬場"},
    
    # 地方競馬 (NAR) - 南関東
    "大井": {"lat": 35.5922, "lon": 139.7467, "name": "大井競馬場"},
    "川崎": {"lat": 35.5256, "lon": 139.7128, "name": "川崎競馬場"},
    "船橋": {"lat": 35.6939, "lon": 139.9811, "name": "船橋競馬場"},
    "浦和": {"lat": 35.8556, "lon": 139.6394, "name": "浦和競馬場"},
    
    # 地方競馬 (NAR) - その他主要場
    "門別": {"lat": 42.4667, "lon": 141.7833, "name": "門別競馬場"},
    "盛岡": {"lat": 39.7667, "lon": 141.1167, "name": "盛岡競馬場"},
    "水沢": {"lat": 39.0667, "lon": 141.1333, "name": "水沢競馬場"},
    "金沢": {"lat": 36.5833, "lon": 136.6833, "name": "金沢競馬場"},
    "笠松": {"lat": 35.3667, "lon": 136.7667, "name": "笠松競馬場"},
    "名古屋": {"lat": 35.0500, "lon": 136.9500, "name": "名古屋競馬場"},
    "園田": {"lat": 34.7500, "lon": 135.4167, "name": "園田競馬場"},
    "姫路": {"lat": 34.8333, "lon": 134.7000, "name": "姫路競馬場"},
    "高知": {"lat": 33.5500, "lon": 133.5333, "name": "高知競馬場"},
    "佐賀": {"lat": 33.2833, "lon": 130.3000, "name": "佐賀競馬場"},
    "帯広": {"lat": 42.9167, "lon": 143.2000, "name": "帯広競馬場"},
}


class WeatherFetcher:
    """OpenWeatherMap APIで天気情報を取得"""
    
    API_URL = "https://api.openweathermap.org/data/2.5/weather"
    FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"  # 3時間ごと5日間予報
    
    def __init__(self, api_key: str = None):
        """
        Args:
            api_key: OpenWeatherMap APIキー。Noneの場合は環境変数から取得
        """
        self.api_key = api_key or os.environ.get("OPENWEATHER_API_KEY", "")
        if not self.api_key:
            logger.warning("OpenWeatherMap APIキーが設定されていません。環境変数 OPENWEATHER_API_KEY を設定してください。")
    
    async def fetch_weather(self, venue: str) -> dict:
        """
        競馬場の現在の天気情報を取得
        
        Args:
            venue: 競馬場名（例: "福島", "東京", "浦和"）
        
        Returns:
            天気情報辞書 {
                "venue": "福島",
                "timestamp": "2025-11-26T14:30:00",
                "temperature": 12.5,
                "feels_like": 10.2,
                "humidity": 65,
                "weather": "曇り",
                "weather_code": "04d",
                "wind_speed": 3.5,
                "wind_deg": 180,
                "pressure": 1015
            }
        """
        if not self.api_key:
            return {"error": "APIキー未設定", "venue": venue}
        
        coord = VENUE_COORDINATES.get(venue)
        if not coord:
            logger.warning(f"競馬場 '{venue}' の座標が未登録です")
            return {"error": f"座標未登録: {venue}", "venue": venue}
        
        params = {
            "lat": coord["lat"],
            "lon": coord["lon"],
            "appid": self.api_key,
            "units": "metric",  # 摂氏
            "lang": "ja"  # 日本語
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.API_URL, params=params, timeout=10) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error(f"天気API エラー ({resp.status}): {error_text}")
                        return {"error": f"API error: {resp.status}", "venue": venue}
                    
                    data = await resp.json()
            
            # レスポンスをパース
            weather_info = {
                "venue": venue,
                "venue_name": coord["name"],
                "lat": coord["lat"],
                "lon": coord["lon"],
                "timestamp": datetime.now().isoformat(),
                "forecast_time": None,  # 現在天気の場合はNone
                "temperature": data.get("main", {}).get("temp"),
                "feels_like": data.get("main", {}).get("feels_like"),
                "humidity": data.get("main", {}).get("humidity"),
                "pressure": data.get("main", {}).get("pressure"),
                "weather": data.get("weather", [{}])[0].get("description", ""),
                "weather_code": data.get("weather", [{}])[0].get("icon", ""),
                "wind_speed": data.get("wind", {}).get("speed"),
                "wind_deg": data.get("wind", {}).get("deg"),
            }
            
            logger.info(f"天気取得成功: {venue} - {weather_info['temperature']}℃ ({weather_info['weather']})")
            return weather_info
            
        except asyncio.TimeoutError:
            logger.error(f"天気API タイムアウト: {venue}")
            return {"error": "タイムアウト", "venue": venue}
        best = None
        best_diff = float('inf')
        
        with open(self.db_path, 'r', encoding='utf-8') as f:
            next(f)  # ヘッダースキップ
            for line in f:
                parts = line.strip().split(",")
                if len(parts) >= 8 and parts[0] == date and parts[2] == venue:
                    time_parts = parts[1].split(":")
                    if len(time_parts) == 2:
                        record_minutes = int(time_parts[0]) * 60 + int(time_parts[1])
                        diff = abs(record_minutes - target_minutes)
                        if diff < best_diff and diff <= tolerance_minutes:
                            best_diff = diff
                            best = {
                                "date": parts[0],
                                "time": parts[1],
                                "venue": parts[2],
                                "temperature": float(parts[3]) if parts[3] else None,
                                "feels_like": float(parts[4]) if parts[4] else None,
                                "humidity": int(parts[5]) if parts[5] else None,
                                "weather": parts[6],
                                "wind_speed": float(parts[7]) if parts[7] else None,
                            }
        
        return best


async def update_weather_for_venues(venues: list, api_key: str = None) -> dict:
    """
    複数競馬場の天気を取得してDBに保存
    
    Args:
        venues: 競馬場名リスト
        api_key: APIキー（省略時は環境変数）
    
    Returns:
        {venue: weather_info, ...}
    """
    fetcher = WeatherFetcher(api_key)
    db = WeatherDB()
    
    weather_map = await fetcher.fetch_multiple_venues(venues)
    
    for venue, info in weather_map.items():
        if "error" not in info:
            db.save(info)
    
    return weather_map


# CLI実行用
if __name__ == "__main__":
    import sys
    
    venues = sys.argv[1:] if len(sys.argv) > 1 else ["東京", "中山", "阪神"]
    print(f"天気取得: {venues}")
    
    result = asyncio.run(update_weather_for_venues(venues))
    for venue, info in result.items():
        if "error" in info:
            print(f"  {venue}: エラー - {info['error']}")
        else:
            print(f"  {venue}: {info['temperature']}℃ ({info['weather']})")
