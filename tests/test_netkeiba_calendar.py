import asyncio
import datetime
import pytest
from unittest.mock import AsyncMock, patch

from src.scrapers.netkeiba_calendar import NetkeibaCalendarFetcher


@pytest.mark.asyncio
async def test_netkeiba_calendar_parse():
    # prepare a minimal calendar HTML that contains Tokyo and Kyoto on day 9
    sample_html = '''
    <html>
      <body>
        <table class="calendar">
          <tr>
            <td>
              <div class="date">9</div>
              <a href="/race/list.html?venue=tokyo">東京 1R 10:00 2R 10:40</a>
              <a href="/race/list.html?venue=kyoto">京都 1R 09:50</a>
            </td>
          </tr>
        </table>
      </body>
    </html>
    '''

    target_date = datetime.date.today().replace(day=9)

    with patch('src.scrapers.netkeiba_calendar.async_playwright') as mock_playwright:
        mock_pw = AsyncMock()
        mock_playwright.return_value.__aenter__.return_value = mock_pw
        mock_browser = AsyncMock()
        mock_pw.chromium.launch.return_value = mock_browser
        mock_context = AsyncMock()
        mock_browser.new_context.return_value = mock_context
        mock_page = AsyncMock()
        mock_context.new_page.return_value = mock_page
        mock_page.content = AsyncMock(return_value=sample_html)

        result = await NetkeibaCalendarFetcher.fetch_schedule_for_date(target_date)
        # It should detect Tokyo and Kyoto and parse times
        tokyo = next((r for r in result if r['venue'] == '東京'), None)
        kyoto = next((r for r in result if r['venue'] == '京都'), None)
        assert tokyo is not None and len(tokyo['races']) >= 2
        assert any(r['race_num'] == 1 and r['time'] == '10:00' for r in tokyo['races'])
        assert kyoto is not None and len(kyoto['races']) == 1
        assert kyoto['races'][0]['time'] == '09:50'
