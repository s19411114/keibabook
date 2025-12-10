"""
ARCHIVED: app.py (Streamlit UI)
This file has been archived and replaced by `app_nicegui.py`.
Do not run this file. Use `python -m app_nicegui` or `scripts/run_nicegui.sh`.
"""

from src.utils.logger import get_logger

logger = get_logger(__name__)
logger.warning('app.py is archived. Use app_nicegui.py (NiceGUI) instead.')

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
    from src.ui.scraping_tab import render_scraping_tab
    render_scraping_tab(
        settings,
        st.session_state.db_manager,
        selected_date,
        selected_venue_name,
        selected_race_num,
        generated_race_id,
        generated_race_key,
        generated_url,
        manual_race_id,
        manual_race_key,
        manual_url,
        headless_mode,
        use_duplicate_check,
    )

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
        st.header("🏇 トラックバイアス（移行済み）")
        st.warning("トラックバイアス解析は keiba-ai に移行しました。詳細は migration/to_keiba_ai を参照してください。")
        

with tab4:
    st.header("🎯 レコメンド機能（移行済み）")
    st.warning("レコメンド（過小評価馬検出、穴馬検出、順位付け）は keiba-ai に移行しました。解析・UI は keiba-ai を参照してください。")

with tab_training:
    st.header("⏱️ 調教評価（移行済み）")
    st.warning("調教評価は keiba-ai に移行しました。分析とUIは keiba-ai を参照してください。")

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
