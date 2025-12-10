"""
ARCHIVED: src/ui/training_evaluation_tab.py (Streamlit UI)
This Streamlit-based module was archived after migration to NiceGUI and keiba-ai.
"""
from src.utils.logger import get_logger

logger = get_logger(__name__)

def render_training_evaluation_tab(*args, **kwargs):
    logger.warning("src/ui/training_evaluation_tab.py is archived. Use NiceGUI/keiba-ai for training evaluation.")
    """調教早見表タブの描画"""
    st.header("🏇 調教早見表")
    
    st.markdown("""
    ### 調教評価システム（タイム換算方式）
    
    #### 📊 評価方法
    1. **追い切り方をタイム補正に変換**
       - 馬なり余力: **-0.5秒**（実質0.5秒速い）
       - 馬なり: **-0.4秒**（余裕あり）
       - G前強め: **-0.2秒**（良好）
       - 強め: **0.0秒**（そのまま）
       - G前一杯: **+0.3秒**（やや限界）
       - 一杯: **+0.6秒**（限界、実質0.6秒遅い）
    
    2. **調整後タイム = 実測タイム + 追い切り補正**
    
    3. **調整後タイムで順位をつけて5段階評価**
       - **S（◎）**: 上位20%（最高評価）
       - **A（○）**: 上位40%（良好）
       - **B（▲）**: 上位60%（普通）
       - **C（△）**: 上位80%（やや不安）
       - **D（☆）**: それ以下（要注意）
       - **⚠️**: 軽め調整（本番が調教代わり）
    """)
    
    # JSONファイル一覧を取得
    json_dir = Path("data/json")
    if not json_dir.exists():
        st.warning("data/json フォルダが見つかりません")
        return
    
    json_files = sorted(json_dir.glob("*.json"), reverse=True)
    
    if not json_files:
        st.warning("JSONファイルが見つかりません。先にスクレイピングを実行してください。")
        return
    
    # ファイル選択
    file_options = [f.stem for f in json_files]
    selected_file = st.selectbox(
        "📁 レースを選択",
        file_options,
        help="調教データを含むJSONファイルを選択"
    )
    
    if not selected_file:
        return
    
    # JSONファイルを読み込み
    json_path = json_dir / f"{selected_file}.json"
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            race_data = json.load(f)
        
        # 調教データを取得
        training_data = race_data.get('training_data', {})
        
        if not training_data:
            st.warning("⚠️ このレースには調教データがありません")
            return
        
        # レース情報を取得
        race_name = race_data.get('race_name', '不明')
        race_info = race_data.get('race_info', {})
        race_date_str = race_info.get('date', '')
        
        # レース日を推定
        race_date = None
        if race_date_str:
            try:
                # "2025年11月30日" のような形式をパース
                race_date = datetime.strptime(race_date_str, '%Y年%m月%d日').strftime('%Y-%m-%d')
            except ValueError:
                pass
        
        # レース概要を表示
        st.subheader(f"🏆 {race_name}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📅 レース日", race_date_str if race_date_str else '不明')
        with col2:
            st.metric("🐴 出走頭数", len(training_data))
        with col3:
            venue = race_info.get('venue', '不明')
            st.metric("🏟️ 会場", venue)
        
        st.divider()
        
        # 調教評価を実行
        with st.spinner('調教データを評価中...'):
            evaluation_results = evaluate_all_horses_training(training_data, race_date)
        
        if not evaluation_results:
            st.warning("⚠️ 評価可能な調教データがありません")
            return
        
        # 評価結果をテーブル表示
        st.subheader("📊 調教評価一覧")
        
        # DataFrame作成
        table_data = []
        for horse_num in sorted(evaluation_results.keys(), key=lambda x: int(x) if x.isdigit() else 999):
            data = evaluation_results[horse_num]
            eval_info = data['evaluation']
            training = data['last_training']
            
            # 馬名を取得（training_dataから）
            horse_name = training_data.get(horse_num, {}).get('horse_name', '')
            
            # ラスト1ハロンタイム
            converted_times = training.get('times_converted', [])
            last_time = converted_times[-1] if converted_times else ''
            
            # 元のタイム
            original_times = training.get('times', [])
            original_last = original_times[-1] if original_times else ''
            
            table_data.append({
                '馬番': horse_num,
                '馬名': horse_name,
                '印': eval_info.get('mark', eval_info['rank']),
                'ランク': eval_info['rank'],
                'スコア': f"{eval_info['score']}/5.0" if eval_info['score'] > 0 else '-',
                '調整後タイム': f"{eval_info.get('adjusted_time', 0):.1f}秒" if not eval_info['is_light'] else '-',
                '順位': f"{eval_info['time_rank']}位" if eval_info.get('time_rank') else '-',
                '日付・場所': training.get('date_location', ''),
                '追い切り方': training.get('追い切り方', ''),
                '実測ラスト1F': last_time if not eval_info['is_light'] else '-',
                '補正': f"{eval_info.get('oikiri_adjustment', 0):+.1f}秒" if eval_info.get('oikiri_adjustment') is not None and not eval_info['is_light'] else '-',
                '備考': eval_info.get('note', '')
            })
        
        df = pd.DataFrame(table_data)
        
        # ランク別に色分け
        def highlight_rank(row):
            rank = row['ランク']
            if rank == 'S':
                return ['background-color: #FFD700'] * len(row)  # ゴールド
            elif rank == 'A':
                return ['background-color: #C0C0C0'] * len(row)  # シルバー
            elif rank == 'B':
                return ['background-color: #F0F0F0'] * len(row)  # グレー
            elif rank == 'C':
                return ['background-color: #FFF8DC'] * len(row)  # コーンシルク
            elif rank == '⚠️':
                return ['background-color: #FFE4B5'] * len(row)  # モカシン（要注意）
            else:
                return [''] * len(row)
        
        styled_df = df.style.apply(highlight_rank, axis=1)
        st.dataframe(styled_df, use_container_width=True, height=600)
        
        st.divider()
        
        # 詳細表示
        st.subheader("📋 調教詳細")
        
        # ランク別フィルター
        rank_filter = st.multiselect(
            "ランクでフィルター",
            ['S', 'A', 'B', 'C', 'D', '⚠️'],
            default=['S', 'A', 'B']
        )
        
        # フィルター適用
        filtered_horses = [
            (horse_num, data) 
            for horse_num, data in evaluation_results.items()
            if data['evaluation']['rank'] in rank_filter
        ]
        
        # ランク順にソート
        rank_order = {'S': 0, 'A': 1, 'B': 2, 'C': 3, 'D': 4, '⚠️': 5}
        filtered_horses.sort(
            key=lambda x: (
                rank_order.get(x[1]['evaluation']['rank'], 6),
                -x[1]['evaluation']['score']
            )
        )
        
        # 詳細カード表示
        for horse_num, data in filtered_horses:
            eval_info = data['evaluation']
            training = data['last_training']
            horse_name = training_data.get(horse_num, {}).get('horse_name', '')
            
            # カード
            with st.container():
                rank = eval_info['rank']
                score = eval_info['score']
                
                # ヘッダー
                col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
                with col1:
                    st.markdown(f"### {horse_num}番")
                with col2:
                    st.markdown(f"**{horse_name}**")
                with col3:
                    if eval_info['is_light']:
                        st.markdown("### ⚠️ 調整中")
                    else:
                        st.markdown(f"### ランク: {rank}")
                with col4:
                    if not eval_info['is_light']:
                        st.markdown(f"**スコア: {score}/5.0**")
                
                # 調教情報
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"📅 **{training.get('date_location', '')}**")
                    st.markdown(f"⚡ **{training.get('追い切り方', '')}**")
                
                with col2:
                    # タイム表示
                    times_converted = training.get('times_converted', [])
                    times_original = training.get('times', [])
                    positions = training.get('positions', [])
                    
                    if times_converted:
                        time_display = []
                        for i in range(len(times_converted)):
                            conv = times_converted[i] if i < len(times_converted) else ''
                            orig = times_original[i] if i < len(times_original) else ''
                            pos = positions[i] if i < len(positions) else ''
                            
                            if conv != orig:
                                time_display.append(f"{conv}{pos}({orig})")
                            else:
                                time_display.append(f"{conv}{pos}")
                        
                        st.markdown(f"⏱️ **タイム**: {' - '.join(time_display)}")
                    
                    # 変換情報
                    training_center = training.get('training_center', '')
                    course = training.get('course', '')
                    if training_center and course:
                        st.markdown(f"✅ {training_center}{course} → 美浦南W換算")
                
                # 評価詳細
                if not eval_info['is_light']:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        time_rank = eval_info.get('time_rank')
                        if time_rank:
                            st.metric("タイム順位", f"{time_rank}位")
                    with col2:
                        st.metric("追い切り評価", f"{eval_info['oikiri_score']}/5.5")
                    with col3:
                        days_before = data.get('days_before_race', 0)
                        st.metric("調教実施", f"{days_before}日前")
                
                # 備考
                note = eval_info.get('note', '')
                if note:
                    st.info(f"💭 {note}")
                
                # 併せ馬・コメント
                awase = training.get('awase', '')
                comment = training.get('comment', '')
                
                if awase or comment:
                    with st.expander("詳細情報"):
                        if awase:
                            st.markdown(f"🐎 **併せ**: {awase}")
                        if comment:
                            st.markdown(f"💭 **コメント**: {comment}")
                
                st.divider()
        
        # テキスト出力オプション
        with st.expander("📄 テキスト形式で表示"):
            text_output = format_training_evaluation(evaluation_results)
            st.text(text_output)
            
            # ダウンロードボタン
            st.download_button(
                label="📥 テキストをダウンロード",
                data=text_output,
                file_name=f"training_evaluation_{selected_file}.txt",
                mime="text/plain"
            )
        
    except Exception as e:
        logger.error(f"調教評価エラー: {e}", exc_info=True)
        st.error(f"エラーが発生しました: {e}")


if __name__ == "__main__":
    render_training_evaluation_tab()
