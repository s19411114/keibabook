"""
Streamlit GUI アプリケーション
競馬ブックスクレイパーの操作インターフェース

【重要な変更点】
- Playwright → httpx に移行（Streamlit環境で安定動作）
- asyncio.run() → 同期版 scrape_sync() を使用
- スケジュール取得は一時的に無効化（手動選択）
"""
import streamlit as st
import os
import json
import datetime
import time
import subprocess
import sys
from pathlib import Path
from src.utils.config import load_settings
# Playwrightはサブプロセス(scripts/scrape_worker.py)で実行

from src.utils.db_manager import CSVDBManager
from src.utils.recommender import HorseRecommender
from src.utils.horse_ranker import HorseRanker
from src.utils.upset_detector import UpsetDetector
from src.utils.logger import get_logger
from src.utils.venue_manager import VenueManager
from src.utils.output import save_per_race_json

logger = get_logger(__name__)

# ページ設定
st.set_page_config(
    page_title="競馬ブックスクレイパー",
    page_icon="🐎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 設定ファイルの読み込み（最初に実行）
try:
    settings = load_settings()
except Exception as e:
    st.error(f"設定ファイル読み込みエラー: {e}")
    settings = {}

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
        min-height: 40px;  /* 最小高さを統一 */
    }
    .stButton>button:hover {
        background-color: #45a049;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    /* サイドバーのレース番号ボタン */
    [data-testid="stSidebar"] .stButton>button {
        min-height: 36px;
        padding: 6px 8px;
        font-size: 13px;
        white-space: nowrap;
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

# タイトル（シンプルに1行）
st.markdown("### 🐎 競馬ブックスクレイパー")

# --- サイドバー: レース選択 + 開発者設定 ---
with st.sidebar:
    st.markdown("### 📅 レース選択")
    
    # 競馬種別
    race_type_options = ["中央 (JRA)", "地方 (NAR)"]
    race_type_display = st.radio(
        "種別", race_type_options, 
        index=0 if settings.get('race_type', 'jra') == 'jra' else 1,
        horizontal=True
    )
    race_type = "jra" if race_type_display == "中央 (JRA)" else "nar"
    
    # 日付選択
    now = datetime.datetime.now()
    today = datetime.date.today()
    default_date = today + datetime.timedelta(days=1) if now.hour >= 17 else today
    selected_date = st.date_input("開催日", default_date)
    date_str = selected_date.strftime("%Y%m%d")
    
    # スケジュール（シンプルに空リストを使用）
    if st.session_state.last_fetched_date != selected_date:
        st.session_state.jra_schedule = []
        st.session_state.last_fetched_date = selected_date
    
    # 会場選択
    if race_type == "nar":
        minami_kanto = VenueManager.get_minami_kanto_venues()
        other_venues = VenueManager.get_other_venues()
        venue_options = minami_kanto + ["――"] + other_venues
        default_venue = settings.get('venue', '大井')
        default_index = venue_options.index(default_venue) if default_venue in venue_options else 0
        selected_venue_display = st.selectbox(
            "会場", venue_options, index=default_index,
            format_func=lambda x: "─────" if x == "――" else x
        )
        selected_venue_name = selected_venue_display if selected_venue_display != "――" else minami_kanto[0]
    else:
        priority_order = ["東京", "中山", "阪神", "京都", "中京", "福島", "新潟", "小倉", "札幌", "函館"]
        selected_venue_name = st.selectbox("会場", priority_order)
    
    # レース番号 - ワンクリックボタン形式
    st.markdown("##### 🏇 レース番号")
    
    # 初期化
    if 'selected_race_num' not in st.session_state:
        # デフォルト: 現在時刻から推測
        default_race_num = 11  # 重賞は11Rか12Rが多い
        if selected_date == today and 9 <= now.hour <= 16:
            start_minutes = 9 * 60 + 50
            current_minutes = now.hour * 60 + now.minute
            diff_minutes = current_minutes - start_minutes
            if diff_minutes > 0:
                default_race_num = max(1, min(12, int(diff_minutes / 30) + 1))
        st.session_state.selected_race_num = default_race_num
    
    # 12個のボタンを3行4列で配置
    for row in range(3):
        cols = st.columns(4)
        for col_idx in range(4):
            race_num = row * 4 + col_idx + 1
            with cols[col_idx]:
                # 選択中のレースは異なるスタイル
                is_selected = st.session_state.selected_race_num == race_num
                # ボタンラベルを統一（選択中は●、未選択は○）
                if is_selected:
                    btn_label = f"● {race_num}R"
                else:
                    btn_label = f"○ {race_num}R"
                if st.button(btn_label, key=f"race_btn_{race_num}", use_container_width=True):
                    st.session_state.selected_race_num = race_num
                    st.rerun()
    
    selected_race_num = st.session_state.selected_race_num
    
    # ID/URL生成
    venue_code = VENUE_CODES.get(selected_venue_name, "00")
    generated_race_id = f"{date_str}{venue_code}{selected_race_num:02d}"
    generated_race_key = f"{date_str}_{VenueManager.get_venue_code(selected_venue_name) or 'unknown'}{selected_race_num}R"
    if race_type == "nar":
        generated_url = f"https://s.keibabook.co.jp/chihou/syutuba/{generated_race_id}"
    else:
        generated_url = f"https://s.keibabook.co.jp/cyuou/syutuba/{generated_race_id}"
    
    st.markdown("---")
    st.caption(f"ID: {generated_race_id}")
    st.markdown(f"[🔗 出馬表]({generated_url})")
    
    st.markdown("---")
    
    # ================================================================================
    # ⚠️ ログイン管理セクション - このセクションを削除しないでください
    # ================================================================================
    st.markdown("##### 🔐 ログイン管理")
    cookie_file = settings.get('cookie_file', 'cookies.json')
    
    from src.utils.keibabook_auth import KeibaBookAuth
    is_valid, status_msg = KeibaBookAuth.is_cookie_valid(cookie_file)
    
    if is_valid:
        st.success(f"✅ ログイン済 ({status_msg})")
        # ログアウトボタン
        if st.button("🚪 ログアウト", key="logout_btn", help="Cookieを削除してログアウト"):
            try:
                import os
                if os.path.exists(cookie_file):
                    os.remove(cookie_file)
                    st.success("✅ ログアウトしました")
                    st.rerun()
            except Exception as e:
                st.error(f"❌ ログアウトエラー: {e}")
    else:
        st.warning(f"⚠️ 未ログイン")
        st.caption(status_msg)
        if st.button("🔑 ログイン実行", key="sidebar_login", help="ブラウザでログインを実行"):
            with st.spinner("ログイン中..."):
                try:
                    result = subprocess.run(
                        [sys.executable, "scripts/login_helper.py"],
                        capture_output=True, text=True, timeout=120
                    )
                    if result.returncode == 0:
                        st.success("✅ ログイン成功！")
                        st.rerun()
                    else:
                        st.error(f"❌ ログイン失敗")
                        with st.expander("エラー詳細"):
                            st.code(result.stderr if result.stderr else result.stdout)
                except Exception as e:
                    st.error(f"❌ エラー: {e}")
    # ================================================================================
    
    # 開発者設定
    with st.expander("⚙️ 詳細設定"):
        manual_race_id = st.text_input("レースID", value=generated_race_id)
        manual_race_key = st.text_input("レースキー", value=generated_race_key)
        manual_url = st.text_input("URL", value=generated_url)
        use_duplicate_check = st.checkbox("重複チェック", value=True)
        headless_mode = st.checkbox("ヘッドレス", value=settings.get('playwright_headless', False))
        race_ids = st.session_state.db_manager.get_race_ids()
        st.caption(f"保存済: {len(race_ids)}件")

# タブ（Home削除）
tab1, tab3, tab_training, tab4, tab2, tab5 = st.tabs(["📥 スクレイピング", "🏇 トラックバイアス", "⏱️ 調教", "🎯 レコメンド", "📊 データ", "📝 ログ"])


with tab1:
    # シンプルなヘッダー
    st.markdown(f"### 📥 {selected_date.strftime('%m/%d')} {selected_venue_name} {selected_race_num}R")
    
    # 一括取得ボタン（Playwrightをサブプロセスで実行）
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if st.button("🚀 データ取得", type="primary", disabled=st.session_state.scraping_in_progress, use_container_width=True):
            st.session_state.scraping_in_progress = True
            
            # 手動設定があればそちらを優先
            target_race_id = manual_race_id if manual_race_id != generated_race_id else generated_race_id
            target_race_key = manual_race_key if manual_race_key != generated_race_key else generated_race_key
            target_url = manual_url if manual_url != generated_url else generated_url
            
            if not target_race_id or not target_url:
                st.error("レースIDとURLが無効です")
                st.session_state.scraping_in_progress = False
            else:
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
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    # サブプロセスでPlaywrightスクレイパーを実行
                    output_file = Path(settings.get('output_dir', 'data')) / f"{target_race_key}.json"
                    
                    status_text.text("🔄 Playwrightでデータ取得中...")
                    progress_bar.progress(20)
                    
                    # スクレイピングワーカーを実行
                    result = subprocess.run(
                        [
                            sys.executable, 
                            "scripts/scrape_worker.py",
                            f"--race_id={target_race_id}",
                            f"--race_type={race_type}",
                            f"--output={output_file}"
                        ],
                        capture_output=True,
                        text=True,
                        timeout=180,  # 3分タイムアウト
                        cwd=str(Path(__file__).parent)
                    )
                    
                    progress_bar.progress(80)
                    
                    if result.returncode == 0 and output_file.exists():
                        with open(output_file, 'r', encoding='utf-8') as f:
                            scraped_data = json.load(f)
                        
                        horse_count = len(scraped_data.get('horses', []))
                        
                        # DBに保存
                        if use_duplicate_check:
                            st.session_state.db_manager.save_race_data(
                                scraped_data, target_race_id, target_race_key
                            )
                        
                        progress_bar.progress(100)
                        status_text.text("✅ 完了！")
                        st.success(f"✅ {horse_count}頭のデータを取得しました")
                        st.session_state.scraped_data = scraped_data
                    else:
                        status_text.text("❌ エラー")
                        st.error("データ取得に失敗しました")
                        if result.stderr:
                            with st.expander("エラー詳細"):
                                st.code(result.stderr)
                
                except subprocess.TimeoutExpired:
                    st.error("⏱️ タイムアウト（3分経過）")
                except Exception as e:
                    st.error(f"❌ エラー: {e}")
                finally:
                    st.session_state.scraping_in_progress = False
    
    with col2:
        # 中断ボタン（将来用）
        st.button("⛔ 中断", disabled=not st.session_state.scraping_in_progress, use_container_width=True)
    
    # 取得済みデータの表示
    if 'scraped_data' in st.session_state and st.session_state.scraped_data:
        data = st.session_state.scraped_data
        st.markdown("---")
        st.markdown(f"#### {data.get('race_name', '')} {data.get('race_grade', '')}")
        
        horses = data.get('horses', [])
        if horses:
            # 簡易テーブル
            for horse in horses[:5]:  # 最初の5頭だけ表示
                col_a, col_b, col_c = st.columns([1, 3, 2])
                with col_a:
                    st.write(f"**{horse.get('horse_num', '')}**")
                with col_b:
                    st.write(horse.get('horse_name', ''))
                with col_c:
                    st.write(f"{horse.get('prediction_mark', '')} | {horse.get('jockey', '')}")
            
            if len(horses) > 5:
                st.caption(f"... 他 {len(horses) - 5} 頭")

with tab2:
    st.header("📊 データ確認")
    
    # 保存済みファイルを取得
    output_dir = Path(settings.get('output_dir', 'data'))
    json_files = list(output_dir.glob('*.json'))
    
    # ファイル名からレース情報を抽出
    race_data_map = {}
    for json_file in json_files:
        filename = json_file.stem  # 例: 20251124_tokyo11R
        try:
            # 新しいファイル名形式に対応 (YYYYMMDD_venueRR)
            parts = filename.split('_')
            if len(parts) >= 2:
                date_str = parts[0]  # 20251124
                venue_race = parts[1]  # tokyo11R
                
                # 日付をフォーマット
                if len(date_str) == 8:
                    year = date_str[:4]
                    month = date_str[4:6]
                    day = date_str[6:8]
                    date_key = f"{year}-{month}-{day}"
                    
                    # 会場とレース番号を抽出
                    import re
                    # 日本語会場名または英語会場名に対応
                    match = re.match(r'([a-zA-Z]+|[^0-9]+)(\d+)R', venue_race)
                    if match:
                        venue = match.group(1)
                        race_num = int(match.group(2))
                        
                        # 英語会場名を日本語に変換（必要なら）
                        venue_map = {"tokyo": "東京", "kyoto": "京都", "fukushima": "福島", "hanshin": "阪神", "nakayama": "中山"}
                        venue_jp = venue_map.get(venue.lower(), venue)
                        
                        if date_key not in race_data_map:
                            race_data_map[date_key] = {}
                        if venue_jp not in race_data_map[date_key]:
                            race_data_map[date_key][venue_jp] = {}
                        
                        race_data_map[date_key][venue_jp][race_num] = json_file
        except Exception as e:
            logger.warning(f"ファイル名パースエラー: {filename} - {e}")
    
    if race_data_map:
        # 日付ごとに表示
        for date_key in sorted(race_data_map.keys(), reverse=True):
            year, month, day = date_key.split('-')
            with st.expander(f"📅 {year}年{month}月{day}日", expanded=True):
                venues = race_data_map[date_key]
                
                # 会場ごとにグリッド表示
                for venue in sorted(venues.keys()):
                    st.markdown(f"**{venue}**")
                    
                    # 12レース分のボタンを横並びで表示
                    cols = st.columns(12)
                    for race_num in range(1, 13):
                        with cols[race_num - 1]:
                            if race_num in venues[venue]:
                                # データあり - 選択ボタン
                                if st.button(f"●{race_num}R", key=f"sel_{date_key}_{venue}_{race_num}"):
                                    st.session_state.selected_file = venues[venue][race_num]
                            else:
                                # データなし
                                st.markdown(f"<div style='text-align: center; color: #666; font-size: 0.8em; padding-top: 5px;'>○{race_num}</div>", unsafe_allow_html=True)
                    st.markdown("---")

        # 選択されたファイルのデータを表示
        if 'selected_file' in st.session_state and st.session_state.selected_file:
            json_file = st.session_state.selected_file
            st.markdown("### 📝 選択中のレースデータ")
            
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                # 基本情報表示
                st.info(f"📍 {json_data.get('race_name', '不明なレース')} ({json_data.get('race_grade', '-')})")
                
                # データ整形（コピー用）
                copy_text = f"レース名: {json_data.get('race_name')}\n"
                copy_text += f"グレード: {json_data.get('race_grade')}\n"
                copy_text += "-" * 30 + "\n"
                

                horses = json_data.get('horses', [])
                
                # テーブルデータ作成
                table_data = []
                for horse in horses:
                    # コピー用テキスト作成
                    mark = horse.get('prediction_mark', '-')
                    odds = horse.get('odds_text', '-')
                    pedigree = horse.get('pedigree_data', {})
                    father = pedigree.get('father', '-')
                    mother = pedigree.get('mother', '-')
                    
                    copy_text += f"{horse.get('horse_num', '?')}番: {horse.get('horse_name', '-')} ({mark}印 | {odds}倍)\n"
                    copy_text += f"  父: {father} / 母: {mother}\n"
                    
                    # テーブル行を追加
                    table_data.append({
                        "馬番": horse.get('horse_num', '?'),
                        "馬名": horse.get('horse_name', '-'),
                        "印": mark,
                        "オッズ": odds,
                        "父": father,
                        "母": mother
                    })
                
                # テーブル表示
                if table_data:
                    st.table(table_data)
                    
                    # コピーボタン
                    st.download_button(
                        label="📋 データをコピー用に保存",
                        data=copy_text,
                        file_name=f"{json_data.get('race_name', 'race')}_copy.txt",
                        mime="text/plain"
                    )
            
            except Exception as e:
                st.error(f"データ読み込みエラー: {e}")
    
    else:
        st.info("保存されているデータがありません。スクレイピングを実行してください。")

# tab3: トラックバイアス分析
if tab3:
    with tab3:
        from src.ui import render_track_bias_tab
        render_track_bias_tab(st.session_state.db_manager, headless_mode)
        

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

with tab_training:
    # 調教早見表タブ
    from src.ui.training_evaluation_tab import render_training_evaluation_tab
    render_training_evaluation_tab()

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
