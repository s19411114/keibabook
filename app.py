"""
Streamlit GUI アプリケーション
競馬ブックスクレイパーの操作インターフェース
"""
import streamlit as st
import asyncio
import os
import json
import datetime
import importlib
from pathlib import Path
from src.utils.config import load_settings
from src.scrapers.keibabook import KeibaBookScraper
# モジュールのリロードを強制 (AttributeError対策)
import src.scrapers.jra_schedule
importlib.reload(src.scrapers.jra_schedule)
from src.scrapers.jra_schedule import JRAScheduleFetcher

from src.scrapers.jra_odds import JRAOddsFetcher
from src.utils.db_manager import CSVDBManager
from src.utils.recommender import HorseRecommender
from src.utils.horse_ranker import HorseRanker
from src.utils.upset_detector import UpsetDetector
from src.utils.logger import get_logger
from src.utils.venue_manager import VenueManager

logger = get_logger(__name__)

# ページ設定
st.set_page_config(
    page_title="競馬ブックスクレイパー",
    page_icon="🐎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- カスタムCSS (Premium UI - High Contrast) ---
st.markdown("""
<style>
    /* 全体のフォントと背景 */
    .stApp {
        background-color: #0e1117;
        color: #ffffff; /* テキストを真っ白に */
        font-family: 'Inter', sans-serif;
    }
    
    /* ヘッダー */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important; /* 強制的に白 */
        font-weight: 700;
    }
    
    /* 通常テキスト */
    p, label, .stMarkdown, .stText, li {
        color: #e0e0e0 !important;
    }
    
    /* カード風コンテナ */
    .css-1r6slb0, .css-12w0qpk {
        background-color: #1e2130;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        border: 1px solid #333;
    }
    
    /* ボタン */
    .stButton>button {
        background-color: #4CAF50;
        color: white !important;
        border-radius: 5px;
        border: none;
        padding: 10px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #45a049;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    /* 入力フィールド */
    .stTextInput>div>div>input, .stNumberInput>div>div>input {
        background-color: #262730;
        color: #ffffff !important;
        border-radius: 5px;
        border: 1px solid #444;
    }
    
    /* セレクトボックス - ドロップダウンメニューの視認性を確保 */
    .stSelectbox [data-baseweb="select"] > div {
        background-color: #262730 !important;
        color: #ffffff !important;
    }
    
    /* ドロップダウンメニューのオプション */
    [data-baseweb="popover"] {
        background-color: #1e2130 !important;
    }
    
    [role="option"] {
        background-color: #262730 !important;
        color: #ffffff !important;
    }
    
    [role="option"]:hover {
        background-color: #4CAF50 !important;
        color: #ffffff !important;
    }
    
    /* ラジオボタン */
    .stRadio>div {
        color: #ffffff !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        color: #ffffff !important;
        background-color: #1e2130;
    }
    
    /* メトリック */
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
    }
    [data-testid="stMetricLabel"] {
        color: #aaaaaa !important;
    }
    
    /* サイドバー */
    section[data-testid="stSidebar"] {
        background-color: #111;
    }
    
    /* ツールチップアイコン (?マーク) の視認性向上 */
    [data-testid="stTooltipIcon"] {
        color: #ffffff !important;
    }
    [data-testid="stTooltipIcon"] > svg {
        stroke: #ffffff !important;
        fill: #ffffff !important;
    }
    
    /* リンクの色 */
    a {
        color: #4CAF50 !important;
        text-decoration: none;
    }
    a:hover {
        text-decoration: underline;
    }
</style>
""", unsafe_allow_html=True)

# セッション状態の初期化
if 'scraping_in_progress' not in st.session_state:
    st.session_state.scraping_in_progress = False
if 'abort_scraping' not in st.session_state:
    st.session_state.abort_scraping = False
if 'scraped_data' not in st.session_state:
    st.session_state.scraped_data = None
if 'db_manager' not in st.session_state:
    st.session_state.db_manager = CSVDBManager()
if 'jra_schedule' not in st.session_state:
    st.session_state.jra_schedule = []
if 'last_fetched_date' not in st.session_state:
    st.session_state.last_fetched_date = None

# 会場コード定義 (推定)
VENUE_CODES = {
    # JRA
    "札幌": "01", "函館": "02", "福島": "03", "新潟": "04", "東京": "05", 
    "中山": "06", "中京": "07", "京都": "08", "阪神": "09", "小倉": "10",
    # NAR (標準的なコード)
    "帯広": "03", "門別": "36", "盛岡": "10", "水沢": "11", 
    "浦和": "18", "船橋": "19", "大井": "20", "川崎": "21", 
    "金沢": "22", "笠松": "23", "名古屋": "24", 
    "園田": "27", "姫路": "28", "高知": "31", "佐賀": "32"
}

# タイトルエリア
col_title, col_status = st.columns([3, 1])
with col_title:
    st.title("🐎 競馬ブックスクレイパー Pro")
with col_status:
    if st.session_state.scraping_in_progress:
        st.warning("🔄 処理中...")
    else:
        st.success("✅ 待機中")

st.markdown("---")

# 設定ファイルの読み込み
try:
    settings = load_settings()
except Exception as e:
    st.error(f"設定ファイル読み込みエラー: {e}")
    settings = {}

# --- スマートレース選択 (メインエリア上部) ---
st.subheader("📅 レース選択")

col1, col2, col3, col4 = st.columns(4)

with col1:
    # 日付選択 (現在時刻に応じてデフォルトを変更)
    now = datetime.datetime.now()
    today = datetime.date.today()
    
    # 17時以降なら翌日をデフォルトに
    if now.hour >= 17:
        default_date = today + datetime.timedelta(days=1)
    else:
        default_date = today
        
    selected_date = st.date_input("開催日", default_date)
    date_str = selected_date.strftime("%Y%m%d")
    
    # 日付が変わったらスケジュール再取得
    if st.session_state.last_fetched_date != selected_date:
        async def update_schedule():
            # タイムアウト対策: spinnerを表示しつつ、失敗してもエラーにしない
            try:
                with st.spinner(f"{selected_date}のスケジュールを確認中..."):
                    schedule = await JRAScheduleFetcher.fetch_schedule_for_date(selected_date)
                    st.session_state.jra_schedule = schedule
                    st.session_state.last_fetched_date = selected_date
            except Exception as e:
                logger.error(f"スケジュール更新エラー: {e}")
                st.session_state.jra_schedule = [] # 失敗時は空にして手動選択へ
        
        asyncio.run(update_schedule())

with col2:
    # 競馬種別と会場選択
    race_type_options = ["中央競馬 (JRA)", "地方競馬 (NAR)"]
    race_type_display = st.radio(
        "競馬種別", 
        race_type_options, 
        index=0 if settings.get('race_type', 'jra') == 'jra' else 1,
        horizontal=True
    )
    race_type = "jra" if race_type_display == "中央競馬 (JRA)" else "nar"
    
    if race_type == "nar":
        # 南関競馬会場を優先表示
        minami_kanto = VenueManager.get_minami_kanto_venues()
        other_venues = VenueManager.get_other_venues()
        
        # 南関競馬 + 区切り + その他会場
        venue_options = minami_kanto + ["---"] + other_venues
        
        default_venue = settings.get('venue', '大井')
        default_index = venue_options.index(default_venue) if default_venue in venue_options else 0
        
        selected_venue_display = st.selectbox(
            "会場", 
            venue_options,
            index=default_index,
            format_func=lambda x: "━━━━━━━━━━" if x == "---" else x
        )
        
        # 区切り線が選択された場合は最初の会場を選択
        selected_venue_name = selected_venue_display if selected_venue_display != "---" else minami_kanto[0]
    else:
        # JRA会場 (開催中の会場のみ表示)
        priority_order = ["福島", "東京", "中山", "阪神", "中京", "京都", "新潟", "小倉", "札幌", "函館"]
        
        # 取得したスケジュールから会場リストを作成
        today_venues = list(set([s['venue'] for s in st.session_state.jra_schedule])) if st.session_state.jra_schedule else []
        
        if today_venues:
            # 開催中の会場のみを優先順にソート
            active_venues = sorted([v for v in today_venues if v in priority_order], key=lambda x: priority_order.index(x))
            active_venues += [v for v in today_venues if v not in priority_order]
            
            selected_venue_name = st.selectbox("会場", active_venues)
        else:
            # スケジュール取得失敗時のみ全会場表示
            st.warning("⚠️ スケジュール取得に失敗しました。手動で会場を選択してください。")
            selected_venue_name = st.selectbox("会場 (手動選択)", priority_order)

with col3:
    # レース番号選択 (現在時刻から推定)
    default_race_num = 1
    
    # 選択日が今日の場合のみ時刻推定を行う
    if selected_date == today:
        if 9 <= now.hour <= 16:
            start_minutes = 9 * 60 + 50 # 9:50開始基準
            current_minutes = now.hour * 60 + now.minute
            diff_minutes = current_minutes - start_minutes
            if diff_minutes > 0:
                estimated_race = int(diff_minutes / 30) + 1
                default_race_num = max(1, min(12, estimated_race))
        elif 17 <= now.hour:
            # 今日だけど17時以降 -> 最終レース終わってるので手動選択待ち (または翌日誘導済み)
            default_race_num = 12 
    else:
        # 明日以降なら1Rから
        default_race_num = 1
    
    selected_race_num = st.number_input("レース番号", min_value=1, max_value=12, value=default_race_num)

with col4:
    # ID自動生成
    venue_code = VENUE_CODES.get(selected_venue_name, "00")
    generated_race_id = f"{date_str}{venue_code}{selected_race_num:02d}"
    
    # URL生成
    if race_type == "nar":
        generated_url = f"https://s.keibabook.co.jp/chihou/syutuba/{generated_race_id}"
    else:
        generated_url = f"https://s.keibabook.co.jp/cyuou/syutuba/{generated_race_id}"
    
    # URLリンク表示 (ボタン風)
    st.markdown(f"""
    <div style="margin-top: 28px;">
        <a href="{generated_url}" target="_blank" style="
            background-color: #262730; 
            color: #4CAF50 !important; 
            padding: 10px 15px; 
            border-radius: 5px; 
            border: 1px solid #4CAF50;
            text-decoration: none;
            display: block;
            text-align: center;
        ">
            🔗 出馬表ページを開く
        </a>
    </div>
    """, unsafe_allow_html=True)

# レースキー生成 (内部用)
generated_race_key = f"{date_str}_{VenueManager.get_venue_code(selected_venue_name) or 'unknown'}{selected_race_num}R"

st.markdown("---")

# --- サイドバー: 開発者設定 (隠蔽) ---
with st.sidebar:
    with st.expander("🛠️ 開発者設定 (Developer Settings)"):
        st.header("⚙️ 詳細設定")
        
        # ID/URLの手動オーバーライド
        st.subheader("🔧 パラメータ手動設定")
        manual_race_id = st.text_input("レースID (上書き用)", value=generated_race_id)
        manual_race_key = st.text_input("レースキー (上書き用)", value=generated_race_key)
        manual_url = st.text_input("URL (上書き用)", value=generated_url)
        
        # データベース統計
        st.subheader("📊 データベース統計")
        race_ids = st.session_state.db_manager.get_race_ids()
        st.metric("保存済みレース数", len(race_ids))
        
        # 重複チェック設定
        use_duplicate_check = st.checkbox("重複チェックを有効化", value=True)
        headless_mode = st.checkbox("ヘッドレスモード", value=settings.get('playwright_headless', False))

# メインコンテンツ
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📥 スクレイピング", "📊 データ確認", "🏇 トラックバイアス", "🎯 レコメンド", "📝 ログ"])

with tab1:
    st.header("データ取得実行")
    
    # 最終確認用の表示
    st.info(f"**対象**: {selected_date} {selected_venue_name} {selected_race_num}R")
    
    # ボタンエリア
    col_btn1, col_btn2 = st.columns([3, 1])
    
    with col_btn1:
        # スクレイピング実行ボタン
        start_button = st.button("🚀 スクレイピング開始", type="primary", disabled=st.session_state.scraping_in_progress)
    
    with col_btn2:
        # 中断ボタン
        if st.session_state.scraping_in_progress:
            if st.button("⛔ 中断", type="secondary"):
                st.session_state.abort_scraping = True
                st.warning("⚠️ 中断リクエストを送信しました...")
    
    if start_button:
        # 手動設定があればそちらを優先
        target_race_id = manual_race_id if manual_race_id != generated_race_id else generated_race_id
        target_race_key = manual_race_key if manual_race_key != generated_race_key else generated_race_key
        target_url = manual_url if manual_url != generated_url else generated_url
        
        if not target_race_id or not target_url:
            st.error("レースIDとURLが無効です")
        else:
            st.session_state.scraping_in_progress = True
            
            # 設定を更新
            current_settings = {
                'race_type': race_type,
                'venue': selected_venue_name if race_type == 'nar' else None,
                'venue_type': 'minami_kanto' if (race_type == 'nar' and VenueManager.is_minami_kanto(selected_venue_name)) else 'other' if race_type == 'nar' else None,
                'race_id': target_race_id,
                'race_key': target_race_key,
                'shutuba_url': target_url,
                'seiseki_url': settings.get('seiseki_url', ''),
                'playwright_headless': headless_mode,
                'playwright_timeout': settings.get('playwright_timeout', 30000),
                'output_dir': settings.get('output_dir', 'data')
            }
            
            # プログレスバー
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # スクレイピング実行
            async def run_scraping():
                # 中断フラグをリセット
                st.session_state.abort_scraping = False
                incomplete_files = []  # 中途半端なファイルを追跡
                
                try:
                    status_text.text("初期化中...")
                    progress_bar.progress(10)
                    
                    # 中断チェック
                    if st.session_state.abort_scraping:
                        raise Exception("ユーザーによる中断")
                    
                    # DBマネージャーの設定
                    db_manager = st.session_state.db_manager if use_duplicate_check else None
                    
                    # スクレイパー作成
                    scraper = KeibaBookScraper(current_settings, db_manager=db_manager)
                    
                    status_text.text("ページ取得中 (KeibaBook)...")
                    progress_bar.progress(30)
                    
                    # 中断チェック
                    if st.session_state.abort_scraping:
                        raise Exception("ユーザーによる中断")
                    
                    # スクレイピング実行 (KeibaBook)
                    scraped_data = await scraper.scrape()
                    
                    # 中断チェック
                    if st.session_state.abort_scraping:
                        raise Exception("ユーザーによる中断")
                    
                    # JRAオッズ取得 (JRAの場合のみ)
                    if race_type == 'jra':
                        status_text.text("リアルタイムオッズ取得中 (JRA)...")
                        progress_bar.progress(60)
                        
                        # 中断チェック
                        if st.session_state.abort_scraping:
                            raise Exception("ユーザーによる中断")
                        
                        jra_odds = await JRAOddsFetcher.fetch_realtime_odds(selected_venue_name, selected_race_num)
                        
                        # オッズデータをマージ
                        if jra_odds:
                            for horse in scraped_data.get('horses', []):
                                horse_num = horse.get('horse_num')
                                if horse_num in jra_odds:
                                    horse['current_odds'] = jra_odds[horse_num]
                                    logger.info(f"JRAオッズ適用: 馬番{horse_num} -> {jra_odds[horse_num]}")
                    
                    status_text.text("データ保存中...")
                    progress_bar.progress(80)
                    
                    # CSV DBに保存
                    if db_manager:
                        db_manager.save_race_data(
                            scraped_data,
                            target_race_id,
                            target_race_key
                        )
                    
                    # JSONファイルにも保存
                    output_dir = Path(current_settings.get('output_dir', 'data'))
                    output_dir.mkdir(parents=True, exist_ok=True)
                    json_file = output_dir / f"{target_race_key}.json"
                    incomplete_files.append(json_file)  # 追跡
                    
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(scraped_data, f, ensure_ascii=False, indent=2)
                    
                    # AI用JSONもエクスポート
                    if db_manager:
                        ai_json = db_manager.export_for_ai(target_race_id, str(output_dir / "json"))
                        if ai_json:
                            incomplete_files.append(Path(ai_json))  # 追跡
                    
                    progress_bar.progress(100)
                    status_text.text("完了！")
                    
                    st.session_state.scraped_data = scraped_data
                    st.success(f"✅ スクレイピング完了！ ({len(scraped_data.get('horses', []))}頭)")
                    
                    return scraped_data
                    
                except Exception as e:
                    logger.error(f"スクレイピングエラー: {e}")
                    
                    # 中断の場合は中途半端なファイルを削除
                    if st.session_state.abort_scraping or "中断" in str(e):
                        st.warning("🗑️ 中途半端なデータを削除しています...")
                        for file_path in incomplete_files:
                            try:
                                if file_path.exists():
                                    file_path.unlink()
                                    logger.info(f"削除: {file_path}")
                            except Exception as del_err:
                                logger.error(f"ファイル削除エラー: {del_err}")
                        st.info("✅ 中断しました。不完全なデータは削除されました。")
                    else:
                        st.error(f"❌ エラーが発生しました: {e}")
                    
                    status_text.text("中断" if st.session_state.abort_scraping else "エラー")
                    progress_bar.progress(0)
                finally:
                    st.session_state.scraping_in_progress = False
                    st.session_state.abort_scraping = False
            
            # 非同期実行
            asyncio.run(run_scraping())
            
            # ページをリロードして結果を表示
            st.rerun()

with tab2:
    st.header("📊 データ確認")
    
    # 保存済みファイルを取得
    output_dir = Path(settings.get('output_dir', 'data'))
    json_files = list(output_dir.glob('*.json'))
    
    # ファイル名からレース情報を抽出
    race_data_map = {}
    for json_file in json_files:
        filename = json_file.stem  # 例: 20251122_福島11R
        try:
            # ファイル名をパース
            parts = filename.split('_')
            if len(parts) >= 2:
                date_str = parts[0]  # 20251122
                venue_race = parts[1]  # 福島11R
                
                # 日付をフォーマット
                year = date_str[:4]
                month = date_str[4:6]
                day = date_str[6:8]
                date_key = f"{year}-{month}-{day}"
                
                # 会場とレース番号を抽出
                import re
                match = re.match(r'(.+?)(\d+)R', venue_race)
                if match:
                    venue = match.group(1)
                    race_num = int(match.group(2))
                    
                    if date_key not in race_data_map:
                        race_data_map[date_key] = {}
                    if venue not in race_data_map[date_key]:
                        race_data_map[date_key][venue] = {}
                    
                    race_data_map[date_key][venue][race_num] = json_file
        except Exception as e:
            logger.warning(f"ファイル名パースエラー: {filename} - {e}")
    
    if race_data_map:
        # 日付ごとに表示
        for date_key in sorted(race_data_map.keys(), reverse=True):
            year, month, day = date_key.split('-')
            st.subheader(f"📅 {year}年{month}月{day}日")
            
            venues = race_data_map[date_key]
            
            # 会場ごとにグリッド表示
            for venue in sorted(venues.keys()):
                st.markdown(f"**{venue}**")
                
                # 12レース分のボタンを横並びで表示
                cols = st.columns(12)
                for race_num in range(1, 13):
                    with cols[race_num - 1]:
                        if race_num in venues[venue]:
                            # データあり - ダウンロードボタン
                            json_file = venues[venue][race_num]
                            with open(json_file, 'r', encoding='utf-8') as f:
                                json_data = json.load(f)
                            json_str = json.dumps(json_data, ensure_ascii=False, indent=2)
                            
                            st.download_button(
                                label=f"●{race_num}R",
                                data=json_str,
                                file_name=f"{json_file.stem}.json",
                                mime="application/json",
                                key=f"download_{date_key}_{venue}_{race_num}",
                                help=f"{venue} {race_num}Rのデータをダウンロード"
                            )
                        else:
                            # データなし
                            st.markdown(f"<div style='text-align: center; color: #666;'>○{race_num}R</div>", unsafe_allow_html=True)
                
                st.markdown("---")
    else:
        st.info("まだデータがありません。スクレイピングを実行してください。")

with tab3:
    st.header("🏇 トラックバイアス分析")
    st.markdown("レース結果から馬場の傾向を分析します（上位6頭のデータを使用）")
    
    # Netkeiba結果URL入力
    st.subheader("📍 Netkeiba結果ページ")
    
    col_url1, col_url2 = st.columns([3, 1])
    
    with col_url1:
        result_url = st.text_input(
            "結果ページURL",
            value="https://race.netkeiba.com/race/result.html?race_id=202508040611",
            help="NetkeibaのレースIDを含むURL"
        )
    
    with col_url2:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        fetch_button = st.button("🔍 取得", type="primary")
    
    # レースIDを抽出
    import re
    race_id_match = re.search(r'race_id=(\d+)', result_url)
    
    if fetch_button and race_id_match:
        race_id = race_id_match.group(1)
        
        with st.spinner(f"レース結果を取得中... (ID: {race_id})"):
            # Netkeibaスクレイパーをインポート
            from src.scrapers.netkeiba_result import NetkeibaResultScraper
            
            async def fetch_and_analyze():
                scraper = NetkeibaResultScraper(headless=headless_mode)
                result_data = await scraper.fetch_result(race_id)
                return result_data
            
            # 非同期実行
            result_data = asyncio.run(fetch_and_analyze())
            
            if result_data and result_data.get('horses'):
                st.success(f"✅ 取得完了！ ({len(result_data['horses'])}頭)")
                
                # セッションに保存
                st.session_state.track_bias_data = result_data
            else:
                st.error("❌ データ取得に失敗しました")
    
    # トラックバイアス指数を表示
    if 'track_bias_data' in st.session_state and st.session_state.track_bias_data:
        data = st.session_state.track_bias_data
        
        st.markdown("---")
        st.subheader("📊 トラックバイアス指数")
        
        bias = data.get('track_bias', {})
        
        if bias and bias.get('bias_type') != 'データ不足':
            # メトリクス表示
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "バイアスタイプ",
                    bias.get('bias_type', 'N/A'),
                    help="内外・ペースの傾向"
                )
            
            with col2:
                inner_outer = bias.get('inner_outer_bias', 0)
                st.metric(
                    "内外バイアス",
                    f"{inner_outer:+.1f}",
                    help="マイナス=内有利、プラス=外有利"
                )
            
            with col3:
                pace = bias.get('pace_bias', 0)
                st.metric(
                    "ペースバイアス",
                    f"{pace:+.1f}",
                    help="マイナス=前有利、プラス=後有利"
                )
            
            with col4:
                confidence = bias.get('confidence', 0)
                st.metric(
                    "信頼度",
                    f"{confidence:.0%}",
                    help="データの完全性"
                )
            
            # 詳細情報
            with st.expander("📈 詳細分析"):
                st.write(f"**総合バイアススコア**: {bias.get('overall_bias_score', 0):.1f}/100")
                st.write(f"**上がり3Fバイアス**: {bias.get('last_3f_bias', 0):.1f}/100")
                
                # 解釈
                st.markdown("### 💡 解釈")
                bias_type = bias.get('bias_type', '')
                
                if '内有利' in bias_type:
                    st.info("🔵 **内枠有利**: 内枠の馬が好走しやすい馬場状態です")
                elif '外有利' in bias_type:
                    st.info("🔴 **外枠有利**: 外枠の馬が好走しやすい馬場状態です")
                
                if '前有利' in bias_type:
                    st.info("⚡ **前残り**: 逃げ・先行馬が有利な展開です")
                elif '後有利' in bias_type:
                    st.info("🏃 **差し有利**: 差し・追込馬が有利な展開です")
            
            # 上位6頭の詳細
            st.markdown("---")
            st.subheader("🏆 上位6頭の成績")
            
            horses = data.get('horses', [])[:6]
            
            for i, horse in enumerate(horses, 1):
                with st.expander(f"{i}着: {horse.get('horse_name', 'N/A')} ({horse.get('horse_num', '?')}番)"):
                    col_h1, col_h2, col_h3 = st.columns(3)
                    
                    with col_h1:
                        st.text(f"騎手: {horse.get('jockey', 'N/A')}")
                        st.text(f"タイム: {horse.get('time', 'N/A')}")
                    
                    with col_h2:
                        st.text(f"通過: {horse.get('passing', 'N/A')}")
                        st.text(f"上がり: {horse.get('last_3f', 'N/A')}")
                    
                    with col_h3:
                        st.text(f"人気: {horse.get('popularity', 'N/A')}番人気")
                        st.text(f"オッズ: {horse.get('odds', 'N/A')}倍")
        else:
            st.warning("⚠️ トラックバイアス指数を計算できませんでした（データ不足）")

with tab4:
    st.header("🎯 レコメンド機能")
    st.markdown("過小評価馬、穴馬候補、順位付けなど")
    
    # タブ内のサブタブ
    rec_tab1, rec_tab2, rec_tab3 = st.tabs(["🔍 過小評価馬", "💎 穴馬発見", "📊 順位付け"])
    
    # 保存済みレース一覧
    race_ids = st.session_state.db_manager.get_race_ids()
    
    if race_ids:
        selected_race_id = st.selectbox("レースを選択", race_ids, key="recommend_race")
        
        if selected_race_id:
            # JSONファイルを読み込み
            output_dir = Path(settings.get('output_dir', 'data'))
            json_file = output_dir / f"{selected_race_id}.json"
            
            if json_file.exists():
                with open(json_file, 'r', encoding='utf-8') as f:
                    race_data = json.load(f)
                
                # レコメンダー、ランカー、穴馬検出器を初期化
                recommender = HorseRecommender(st.session_state.db_manager)
                ranker = HorseRanker()
                upset_detector = UpsetDetector()
                
                with rec_tab1:
                    # 過小評価馬を検出
                    st.subheader("🔍 過小評価馬検出")
                
                col1, col2 = st.columns(2)
                with col1:
                    threshold_rank = st.slider(
                        "上位何割以内", 
                        min_value=0.5, 
                        max_value=1.0, 
                        value=0.7, 
                        step=0.1,
                        help="前走が上位何割以内に入っている馬を対象"
                    )
                with col2:
                    min_odds = st.number_input(
                        "最低オッズ", 
                        min_value=10.0, 
                        max_value=500.0, 
                        value=50.0, 
                        step=10.0,
                        help="これ以上のオッズの馬を検出"
                    )
                
                if st.button("過小評価馬を検出", type="primary"):
                    undervalued = recommender.find_undervalued_horses(
                        race_data, 
                        threshold_rank=threshold_rank, 
                        min_odds=min_odds
                    )
                    
                    if undervalued:
                        st.success(f"⚠️ {len(undervalued)}頭の過小評価馬を検出しました！")
                        for horse in undervalued:
                            with st.expander(f"🐴 {horse['horse_num']}番: {horse['horse_name']} - オッズ{horse['current_odds']:.1f}倍"):
                                st.warning(f"**理由**: {horse['reason']}")
                                st.info(f"前走着順: {horse['previous_rank']}着")
                    else:
                        st.info("過小評価馬は見つかりませんでした")
                
                with rec_tab2:
                    # 穴馬発見
                    st.subheader("💎 穴馬発見")
                    
                    if st.button("穴馬を検出", type="primary", key="detect_upset"):
                        upset_horses = upset_detector.detect_upset_horses(race_data)
                        
                        if upset_horses:
                            st.success(f"💎 {len(upset_horses)}頭の穴馬候補を検出しました！")
                            for horse in upset_horses:
                                with st.expander(f"🐴 {horse['horse_num']}番: {horse['horse_name']} - スコア{horse['upset_score']:.1f}"):
                                    st.metric("穴馬スコア", f"{horse['upset_score']:.1f}")
                                    st.write("**検出シグナル:**")
                                    for signal in horse.get('upset_signals', []):
                                        st.info(f"• {signal.get('reason', '')}")
                        else:
                            st.info("穴馬候補は見つかりませんでした")
                
                with rec_tab3:
                    # 順位付け
                    st.subheader("📊 順位付け")
                    
                    if st.button("順位付けを実行", type="primary", key="rank_horses"):
                        ranked_horses = ranker.rank_horses(race_data)
                        
                        st.success(f"✅ {len(ranked_horses)}頭を順位付けしました")
                        
                        # 順位表を表示
                        for horse in ranked_horses:
                            with st.expander(f"🏆 {horse.get('predicted_rank', '?')}位: {horse.get('horse_num', '?')}番 {horse.get('horse_name', 'N/A')} - スコア{horse.get('rank_score', 0):.1f}"):
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("総合スコア", f"{horse.get('rank_score', 0):.1f}")
                                    st.metric("予測順位", f"{horse.get('predicted_rank', '?')}位")
                                with col2:
                                    breakdown = horse.get('rank_breakdown', {})
                                    st.write("**スコア内訳:**")
                                    st.text(f"血統: {breakdown.get('pedigree', 0):.1f}")
                                    st.text(f"トラックバイアス: {breakdown.get('track_bias', 0):.1f}")
                                    st.text(f"斤量比: {breakdown.get('weight_ratio', 0):.1f}")
                                    st.text(f"クラス成績: {breakdown.get('class_performance', 0):.1f}")
                                    st.text(f"脚質: {breakdown.get('running_style', 0):.1f}")
                                    st.text(f"調教: {breakdown.get('training', 0):.1f}")
                
                st.markdown("---")
                
                # 馬の成績分析
                st.subheader("📈 馬の成績分析")
                horses = race_data.get('horses', [])
                if horses:
                    selected_horse = st.selectbox(
                        "分析する馬を選択",
                        [f"{h.get('horse_num', '?')}番: {h.get('horse_name', 'N/A')}" for h in horses],
                        key="analyze_horse"
                    )
                    
                    if st.button("分析実行", key="analyze_btn"):
                        horse_num = selected_horse.split('番')[0]
                        target_horse = next((h for h in horses if h.get('horse_num') == horse_num), None)
                        
                        if target_horse:
                            analysis = recommender.analyze_horse_performance(target_horse)
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("一貫性", analysis['consistency'])
                            with col2:
                                st.metric("近走調子", analysis['recent_form'])
                            
                            if analysis['flags']:
                                 st.warning("⚠️ 要注意フラグ:")
                                 for flag in analysis['flags']:
                                     st.text(f"  • {flag}")
                else:
                    st.info("馬データがありません")
            else:
                st.warning(f"JSONファイルが見つかりません: {json_file}")
    else:
        st.info("まだデータがありません。スクレイピングを実行してください。")

with tab5:
    st.header("ログ・進捗記録")
    
    # URLログ表示
    st.subheader("取得済みURL一覧")
    url_log_path = st.session_state.db_manager.url_log_path
    
    if url_log_path.exists():
        import pandas as pd
        try:
            df = pd.read_csv(url_log_path, encoding='utf-8-sig')
            if len(df) > 0:
                st.dataframe(df, use_container_width=True)
            else:
                st.info("ログがありません")
        except Exception as e:
            st.error(f"ログ読み込みエラー: {e}")
    else:
        st.info("ログファイルがありません")
    
    st.markdown("---")
    
    # プロジェクトログ表示
    if Path("PROJECT_LOG.md").exists():
        st.subheader("プロジェクトログ")
        with open("PROJECT_LOG.md", 'r', encoding='utf-8') as f:
            log_content = f.read()
        st.markdown(log_content)

# フッター
st.markdown("---")
st.caption("競馬ブックスクレイパー v1.0 | 利用規約とrobots.txtを確認してください")
