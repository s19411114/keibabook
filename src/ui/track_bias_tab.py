"""
Keibabook UI placeholder for Track Bias Tab

NOTE: This UI tab has been moved to keiba-ai migration. The full implementation
was copied to `migration/to_keiba_ai/src/ui/track_bias_tab.py`. This module is a
minimal shim to keep `import` compatibility and show a message in the UI.
"""
import streamlit as st


def render_track_bias_tab(db_manager, headless_mode=True):
    """
    トラックバイアス分析タブを描画
    
    Args:
        db_manager: DBマネージャーインスタンス
        headless_mode: ヘッドレスモードでブラウザを起動するか
    """
    st.header("🏇 トラックバイアス分析 (移行済)")
    st.info("このタブは keiba-ai に移管されました。詳細と履歴は migration/to_keiba_ai を参照してください。")
    
    # トラックバイアス履歴をアーカイブ表示
    _display_track_bias_archive(db_manager)
    
    st.markdown("---")
    
    # 保存済みレース一覧は保持するが、直接の取得は無効化
    try:
        race_ids = db_manager.get_race_ids()
    except Exception:
        race_ids = []
    
    if race_ids:
        selected_race_id = st.selectbox(
            "分析するレースを選択",
            race_ids,
            key="track_bias_race_select"
        )
        
        col_btn1, col_btn2 = st.columns([3, 1])
        
        with col_btn1:
            fetch_button = st.button("🔍 Netkeibaから結果を取得", type="primary")
        
        with col_btn2:
            if 'track_bias_data' in st.session_state:
                if st.button("🗑️ クリア"):
                    del st.session_state.track_bias_data
                    st.rerun()
        
            if fetch_button:
                st.warning("この機能は keiba-ai に移行しました。Netkeiba の直接スクレイピングは main では無効化されています。")
    else:
        st.info("📝 まずtab1でレースデータをスクレイピングしてください")
    
    st.markdown("---")
    st.write("トラックバイアスの取得と解析は keiba-ai に移行されました。GUI の再度有効化は移行完了後に検討してください。")


def _fetch_netkeiba_data(race_id: str, headless_mode: bool, db_manager):
    """Netkeibaからデータを取得する機能は keiba-ai に移行済みのため無効化されています。

    ここでは直接スクレイピングを行わず、ユーザーに keiba-ai で対応する旨を案内します。
    """
    st.info("Netkeiba のレース結果取得およびトラックバイアス分析は keiba-ai に移管されました。\n" \
            "keiba-ai が利用可能になったらこの機能を再有効化してください。")


def _display_track_bias(data: dict):
    """トラックバイアス指数を表示"""
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
        _display_top_horses(data)
    else:
        st.warning("⚠️ トラックバイアス指数を計算できませんでした（データ不足）")


def _display_top_horses(data: dict):
    """上位6頭の詳細を表示"""
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


def _display_track_bias_archive(db_manager):
    """トラックバイアス履歴をアーカイブ表示"""
    st.subheader("📚 トラックバイアスアーカイブ（過去30日）")
    
    # 会場フィルタ
    col_filter1, col_filter2 = st.columns([2, 3])
    
    with col_filter1:
        venue_filter = st.selectbox(
            "会場フィルタ",
            ["全会場", "東京", "京都", "中山", "阪神", "福島", "新潟", "札幌", "函館", "小倉", "中京"],
            key="bias_venue_filter"
        )
    
    venue = None if venue_filter == "全会場" else venue_filter
    
    # 履歴データ取得
    history = db_manager.get_track_bias_history(venue=venue, days=30)
    
    if history:
        st.markdown(f"**過去30日の記録**: {len(history)}件")
        
        # 要約統計
        inner_count = sum(1 for h in history if '内有利' in h.get('bias_type', ''))
        outer_count = sum(1 for h in history if '外有利' in h.get('bias_type', ''))
        front_count = sum(1 for h in history if '前有利' in h.get('bias_type', ''))
        closer_count = sum(1 for h in history if '後有利' in h.get('bias_type', ''))
        
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        with col_stat1:
            st.metric("内有利", f"{inner_count}件")
        with col_stat2:
            st.metric("外有利", f"{outer_count}件")
        with col_stat3:
            st.metric("前有利", f"{front_count}件")
        with col_stat4:
            st.metric("後有利", f"{closer_count}件")
        
        # 詳細リスト（コンパクト表示）
        with st.expander("📋 詳細リスト", expanded=False):
            for record in history[:20]:  # 最新20件のみ表示
                date_str = record.get('date', 'N/A')
                venue_str = record.get('venue', 'N/A')
                race_name = record.get('race_name', 'N/A')
                bias_type = record.get('bias_type', 'N/A')
                score = record.get('overall_bias_score', 0)
                
                st.markdown(f"**{date_str} {venue_str}** - {race_name}: `{bias_type}` (スコア: {score:.1f})")
    else:
        st.info("📝 まだアーカイブデータがありません。レース結果を取得してください。")
