"""
ARCHIVED: src/ui/scraping_tab.py (Streamlit UI)
The scraping Tab has been migrated to NiceGUI; this module is kept for historical reference.
"""

from src.utils.logger import get_logger

logger = get_logger(__name__)
logger.warning("src/ui/scraping_tab.py has been archived. The NiceGUI UI now handles scraping interactions.")

def render_scraping_tab(*args, **kwargs):
    logger.info("render_scraping_tab is archived; use app_nicegui.py for UI interactions.")

    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("🚀 データ取得", type="primary", disabled=st.session_state.scraping_in_progress, use_container_width=True):
            st.session_state.scraping_in_progress = True
            target_race_id = manual_race_id if manual_race_id != generated_race_id else generated_race_id
            target_race_key = manual_race_key if manual_race_key != generated_race_key else generated_race_key
            target_url = manual_url if manual_url != generated_url else generated_url

            if not target_race_id or not target_url:
                st.error("レースIDとURLが無効です")
                st.session_state.scraping_in_progress = False
            else:
                current_settings = {
                    'race_id': target_race_id,
                    'race_key': target_race_key,
                    'shutuba_url': target_url,
                    'playwright_headless': headless_mode,
                    'playwright_timeout': settings.get('playwright_timeout', 30000),
                    'output_dir': settings.get('output_dir', 'data'),
                }
                progress_bar = st.progress(0)
                status_text = st.empty()
                try:
                    output_file = Path(settings.get('output_dir', 'data')) / f"{target_race_key}.json"
                    status_text.text("🔄 Playwrightでデータ取得中...")
                    progress_bar.progress(20)
                    result = subprocess.run(
                        [
                            sys.executable,
                            "scripts/scrape_worker.py",
                            f"--race_id={target_race_id}",
                            f"--race_type={settings.get('race_type', 'jra')}",
                            f"--output={output_file}"
                        ],
                        capture_output=True,
                        text=True,
                        timeout=180,
                        cwd=str(Path(__file__).parent.parent)
                    )
                    progress_bar.progress(80)
                    if result.returncode == 0 and output_file.exists():
                        with open(output_file, 'r', encoding='utf-8') as f:
                            scraped_data = json.load(f)
                        horse_count = len(scraped_data.get('horses', []))
                        if use_duplicate_check:
                            db_manager.save_race_data(scraped_data, target_race_id, target_race_key)
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
        st.button("⛔ 中断", disabled=not st.session_state.scraping_in_progress, use_container_width=True)

    if 'scraped_data' in st.session_state and st.session_state.scraped_data:
        data = st.session_state.scraped_data
        st.markdown("---")
        st.markdown(f"#### {data.get('race_name', '')} {data.get('race_grade', '')}")
        horses = data.get('horses', [])
        if horses:
            for horse in horses[:5]:
                col_a, col_b, col_c = st.columns([1, 3, 2])
                with col_a:
                    st.write(f"**{horse.get('horse_num', '')}**")
                with col_b:
                    st.write(horse.get('horse_name', ''))
                with col_c:
                    st.write(f"{horse.get('prediction_mark', '')} | {horse.get('jockey', '')}")
            if len(horses) > 5:
                st.caption(f"... 他 {len(horses) - 5} 頭")
    else:
        st.info("まだデータがありません。スクレイピングを実行してください。")
