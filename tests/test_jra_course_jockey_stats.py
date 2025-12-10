import pytest
from src.scrapers.jra_special_parser import JRASpecialParser


def test_parse_course_jockey_stats_basic():
    parser = JRASpecialParser()
    html = """
    <html>
      <body>
        <table class="jockey_stats">
          <thead>
            <tr><th>騎手</th><th>勝率</th><th>連対率</th><th>騎乗数</th></tr>
          </thead>
          <tbody>
            <tr><td>吉田隼</td><td>12.5%</td><td>28.3%</td><td>80</td></tr>
            <tr><td>西村</td><td>8.3%</td><td>24.5%</td><td>60</td></tr>
          </tbody>
        </table>
      </body>
    </html>
    """
    result = parser.parse_course_jockey_stats(html)
    assert '吉田隼' in result
    assert result['吉田隼']['win_rate'] == pytest.approx(12.5)
    assert result['吉田隼']['top2_rate'] == pytest.approx(28.3)
    assert result['吉田隼']['rides'] == 80
    assert '西村' in result
    assert result['西村']['win_rate'] == pytest.approx(8.3)
    assert result['西村']['top2_rate'] == pytest.approx(24.5)
