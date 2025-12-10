"""
NiceGUI prototype for KeibaBook scraper
This is a minimal prototype that mirrors key functionality from the Streamlit app:
- Date, venue, race number selection
- Login check + login button
- "Get Data" button that triggers `scripts/scrape_worker.py` and shows JSON
- A simple data viewer for saved JSON files

Run: `python -m app_nicegui` or `python app_nicegui.py` (NiceGUI will start a uvicorn server)
"""
import asyncio
import json
import os
from pathlib import Path
from datetime import date, datetime, timedelta
import subprocess
import sys

from nicegui import ui, app

from src.utils.config import load_settings
from src.utils.db_manager import CSVDBManager
from src.utils.venue_manager import VenueManager
from src.utils.keibabook_auth import KeibaBookAuth
import json

# --- Load settings and initialize
try:
    settings = load_settings()
except Exception:
    settings = {}

db = CSVDBManager()

# Some helper constants
# Use VenueManager numeric codes for consistent JRA/NAR mapping
NUMERIC_CODES = VenueManager.NUMERIC_CODES
VENUE_CODES = NUMERIC_CODES
# JRA venue priority order (to match original Streamlit layout)
JRA_VENUES = ["東京","中山","阪神","京都","中京","福島","新潟","小倉","札幌","函館"]

# Inject default CSS for dark/light themes and provide a JS toggle
ui.add_head_html('''
<style>
    :root.kb-dark {
        --bg: #0e1117; --fg: #ffffff; --card: #1e2130; --accent: #4CAF50;
    }
    :root.kb-light {
        --bg: #ffffff; --fg: #111; --card: #f7f7f7; --accent: #0275d8;
    }
    :root.kb-dark, :root.kb-light { color-scheme: normal; }
    body { background-color: var(--bg); color: var(--fg); }
    input, textarea, select, button { background-color: var(--card); color: var(--fg); border-color: rgba(255,255,255,0.06) !important; }
    .kb-card, .nicegui-card, .q-card { background-color: var(--card); color: var(--fg); }
    .nicegui-button, .kb-button, button { background-color: var(--accent); color: #fff !important; border: none; }
    a { color: var(--accent); }
</style>
<script>
    function setKBTheme(dark) {
        try {
            if (dark) {
                document.documentElement.classList.add('kb-dark');
                document.documentElement.classList.remove('kb-light');
            } else {
                document.documentElement.classList.add('kb-light');
                document.documentElement.classList.remove('kb-dark');
            }
        } catch(e) {console.warn('theme toggle error', e)}
    }
    // default to dark at load
    try { setKBTheme(true); } catch(e){}
</script>
''')

# Helper to update the venue select based on race type (calls later in the UI build)
def _update_venue_options():
    # race_type and venue_select are created later in the UI; we'll reference them at call-time
    try:
        if race_type.value.startswith('地方'):
            opts = VenueManager.get_minami_kanto_venues() + ["――"] + VenueManager.get_other_venues()
        else:
            opts = JRA_VENUES

        default_v = settings.get('venue') if settings.get('venue') in opts else (opts[0] if opts else None)
        venue_select.set_options(opts)
        venue_select.value = default_v
        try:
            update_preview()
        except Exception:
            pass
    except Exception:
        pass

# Preview helper to show ID and link
def update_preview():
    try:
        sd = date_input.value
        ds = sd.strftime('%Y%m%d') if hasattr(sd,'strftime') else str(sd)
        vname = venue_select.value or ''
        rnum = int(selected_race.value) if selected_race.value else 1
        vc = VenueManager.get_venue_numeric_code(vname) or '00'
        gid = f"{ds}{vc}{rnum:02d}"
        base_path = 'chihou' if race_type.value.startswith('地方') else 'cyuou'
        gurl = f"https://s.keibabook.co.jp/{base_path}/syutuba/{gid}"
        try:
            preview_md.update(f'ID: {gid}  [🔗 出馬表]({gurl})')
        except Exception:
            pass
    except Exception:
        try:
            preview_md.update('ID: -')
        except Exception:
            pass

# Sidebar-like panel
with ui.row().classes('items-start gap-6'):
    with ui.column().style('width: 290px;'):
        ui.label('🐎 競馬ブックスクレイパー (NiceGUI prototype)')
        ui.markdown('軽量プロトタイプ: 左のサイドバーで種別（JRA/NAR）を切り替え、会場・レースを選んで「データ取得」してください。ログインは Playwright を利用します。')
        ui.separator()

        # Race type
        race_type = ui.radio(['中央 (JRA)', '地方 (NAR)'], value='中央 (JRA)', on_change=lambda e: _update_venue_options())

        # Date
        now = datetime.now()
        today = date.today()
        default_date = today if now.hour < 17 else today + timedelta(days=1)
        date_input = ui.date(value=default_date, on_change=lambda e: update_preview())

        # preview of generated ID/URL
        preview_md = ui.markdown('')

        # venue
        # Start with empty options; `_update_venue_options` will populate based on race type
        venue_select = ui.select([], value=None, label='会場（JRA/NARの切替あり）')
        # Populate the options according to the current race_type
        _update_venue_options()
        # update preview when selection changes
        try:
            venue_select.on_change(lambda e: update_preview())
        except Exception:
            pass

        # Race number grid (3 rows x 4 columns) with compact fixed-size buttons
        selected_race = ui.number(value=1, min=1, max=12)
        ui.label('レース番号').classes('mt-2')
        def set_race(n):
            selected_race.value = n
            update_preview()

        for row in range(3):
            with ui.row().classes('gap-2 mt-1'):
                for col_idx in range(4):
                    race_num = row * 4 + col_idx + 1
                    if race_num <= 12:
                        ui.button(
                            f"{race_num}R",
                            on_click=lambda e, n=race_num: set_race(n),
                        ).style('min-width: 48px; padding: 6px 8px; font-size: 13px;').props('color=primary')

        # Login status
        status_label = ui.label('ログイン状況を確認中...')
        # Small helper text: note about cookie persistence
        ui.label('※ クッキーが有効であればサーバーは cookies.json を参照して自動ログインします（サーバー再起動後も有効）').classes('text-sm')

        # Login credentials (can be left blank to use config/settings.yml)
        login_id_input = ui.input(label='ログインID', value=settings.get('login_id', ''))
        login_password_input = ui.input(label='ログインパスワード', value=settings.get('login_password', ''), password=True)

        async def refresh_login():
            cookie_file = settings.get('cookie_file', 'cookies.json')
            is_valid, msg = KeibaBookAuth.is_cookie_valid(cookie_file)
            if is_valid:
                status_label.set_text(f'✅ ログイン済: {msg}')
            else:
                status_label.set_text(f'⚠️ 未ログイン: {msg}')

        ui.button('ログイン状態の更新', on_click=lambda: asyncio.create_task(refresh_login()))
        # Run once at startup to reflect cookie/login status
        ui.timer(0, lambda: asyncio.create_task(refresh_login()), once=True)
        # Periodic refresh to keep status updated
        ui.timer(60, lambda: asyncio.create_task(refresh_login()), once=False)

        async def do_login():
            status_label.set_text('ログイン中...')
            log_area.set_value('ログインプロセスを開始しています...')

            # Use credentials from UI if provided; otherwise fallback to settings.yml
            env = dict(os.environ)
            if login_id_input.value:
                env['LOGIN_ID'] = login_id_input.value
            if login_password_input.value:
                env['LOGIN_PASSWORD'] = login_password_input.value

            try:
                proc = await asyncio.create_subprocess_exec(
                    sys.executable, 'scripts/login_helper.py',
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                    env=env
                )
                stdout, stderr = await proc.communicate()
                stdout_text = stdout.decode('utf-8', errors='replace')
                stderr_text = stderr.decode('utf-8', errors='replace')
                log_area.set_value('\n'.join(['ログイン出力:', '---', stdout_text, '---', stderr_text]))
                if proc.returncode == 0:
                    status_label.set_text('✅ ログイン成功')
                else:
                    status_label.set_text('❌ ログイン失敗')
                    ui.run(lambda: ui.notify('Login failed: see logs', color='negative'))
            except Exception as e:
                status_label.set_text('❌ エラー')
                log_area.set_value(f'エラー: {e}')
                ui.run(lambda: ui.notify(str(e), color='negative'))


        ui.button('🔑 ログイン実行', on_click=lambda e: asyncio.create_task(do_login())).classes('kb-button')
        ui.button('🚪 ログアウト', on_click=lambda e: (os.remove(settings.get('cookie_file', 'cookies.json')) if os.path.exists(settings.get('cookie_file', 'cookies.json')) else None) or asyncio.create_task(refresh_login()))

        ui.separator()

        # Manual override inputs
        manual_race_id = ui.input(label='手動 レースID', value='')
        manual_url = ui.input(label='手動 URL', value='')

        # Theme options
        # Theme switch: call client JS to toggle site theme
        dark_mode_checkbox = ui.switch('ダークモード (ブラウザ拡張に依存しない表示)', value=settings.get('dark_mode', True), on_change=lambda e: ui.run_javascript(f"setKBTheme({str(e.value).lower()})"))
        # Ensure the theme is applied on startup in case head JS didn't run or setting differs
        ui.timer(0, lambda: ui.run_javascript(f"setKBTheme({str(dark_mode_checkbox.value).lower()})"), once=True)

        # Execution options
        headless_checkbox = ui.checkbox('ヘッドレス', value=settings.get('playwright_headless', True))

        ui.button('🚀 データ取得', on_click=lambda e: asyncio.create_task(run_scrape())).classes('kb-button')
        # Archive viewer: show migration index and view files
        ui.button('📚 アーカイブ表示', on_click=lambda e: asyncio.create_task(open_archive_index()))

    # Main content column
    with ui.column().classes('grow'):
        json_area = ui.textarea(label='取得/表示JSON', value='').style('width: 100%; height: 360px;')
        log_area = ui.textarea(label='ログ/出力', value='').style('width: 100%; height: 160px;')

        # Simple list of saved files
        files_box = ui.select([], label='保存済みデータ', value=None)
        ui.button('📝 調教レポートを生成して表示', on_click=lambda e: asyncio.create_task(generate_training_report()))

        # Archive viewer area (hidden by default can be shown by button)
        archive_area = ui.textarea(label='アーカイブ索引/ファイル表示', value='').style('width: 100%; height: 360px;')
        archive_area.disable()
        # File open input for migration files
        open_file_input = ui.input(label='開くファイル (migration/からの相対パス例: to_keiba_ai/src/scrapers/netkeiba_result.py)')
        def do_open_file(e=None):
            path_val = open_file_input.value.strip()
            if not path_val:
                ui.notify('ファイルパスを入力してください', color='negative')
                return
            full = Path('migration') / Path(path_val)
            if not full.exists() or not full.is_file():
                ui.notify('ファイルが見つかりません', color='negative')
                return
            try:
                txt = full.read_text(encoding='utf-8')
                archive_area.set_value(txt[:50000] + ('\n\n... (truncated)' if len(txt) > 50000 else ''))
            except Exception as ex:
                ui.notify(f'ファイル読み込み失敗: {ex}', color='negative')

        ui.button('ファイルを開く', on_click=lambda e: do_open_file())
        ui.button('未読ドキュメント一覧を更新', on_click=lambda e: asyncio.create_task(load_unread_docs()))
        unread_count_label = ui.label('未読: 0 件')
        unread_box = ui.select([], label='未読ドキュメント', value=None)
        ui.button('未読を開く（選択中）', on_click=lambda e: asyncio.create_task(open_unread_selected()))
        ui.button('未読をマーク済みにする（選択中）', on_click=lambda e: asyncio.create_task(mark_unread_selected_read()))


async def run_scrape():
    # Determine values
    selected_date_val = date_input.value
    date_str = selected_date_val.strftime('%Y%m%d')
    venue = venue_select.value
    race_num = int(selected_race.value)
    # Generate IDs (fall back to manual inputs if provided)
    venue_code = VenueManager.get_venue_numeric_code(venue) or '00'
    generated_race_id = f"{date_str}{venue_code}{race_num:02d}"
    generated_race_key = f"{date_str}_{venue}{race_num}R"

    target_race_id = manual_race_id.value or generated_race_id
    # Choose URL domain depending on JRA/NAR
    base_path = 'chihou' if race_type.value.startswith('地方') else 'cyuou'
    target_url = manual_url.value or f"https://s.keibabook.co.jp/{base_path}/syutuba/{target_race_id}"

    # Progress indicator
    log_area.set_value('Starting scrape...')
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, 'scripts/scrape_worker.py', f'--race_id={target_race_id}', f"--race_type={'nar' if race_type.value.startswith('地方') else 'jra'}", f'--output=data/{generated_race_key}.json',
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode == 0:
            log_area.set_value('Scrape success')
            # load file
            out_file = Path('data') / f'{generated_race_key}.json'
            if out_file.exists():
                with open(out_file, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                json_area.set_value(json.dumps(content, ensure_ascii=False, indent=2))
                ui.run(lambda: ui.notify('✅ データ取得完了'))
            else:
                ui.run(lambda: ui.notify('⚠️ 出力ファイルが見つかりません'))
                if stderr:
                    ui.run(lambda: ui.notify(stderr.decode()[:300]))
        else:
            log_area.set_value('Scrape failed')
            if stderr:
                ui.run(lambda: ui.notify(stderr.decode()[:300]))

    except Exception as e:
        log_area.set_value(f'Error: {e}')
        ui.run(lambda: ui.notify(str(e)))


async def open_archive_index():
    # Display the generated migration/ARCHIVE_INDEX.md
    idx = Path('migration/ARCHIVE_INDEX.md')
    if not idx.exists():
        try:
            # Try to create using generator script if available
            proc = await asyncio.create_subprocess_exec(sys.executable, 'scripts/generate_migration_index.py', stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            await proc.communicate()
        except Exception:
            pass
    if idx.exists():
        txt = idx.read_text(encoding='utf-8')
        ui.run(lambda: archive_area.set_value(txt))
        ui.run(lambda: ui.notify('アーカイブ索引を読み込みました'))
    else:
        ui.run(lambda: ui.notify('ARCHIVE_INDEX.md が見つかりません', color='negative'))


async def load_unread_docs():
    try:
        with open('migration/DOC_MANIFEST.json', 'r', encoding='utf-8') as f:
            m = json.load(f)
        files = m.get('files', {})
        unread = [k for k, v in files.items() if not v.get('read')]
        unread_box.set_options(unread)
        ui.notify(f'未読 {len(unread)} 件を読み込みました')
        unread_count_label.set_text(f'未読: {len(unread)} 件')
    except Exception as e:
        ui.notify(f'読み込み失敗: {e}', color='negative')


async def open_unread_selected():
    v = unread_box.value
    if not v:
        ui.notify('ファイルを選択してください', color='negative')
        return
    full = Path(v)
    if not full.exists():
        ui.notify('ファイルが見つかりません', color='negative')
        return
    txt = full.read_text(encoding='utf-8')
    archive_area.set_value(txt[:50000] + ('\n\n... (truncated)' if len(txt) > 50000 else ''))


async def mark_unread_selected_read():
    v = unread_box.value
    if not v:
        ui.notify('ファイルを選択してください', color='negative')
        return
    # Mark via script to preserve format
    proc = await asyncio.create_subprocess_exec(sys.executable, 'scripts/mark_doc_read.py', '--path', v, '--actor', 'NiceGUI', stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    if proc.returncode == 0:
        ui.notify('マーク済みにしました')
        await load_unread_docs()
    else:
        ui.notify(f'マーク失敗: {stderr.decode()[:200]}', color='negative')


# Helper to refresh saved JSON list
def refresh_files():
    outdir = Path(settings.get('output_dir', 'data'))
    json_files = []
    if outdir.exists():
        json_files = [p.name for p in outdir.glob('*.json')]
    files_box.set_options(json_files)


async def generate_training_report():
    """
    Generate a simple HTML training report from a selected JSON file in `data` and open it.
    """
    try:
        sel = files_box.value
        if not sel:
            ui.notify('保存済みデータを選択してください', color='negative')
            return
        outdir = Path(settings.get('output_dir', 'data'))
        file_path = outdir / sel
        if not file_path.exists():
            ui.notify('選択ファイルが存在しません', color='negative')
            return
        # Read JSON
        cont = file_path.read_text(encoding='utf-8')
        obj = json.loads(cont)
        training = {}
        # Try to extract training_data from 'horses' entries if present
        for h in obj.get('horses', []):
            num = str(h.get('horse_num') or h.get('number') or '')
            if not num:
                continue
            # Some scrapers store training data under 'training_data' or 'training'
            if h.get('training_data'):
                training[num] = h.get('training_data')
            elif h.get('training'):
                training[num] = h.get('training')
        if not training:
            ui.notify('このレースの調教データが見つかりません', color='negative')
            return
        # Simple HTML generator based on existing test template
        html = f"""<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>調教レポート: {sel}</title><style>body{font-family:Arial,Helvetica,sans-serif;background:#0e1117;color:#fff;padding:20px} .card{background:#1e2130;padding:16px;border-radius:8px;margin-bottom:12px}</style></head><body><h1>調教レポート - {sel}</h1>"""
        for num, hdata in training.items():
            horse_name = hdata.get('horse_name','') if isinstance(hdata, dict) else ''
            html += f"<div class='card'><h2>{num}番 {horse_name}</h2>"
            details = hdata.get('details', []) if isinstance(hdata, dict) else []
            for d in details:
                html += f"<div><strong>{d.get('date_location','')}</strong> {d.get('追い切り方','')}<div>"
                times = d.get('times', [])
                times_conv = d.get('times_converted', [])
                html += '<div>'
                for i, t in enumerate(times):
                    conv = times_conv[i] if i < len(times_conv) else ''
                    if conv and conv != t:
                        html += f"<div><span style='color:#4CAF50'>{conv}</span> <small style='color:#999'>({t})</small></div>"
                    else:
                        html += f"<div><span>{t}</span></div>"
                html += '</div>'
                if d.get('awase'):
                    html += f"<div style='background:#223044;padding:8px;margin-top:6px;border-radius:6px'>併せ: {d.get('awase')}</div>"
                if d.get('comment'):
                    html += f"<div style='background:#2b2b24;padding:8px;margin-top:6px;border-radius:6px'>💬 {d.get('comment')}</div>"
                html += '</div>'
            html += '</div>'
        html += '</body></html>'

        outdir_report = outdir / 'reports'
        outdir_report.mkdir(parents=True, exist_ok=True)
        report_file = outdir_report / f"training_report_{sel.replace('.json','')}.html"
        report_file.write_text(html, encoding='utf-8')
        # Open in browser
        ui.open(f"/training_report/{report_file.name}")
        ui.notify('調教レポートを生成しました（新しいタブで開きます）')
    except Exception as e:
        ui.notify(f'エラー: {e}', color='negative')


# Populate files list on startup
refresh_files()

if __name__ in {"__main__", "__mp_main__"}:
    # Launch NiceGUI - if installed, this will run uvicorn/web server
    ui.run(title='KeibaBook NiceGUI Prototype', port=8080)


@app.get('/training_report/{name}')
def training_report_page(name):
    """Serve generated training report HTML files from data/reports."""
    try:
        p = Path('data') / 'reports' / name
        if not p.exists():
            from fastapi.responses import HTMLResponse
            return HTMLResponse(content=f"<h3>レポートが見つかりません: {name}</h3>", status_code=404)
        content = p.read_text(encoding='utf-8')
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=content, status_code=200)
    except Exception as e:
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=f"<h3>エラー: {e}</h3>", status_code=500)
