"""
調教データ取得とタイム変換のテスト
ブラウザでHTMLレポートを確認できる
"""
import asyncio
import json
from src.utils.config import load_settings
from src.scrapers.keibabook import KeibaBookScraper
from src.utils.logger import get_logger

logger = get_logger(__name__)

async def test_training_data():
    """調教データを取得してタイム変換をテスト"""
    
    # 設定をロード
    settings = load_settings()
    
    # テスト用レースID（東京11R ジャパンC）
    race_id = "2025113004"
    
    # スクレイパー設定
    scraper_settings = {
        'race_id': race_id,
        'shutuba_url': f'https://s.keibabook.co.jp/cyuou/cyokyo/{race_id}',  # 調教ページ
        'race_type': 'jra',
        'skip_duplicate_check': True,  # 重複チェックをスキップ
        'cookie_file': settings.get('cookie_file', 'cookies.json'),
        'login_id': settings.get('login_id'),
        'login_password': settings.get('login_password'),
        'playwright_headless': False,  # ブラウザを表示
        'playwright_timeout': 120000,  # 2分に延長
        'playwright_wait_until': 'domcontentloaded',  # networkidleではなくdomcontentloaded
        'rate_limit_base': 0.5,
        'perf': True
    }
    
    # スクレイパーを実行
    scraper = KeibaBookScraper(scraper_settings)
    
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # ブラウザを表示
            context = await browser.new_context()
            page = await context.new_page()
            
            logger.info(f"調教データ取得開始: {race_id}")
            
            # ログイン確保
            from src.utils.login import KeibaBookLogin
            login_ok = await KeibaBookLogin.ensure_logged_in(
                context, 
                scraper_settings['login_id'], 
                scraper_settings['login_password'], 
                cookie_file=scraper_settings['cookie_file'], 
                save_cookies=True, 
                test_url=scraper_settings['shutuba_url'],
                page=page
            )
            
            if not login_ok:
                logger.error("ログイン失敗")
                return
            
            logger.info("ログイン成功")
            
            # 調教ページに移動
            logger.info(f"調教ページに移動: {scraper_settings['shutuba_url']}")
            await page.goto(scraper_settings['shutuba_url'], wait_until='domcontentloaded', timeout=120000)
            
            # ページが完全に読み込まれるまで待機
            await page.wait_for_timeout(3000)
            
            html_content = await page.content()
            
            # デバッグ用にHTMLを保存
            debug_file = f"debug_training_{race_id}.html"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"デバッグHTML保存: {debug_file}")
            
            # 調教データをパース（タイム変換含む）
            training_data = scraper._parse_training_data(html_content)
            
            # HTMLレポートを生成
            html_report = generate_html_report(training_data, race_id)
            
            # HTMLファイルに保存
            report_file = f"training_report_{race_id}.html"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(html_report)
            
            logger.info(f"HTMLレポート保存: {report_file}")
            
            # JSONファイルにも保存
            json_file = f"training_data_{race_id}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(training_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"JSON保存: {json_file}")
            
            # ブラウザでHTMLレポートを開く
            import os
            report_path = os.path.abspath(report_file)
            await page.goto(f"file:///{report_path}")
            
            logger.info("ブラウザでレポートを確認してください（Enterキーで終了）")
            input()
            
            await browser.close()
            
    except Exception as e:
        logger.error(f"エラー: {e}", exc_info=True)

def generate_html_report(training_data, race_id):
    """調教データからHTMLレポートを生成"""
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>調教データレポート - {race_id}</title>
        <style>
            body {{
                font-family: 'Yu Gothic', 'Meiryo', sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
            }}
            h1 {{
                color: #333;
                border-bottom: 3px solid #4CAF50;
                padding-bottom: 10px;
            }}
            .horse-card {{
                background: white;
                margin: 20px 0;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .horse-header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 15px;
            }}
            .horse-num {{
                font-size: 24px;
                font-weight: bold;
                display: inline-block;
                margin-right: 15px;
            }}
            .horse-name {{
                font-size: 20px;
                display: inline-block;
            }}
            .tanpyo {{
                margin-top: 10px;
                font-size: 14px;
                background: rgba(255,255,255,0.2);
                padding: 8px;
                border-radius: 3px;
            }}
            .training-detail {{
                background: #f9f9f9;
                margin: 15px 0;
                padding: 15px;
                border-left: 4px solid #4CAF50;
                border-radius: 3px;
            }}
            .detail-header {{
                font-weight: bold;
                color: #555;
                margin-bottom: 10px;
                display: flex;
                justify-content: space-between;
            }}
            .times {{
                margin: 10px 0;
            }}
            .time-item {{
                display: inline-block;
                margin: 5px 10px 5px 0;
                padding: 8px 12px;
                background: white;
                border-radius: 5px;
                border: 1px solid #ddd;
            }}
            .time-converted {{
                color: #4CAF50;
                font-weight: bold;
                font-size: 16px;
            }}
            .time-original {{
                color: #999;
                font-size: 14px;
                margin-left: 5px;
            }}
            .position {{
                color: #FF6B6B;
                font-size: 14px;
                margin-left: 3px;
            }}
            .awase {{
                margin: 10px 0;
                padding: 8px;
                background: #E3F2FD;
                border-radius: 3px;
                font-size: 14px;
            }}
            .comment {{
                margin: 10px 0;
                padding: 10px;
                background: #FFF9C4;
                border-radius: 3px;
                font-size: 14px;
                line-height: 1.6;
            }}
            .legend {{
                background: white;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 20px;
            }}
            .legend-item {{
                display: inline-block;
                margin-right: 20px;
                font-size: 14px;
            }}
            .conversion-info {{
                background: #E8F5E9;
                padding: 10px;
                border-radius: 3px;
                margin-top: 5px;
                font-size: 13px;
                color: #2E7D32;
            }}
        </style>
    </head>
    <body>
        <h1>🏇 調教データレポート - {race_id}</h1>
        
        <div class="legend">
            <strong>📊 表示説明:</strong><br>
            <div class="legend-item">🟢 <span class="time-converted">緑字</span> = 変換後タイム（共通基準）</div>
            <div class="legend-item">⚫ <span class="time-original">灰字</span> = 元のタイム</div>
            <div class="legend-item">🔴 <span class="position">[n]</span> = 枠位置</div>
            <div class="legend-item">📘 青背景 = 併せ馬</div>
            <div class="legend-item">📒 黄背景 = コメント</div>
        </div>
    """
    
    # 馬ごとにカードを生成
    for horse_num in sorted(training_data.keys(), key=lambda x: int(x) if x.isdigit() else 999):
        horse = training_data[horse_num]
        
        html += f"""
        <div class="horse-card">
            <div class="horse-header">
                <div>
                    <span class="horse-num">🐴 {horse_num}番</span>
                    <span class="horse-name">{horse.get('horse_name', '不明')}</span>
                </div>
                {f'<div class="tanpyo">💬 短評: {horse.get("tanpyo", "")}</div>' if horse.get('tanpyo') else ''}
            </div>
        """
        
        # 調教詳細
        for detail in horse.get('details', []):
            date_location = detail.get('date_location', '')
            oikiri = detail.get('追い切り方', '')
            
            html += f"""
            <div class="training-detail">
                <div class="detail-header">
                    <span>📅 {date_location}</span>
                    <span>⚡ {oikiri}</span>
                </div>
            """
            
            # タイム表示（変換後と元のタイム）
            times_converted = detail.get('times_converted', [])
            times_original = detail.get('times', [])
            positions = detail.get('positions', [])
            
            if times_converted:
                html += '<div class="times">🕐 '
                for i, time_conv in enumerate(times_converted):
                    time_orig = times_original[i] if i < len(times_original) else ''
                    position = positions[i] if i < len(positions) else ''
                    
                    # 変換されているかチェック
                    is_converted = time_conv != time_orig
                    
                    html += f"""
                    <span class="time-item">
                        <span class="time-converted">{time_conv}</span>
                        {f'<span class="time-original">({time_orig})</span>' if is_converted else ''}
                        {f'<span class="position">{position}</span>' if position else ''}
                    </span>
                    """
                html += '</div>'
            
            # 変換情報
            training_center = detail.get('training_center', '')
            course = detail.get('course', '')
            if training_center and course:
                html += f'<div class="conversion-info">✅ 変換基準: {training_center}{course}コース → 美浦南W換算</div>'
            
            # 併せ馬
            awase = detail.get('awase', '')
            if awase:
                html += f'<div class="awase">🐎 併せ: {awase}</div>'
            
            # コメント
            comment = detail.get('comment', '')
            if comment:
                html += f'<div class="comment">💭 {comment}</div>'
            
            html += '</div>'
        
        html += '</div>'
    
    html += """
    </body>
    </html>
    """
    
    return html

if __name__ == "__main__":
    asyncio.run(test_training_data())
