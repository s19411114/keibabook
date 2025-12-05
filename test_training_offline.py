"""
既存の調教HTMLファイルからタイム変換をテスト
"""
import json
from src.scrapers.keibabook import KeibaBookScraper
from src.utils.config import load_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

def test_with_existing_html():
    """既存のHTMLファイルを使って調教データパースとタイム変換をテスト"""
    
    # 既存のHTMLファイル
    html_file = "debug_files/debug_training_20251124_tokyo11R.html"
    race_id = "20251124_tokyo11R"
    
    logger.info(f"HTMLファイル読み込み: {html_file}")
    
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # スクレイパー設定（ダミー）
    settings = {
        'race_id': race_id,
        'shutuba_url': '',
        'race_type': 'jra',
        'skip_duplicate_check': True,
        'perf': False
    }
    
    scraper = KeibaBookScraper(settings)
    
    # 調教データをパース（タイム変換含む）
    logger.info("調教データをパース中...")
    training_data = scraper._parse_training_data(html_content)
    
    # 結果を表示
    logger.info(f"取得した馬の数: {len(training_data)}")
    
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
    
    # サンプル表示（最初の馬）
    if training_data:
        horse_num = list(training_data.keys())[0]
        horse = training_data[horse_num]
        logger.info(f"\n=== サンプル: {horse_num}番 {horse.get('horse_name', '不明')} ===")
        logger.info(f"短評: {horse.get('tanpyo', '')}")
        
        for i, detail in enumerate(horse.get('details', []), 1):
            logger.info(f"\n  調教{i}: {detail.get('date_location', '')} {detail.get('追い切り方', '')}")
            
            times_converted = detail.get('times_converted', [])
            times_original = detail.get('times', [])
            positions = detail.get('positions', [])
            
            time_display = []
            for j in range(len(times_converted)):
                conv = times_converted[j] if j < len(times_converted) else ''
                orig = times_original[j] if j < len(times_original) else ''
                pos = positions[j] if j < len(positions) else ''
                
                if conv != orig:
                    time_display.append(f"{conv}{pos}({orig})")
                else:
                    time_display.append(f"{conv}{pos}")
            
            logger.info(f"  タイム: {' - '.join(time_display)}")
            
            if detail.get('training_center'):
                logger.info(f"  変換: {detail.get('training_center', '')}{detail.get('course', '')}コース → 美浦南W換算")
            
            if detail.get('awase'):
                logger.info(f"  併せ: {detail.get('awase', '')}")
            
            if detail.get('comment'):
                logger.info(f"  コメント: {detail.get('comment', '')}")
    
    # ブラウザで開く
    import webbrowser
    import os
    report_path = os.path.abspath(report_file)
    logger.info(f"\nブラウザで開きます: {report_path}")
    webbrowser.open(f"file:///{report_path}")

def generate_html_report(training_data, race_id):
    """調教データからHTMLレポートを生成"""
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🏇 調教データレポート - {race_id}</title>
        <style>
            body {{
                font-family: 'Yu Gothic', 'Meiryo', sans-serif;
                margin: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            }}
            h1 {{
                color: #333;
                border-bottom: 4px solid #667eea;
                padding-bottom: 15px;
                margin-bottom: 30px;
                font-size: 28px;
            }}
            .legend {{
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 30px;
                border-left: 5px solid #667eea;
            }}
            .legend-title {{
                font-weight: bold;
                font-size: 18px;
                margin-bottom: 15px;
                color: #333;
            }}
            .legend-items {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 10px;
            }}
            .legend-item {{
                padding: 8px;
                background: white;
                border-radius: 5px;
                font-size: 14px;
            }}
            .horse-card {{
                background: white;
                margin: 25px 0;
                padding: 0;
                border-radius: 12px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                overflow: hidden;
                border: 2px solid #e0e0e0;
                transition: transform 0.2s, box-shadow 0.2s;
            }}
            .horse-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 8px 25px rgba(0,0,0,0.15);
            }}
            .horse-header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px 25px;
            }}
            .horse-num {{
                font-size: 28px;
                font-weight: bold;
                display: inline-block;
                margin-right: 15px;
                background: rgba(255,255,255,0.2);
                padding: 5px 15px;
                border-radius: 8px;
            }}
            .horse-name {{
                font-size: 22px;
                display: inline-block;
                vertical-align: middle;
            }}
            .tanpyo {{
                margin-top: 12px;
                font-size: 15px;
                background: rgba(255,255,255,0.2);
                padding: 10px 15px;
                border-radius: 5px;
                line-height: 1.6;
            }}
            .training-detail {{
                background: #fafafa;
                margin: 0;
                padding: 20px 25px;
                border-top: 1px solid #e0e0e0;
            }}
            .training-detail:last-child {{
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
            }}
            .detail-header {{
                font-weight: bold;
                color: #555;
                margin-bottom: 15px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 10px;
            }}
            .date-location {{
                font-size: 16px;
                color: #667eea;
            }}
            .oikiri {{
                background: #fff3cd;
                padding: 5px 12px;
                border-radius: 5px;
                font-size: 14px;
                color: #856404;
            }}
            .times {{
                margin: 15px 0;
                display: flex;
                flex-wrap: wrap;
                gap: 12px;
            }}
            .time-item {{
                padding: 12px 16px;
                background: white;
                border-radius: 8px;
                border: 2px solid #4CAF50;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                transition: transform 0.1s;
            }}
            .time-item:hover {{
                transform: scale(1.05);
            }}
            .time-converted {{
                color: #4CAF50;
                font-weight: bold;
                font-size: 18px;
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
                font-weight: bold;
            }}
            .awase {{
                margin: 12px 0;
                padding: 12px 15px;
                background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%);
                border-radius: 6px;
                border-left: 4px solid #2196F3;
                font-size: 14px;
            }}
            .comment {{
                margin: 12px 0;
                padding: 12px 15px;
                background: linear-gradient(135deg, #FFF9C4 0%, #FFF59D 100%);
                border-radius: 6px;
                border-left: 4px solid #FFC107;
                font-size: 14px;
                line-height: 1.7;
            }}
            .conversion-info {{
                background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
                padding: 10px 15px;
                border-radius: 6px;
                margin-top: 10px;
                font-size: 13px;
                color: #2E7D32;
                border-left: 4px solid #4CAF50;
            }}
            .no-data {{
                text-align: center;
                padding: 40px;
                color: #999;
                font-size: 18px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏇 調教データレポート - {race_id}</h1>
            
            <div class="legend">
                <div class="legend-title">📊 表示説明</div>
                <div class="legend-items">
                    <div class="legend-item">🟢 <span style="color: #4CAF50; font-weight: bold;">緑字</span> = 変換後タイム（共通基準）</div>
                    <div class="legend-item">⚫ <span style="color: #999;">灰字</span> = 元のタイム</div>
                    <div class="legend-item">🔴 <span style="color: #FF6B6B; font-weight: bold;">[n]</span> = 枠位置</div>
                    <div class="legend-item">📘 <span style="background: #E3F2FD; padding: 2px 8px; border-radius: 3px;">青背景</span> = 併せ馬</div>
                    <div class="legend-item">📒 <span style="background: #FFF9C4; padding: 2px 8px; border-radius: 3px;">黄背景</span> = コメント</div>
                    <div class="legend-item">🎯 変換基準: 美浦南W（坂路）</div>
                </div>
            </div>
    """
    
    if not training_data:
        html += '<div class="no-data">⚠️ 調教データが取得できませんでした</div>'
    
    # 馬ごとにカードを生成
    for horse_num in sorted(training_data.keys(), key=lambda x: int(x) if x.isdigit() else 999):
        horse = training_data[horse_num]
        
        html += f"""
        <div class="horse-card">
            <div class="horse-header">
                <div>
                    <span class="horse-num">🐴 {horse_num}</span>
                    <span class="horse-name">{horse.get('horse_name', '不明')}</span>
                </div>
                {f'<div class="tanpyo">💬 短評: {horse.get("tanpyo", "")}</div>' if horse.get('tanpyo') else ''}
            </div>
        """
        
        # 調教詳細
        for idx, detail in enumerate(horse.get('details', []), 1):
            date_location = detail.get('date_location', '')
            oikiri = detail.get('追い切り方', '')
            
            html += f"""
            <div class="training-detail">
                <div class="detail-header">
                    <span class="date-location">📅 {date_location}</span>
                    <span class="oikiri">⚡ {oikiri}</span>
                </div>
            """
            
            # タイム表示（変換後と元のタイム）
            times_converted = detail.get('times_converted', [])
            times_original = detail.get('times', [])
            positions = detail.get('positions', [])
            
            if times_converted:
                html += '<div class="times">'
                for i, time_conv in enumerate(times_converted):
                    time_orig = times_original[i] if i < len(times_original) else ''
                    position = positions[i] if i < len(positions) else ''
                    
                    # 変換されているかチェック
                    is_converted = time_conv != time_orig
                    
                    html += f"""
                    <div class="time-item">
                        <span class="time-converted">{time_conv}</span>
                        {f'<span class="time-original">({time_orig})</span>' if is_converted else ''}
                        {f'<span class="position">{position}</span>' if position else ''}
                    </div>
                    """
                html += '</div>'
            
            # 変換情報
            training_center = detail.get('training_center', '')
            course = detail.get('course', '')
            if training_center and course:
                html += f'<div class="conversion-info">✅ 変換: {training_center}{course}コース → 美浦南W換算</div>'
            
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
        </div>
    </body>
    </html>
    """
    
    return html

if __name__ == "__main__":
    test_with_existing_html()
