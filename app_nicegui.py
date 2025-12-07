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

# --- Load settings and initialize
try:
    settings = load_settings()
except Exception:
    settings = {}

db = CSVDBManager()

# Some helper constants
VENUE_CODES = {
    "札幌": "01", "函館": "02", "福島": "03", "新潟": "04", "東京": "05",
    "中山": "06", "中京": "07", "京都": "08", "阪神": "09", "小倉": "10"
}

# Sidebar-like panel
with ui.row().classes('items-start gap-6'):
    with ui.column().style('width: 290px;'):
        ui.label('🐎 競馬ブックスクレイパー (NiceGUI prototype)')
        ui.separator()

        # Race type
        race_type = ui.radio(['中央 (JRA)', '地方 (NAR)'], value='中央 (JRA)')

        # Date
        now = datetime.now()
        today = date.today()
        default_date = today if now.hour < 17 else today + timedelta(days=1)
        date_input = ui.date(value=default_date)

        # venue
        venue_select = ui.select(items=list(VENUE_CODES.keys()), value=settings.get('venue', '東京'))

        # Race number grid
        selected_race = ui.number( value=1, min=1, max=12)
        ui.label('レース番号').classes('mt-2')
        # Simple row of 12 buttons
        def set_race(n):
            selected_race.value = n

        with ui.row().wrap(False).classes('gap-2 mt-1'): 
            for i in range(1,13):
                ui.button(f'{i}R', on_click=lambda e, n=i: set_race(n)).props('color=primary')

        # Login status
        status_label = ui.label('ログイン状況を確認中...')

        async def refresh_login():
            cookie_file = settings.get('cookie_file', 'cookies.json')
            is_valid, msg = KeibaBookAuth.is_cookie_valid(cookie_file)
            if is_valid:
                status_label.set_text(f'✅ ログイン済: {msg}')
            else:
                status_label.set_text(f'⚠️ 未ログイン: {msg}')

        ui.button('ログイン状態の更新', on_click=lambda: asyncio.create_task(refresh_login()))

        async def do_login():
            status_label.set_text('ログイン中...')
            try:
                result = await asyncio.create_subprocess_exec(
                    sys.executable, 'scripts/login_helper.py',
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await result.communicate()
                if result.returncode == 0:
                    status_label.set_text('✅ ログイン成功')
                else:
                    status_label.set_text('❌ ログイン失敗')
                    ui.notify(f'Login failed: {stderr.decode()[:200]}')
            except Exception as e:
                status_label.set_text('❌ エラー')
                ui.notify(str(e))

        ui.button('🔑 ログイン実行', on_click=lambda e: asyncio.create_task(do_login()))
        ui.button('🚪 ログアウト', on_click=lambda e: (os.remove(settings.get('cookie_file', 'cookies.json')) if os.path.exists(settings.get('cookie_file', 'cookies.json')) else None) or asyncio.create_task(refresh_login()))

        ui.separator()

        # Manual override inputs
        manual_race_id = ui.input(label='手動 レースID', value='')
        manual_url = ui.input(label='手動 URL', value='')

        # Execution options
        headless_checkbox = ui.checkbox('ヘッドレス', value=settings.get('playwright_headless', True))

        ui.button('🚀 データ取得', on_click=lambda e: asyncio.create_task(run_scrape()))

    # Main content column
    with ui.column().classes('grow'):
        json_area = ui.textarea(label='取得/表示JSON', value='', rows=20).style('width: 100%')
        log_area = ui.markdown('')

        # Simple list of saved files
        files_box = ui.select(items=[], label='保存済みデータ', value=None)


async def run_scrape():
    # Determine values
    selected_date_val = date_input.value
    date_str = selected_date_val.strftime('%Y%m%d')
    venue = venue_select.value
    race_num = int(selected_race.value)
    # Generate IDs (fall back to manual inputs if provided)
    venue_code = VENUE_CODES.get(venue, '00')
    generated_race_id = f"{date_str}{venue_code}{race_num:02d}"
    generated_race_key = f"{date_str}_{venue}{race_num}R"

    target_race_id = manual_race_id.value or generated_race_id
    target_url = manual_url.value or f"https://s.keibabook.co.jp/cyuou/syutuba/{target_race_id}"

    # Progress indicator
    log_area.set_text('Starting scrape...')
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, 'scripts/scrape_worker.py', f'--race_id={target_race_id}', f'--race_type=jra', f'--output=data/{generated_race_key}.json',
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode == 0:
            log_area.set_text('Scrape success')
            # load file
            out_file = Path('data') / f'{generated_race_key}.json'
            if out_file.exists():
                with open(out_file, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                json_area.set_value(json.dumps(content, ensure_ascii=False, indent=2))
                ui.notify('✅ データ取得完了')
            else:
                ui.notify('⚠️ 出力ファイルが見つかりません')
                if stderr:
                    ui.notify(stderr.decode()[:300])
        else:
            log_area.set_text('Scrape failed')
            if stderr:
                ui.notify(stderr.decode()[:300])

    except Exception as e:
        log_area.set_text(f'Error: {e}')
        ui.notify(str(e))


# Helper to refresh saved JSON list
def refresh_files():
    outdir = Path(settings.get('output_dir', 'data'))
    json_files = []
    if outdir.exists():
        json_files = [p.name for p in outdir.glob('*.json')]
    files_box.set_items(json_files)


@ui.page('/')
async def index():
    refresh_files()


if __name__ == '__main__':
    # Launch NiceGUI - if installed, this will run uvicorn/web server
    ui.run(title='KeibaBook NiceGUI Prototype', port=8080)
