"""
Streamlit GUI アプリケーション
競馬ブックスクレイパーの操作インターフェース
"""
import streamlit as st
import asyncio
import os
import json
from pathlib import Path
from src.utils.config import load_settings
from src.scrapers.keibabook import KeibaBookScraper
from src.utils.db_manager import CSVDBManager
from src.utils.recommender import HorseRecommender
from src.utils.horse_ranker import HorseRanker
from src.utils.upset_detector import UpsetDetector
from src.utils.logger import get_logger

logger = get_logger(__name__)

# ページ設定
st.set_page_config(
    page_title="競馬ブックスクレイパー",
    page_icon="🐎",
    layout="wide"
)

# セッション状態の初期化
if 'scraping_in_progress' not in st.session_state:
    st.session_state.scraping_in_progress = False
if 'scraped_data' not in st.session_state:
    st.session_state.scraped_data = None
if 'db_manager' not in st.session_state:
    st.session_state.db_manager = CSVDBManager()

# タイトル
st.title("🐎 競馬ブックスクレイパー")
st.markdown("---")

# サイドバー: 設定
with st.sidebar:
    st.header("⚙️ 設定")
    
    # 設定ファイルの読み込み
    try:
        settings = load_settings()
        st.success("設定ファイル読み込み成功")
    except Exception as e:
        st.error(f"設定ファイル読み込みエラー: {e}")
        settings = {}
    
    # レース情報表示
    if 'race_id' in settings:
        st.subheader("現在のレース")
        st.text(f"レースID: {settings.get('race_id', 'N/A')}")
        st.text(f"レースキー: {settings.get('race_key', 'N/A')}")
        st.text(f"URL: {settings.get('shutuba_url', 'N/A')[:50]}...")
    
    st.markdown("---")
    
    # データベース統計
    st.subheader("📊 データベース統計")
    race_ids = st.session_state.db_manager.get_race_ids()
    st.metric("保存済みレース数", len(race_ids))
    
    # 重複チェック設定
    use_duplicate_check = st.checkbox("重複チェックを有効化", value=True)
    
    st.markdown("---")
    
    # 中央競馬/地方競馬選択
    race_type_options = {
        "中央競馬 (JRA)": "jra",
        "地方競馬 (NAR)": "nar"
    }
    race_type_display = st.radio(
        "競馬種別",
        list(race_type_options.keys()),
        index=0 if settings.get('race_type', 'jra') == 'jra' else 1
    )
    race_type = race_type_options[race_type_display]
    
    # 地方競馬の場合、会場選択
    if race_type == 'nar':
        from src.utils.venue_manager import VenueManager
        
        venue_type = st.radio(
            "会場タイプ",
            ["南関4会場", "その他会場"],
            index=0 if settings.get('venue_type', 'minami_kanto') == 'minami_kanto' else 1
        )
        
        if venue_type == "南関4会場":
            venue_options = VenueManager.get_minami_kanto_venues()
            default_venue = settings.get('venue', '大井')
        else:
            venue_options = VenueManager.get_other_venues()
            default_venue = settings.get('venue', '門別')
        
        selected_venue = st.selectbox(
            "会場を選択",
            venue_options,
            index=venue_options.index(default_venue) if default_venue in venue_options else 0
        )
    else:
        selected_venue = None

# メインコンテンツ
tab1, tab2, tab3, tab4 = st.tabs(["📥 スクレイピング", "📊 データ確認", "🎯 レコメンド", "📝 ログ"])

with tab1:
    st.header("レースデータ取得")
    
    # レース情報入力
    col1, col2 = st.columns(2)
    
    with col1:
        race_id = st.text_input(
            "レースID",
            value=settings.get('race_id', ''),
            help="例: 202503060201"
        )
        race_key = st.text_input(
            "レースキー",
            value=settings.get('race_key', ''),
            help="例: 20250306_fukushima1R"
        )
    
    with col2:
        shutuba_url = st.text_input(
            "出馬表URL",
            value=settings.get('shutuba_url', ''),
            help="競馬ブックの出馬表ページURL"
        )
        headless_mode = st.checkbox("ヘッドレスモード", value=settings.get('playwright_headless', False))
    
    # スクレイピング実行ボタン
    if st.button("🚀 スクレイピング開始", type="primary", disabled=st.session_state.scraping_in_progress):
        if not race_id or not shutuba_url:
            st.error("レースIDと出馬表URLを入力してください")
        else:
            st.session_state.scraping_in_progress = True
            
            # 設定を更新
            current_settings = {
                'race_type': race_type,  # 競馬種別
                'venue': selected_venue if race_type == 'nar' else None,  # 会場（地方競馬の場合）
                'venue_type': 'minami_kanto' if (race_type == 'nar' and venue_type == '南関4会場') else 'other' if race_type == 'nar' else None,
                'race_id': race_id,
                'race_key': race_key or race_id,
                'shutuba_url': shutuba_url,
                'seiseki_url': settings.get('seiseki_url', ''),  # 結果ページURL
                'playwright_headless': headless_mode,
                'playwright_timeout': settings.get('playwright_timeout', 30000),
                'output_dir': settings.get('output_dir', 'data')
            }
            
            # プログレスバー
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # スクレイピング実行
            async def run_scraping():
                try:
                    status_text.text("初期化中...")
                    progress_bar.progress(10)
                    
                    # DBマネージャーの設定
                    db_manager = st.session_state.db_manager if use_duplicate_check else None
                    
                    # スクレイパー作成
                    scraper = KeibaBookScraper(current_settings, db_manager=db_manager)
                    
                    status_text.text("ページ取得中...")
                    progress_bar.progress(30)
                    
                    # スクレイピング実行
                    scraped_data = await scraper.scrape()
                    
                    status_text.text("データ保存中...")
                    progress_bar.progress(80)
                    
                    # CSV DBに保存
                    if db_manager:
                        db_manager.save_race_data(
                            scraped_data,
                            race_id,
                            race_key or race_id
                        )
                    
                    # JSONファイルにも保存
                    output_dir = Path(current_settings.get('output_dir', 'data'))
                    output_dir.mkdir(parents=True, exist_ok=True)
                    json_file = output_dir / f"{race_key or race_id}.json"
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(scraped_data, f, ensure_ascii=False, indent=2)
                    
                    # AI用JSONもエクスポート
                    if db_manager:
                        db_manager.export_for_ai(race_id, str(output_dir / "json"))
                    
                    progress_bar.progress(100)
                    status_text.text("完了！")
                    
                    st.session_state.scraped_data = scraped_data
                    st.success(f"✅ スクレイピング完了！ ({len(scraped_data.get('horses', []))}頭)")
                    
                    return scraped_data
                    
                except Exception as e:
                    logger.error(f"スクレイピングエラー: {e}")
                    st.error(f"❌ エラーが発生しました: {e}")
                    status_text.text("エラー")
                    raise
                finally:
                    st.session_state.scraping_in_progress = False
            
            # 非同期実行
            asyncio.run(run_scraping())
            
            # ページをリロードして結果を表示
            st.rerun()

with tab2:
    st.header("データ確認")
    
    # 保存済みレース一覧
    race_ids = st.session_state.db_manager.get_race_ids()
    
    if race_ids:
        selected_race_id = st.selectbox("レースを選択", race_ids)
        
        if selected_race_id:
            # JSONファイルを読み込み
            output_dir = Path(settings.get('output_dir', 'data'))
            json_file = output_dir / f"{selected_race_id}.json"
            
            if json_file.exists():
                with open(json_file, 'r', encoding='utf-8') as f:
                    race_data = json.load(f)
                
                # レース情報表示
                st.subheader("レース情報")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("レース名", race_data.get('race_name', 'N/A'))
                with col2:
                    st.metric("グレード", race_data.get('race_grade', 'N/A'))
                with col3:
                    st.metric("距離", race_data.get('distance', 'N/A'))
                
                # 馬一覧
                st.subheader("出馬表")
                horses = race_data.get('horses', [])
                if horses:
                    for horse in horses:
                        with st.expander(f"🐴 {horse.get('horse_num', '?')}番: {horse.get('horse_name', 'N/A')}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.text(f"騎手: {horse.get('jockey', 'N/A')}")
                                if 'training_data' in horse and horse['training_data']:
                                    st.text("調教データ: あり")
                                if 'pedigree_data' in horse and horse['pedigree_data']:
                                    st.text("血統データ: あり")
                            with col2:
                                if 'stable_comment' in horse:
                                    st.text_area("厩舎コメント", horse.get('stable_comment', ''), height=100)
                                if 'previous_race_comment' in horse:
                                    st.text_area("前走コメント", horse.get('previous_race_comment', ''), height=100)
                else:
                    st.info("馬データがありません")
            else:
                st.warning(f"JSONファイルが見つかりません: {json_file}")
    else:
        st.info("まだデータがありません。スクレイピングを実行してください。")

with tab3:
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

with tab4:
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

