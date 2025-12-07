from bs4 import BeautifulSoup
from src.utils.logger import get_logger

logger = get_logger(__name__)


def parse_race_data(html_content: str) -> dict:
    import re
    soup = BeautifulSoup(html_content, 'html.parser')
    race_data = {}

    # Race name and grade
    racemei_p_elements = soup.select(".racemei p")
    if len(racemei_p_elements) > 1:
        race_data['race_name'] = racemei_p_elements[0].get_text(strip=True)
        race_data['race_grade'] = racemei_p_elements[1].get_text(strip=True)

    racetitle_sub_p_elements = soup.select(".racetitle_sub p")
    if len(racetitle_sub_p_elements) > 1:
        full_condition = racetitle_sub_p_elements[1].get_text(strip=True)
        race_data['full_condition'] = full_condition
        distance_match = re.search(r'(\d+m)', full_condition)
        race_data['distance'] = distance_match.group(1) if distance_match else full_condition.split(' ')[0]
        course_match = re.search(r'\((.*?)\)', full_condition)
        race_data['course'] = course_match.group(1) if course_match else ''
        weather_match = re.search(r'\)\s*(.+)$', full_condition)
        race_data['weather_track'] = weather_match.group(1) if weather_match else ''
    if len(racetitle_sub_p_elements) > 0:
        race_data['race_class'] = racetitle_sub_p_elements[0].get_text(strip=True)

    racebase = soup.select_one('.racebase')
    if racebase:
        race_data['race_base_info'] = racebase.get_text(strip=True)

    time_elem = soup.select_one('.racetitle_sub .time, .starttime')
    if time_elem:
        race_data['start_time'] = time_elem.get_text(strip=True)

    # Horses
    horses = []
    shutuba_table = soup.select_one('.syutuba_sp tbody')
    if shutuba_table:
        for row in shutuba_table.find_all('tr'):
            horse_num_elem = row.select_one('.umaban')
            horse_name_elem = row.select_one('.kbamei a')
            jockey_elem = row.select_one('.kisyu a')
            if not (horse_num_elem and horse_name_elem):
                continue
            horse_data = {}
            waku_elem = row.select_one('.waku p')
            horse_data['waku'] = waku_elem.get_text(strip=True) if waku_elem else ''
            horse_data['horse_num'] = horse_num_elem.get_text(strip=True)
            mark_elem = row.select_one('.tmyoso')
            if mark_elem:
                myuma_mark = mark_elem.select_one('.myumamark')
                yoso_show = mark_elem.select_one('.js-yoso-show')
                star_mark = myuma_mark.get_text(strip=True) if myuma_mark else ''
                num_mark = yoso_show.get_text(strip=True) if yoso_show else ''
                horse_data['prediction_mark'] = f"{star_mark}{num_mark}".strip()
                yoso_detail = mark_elem.select_one('.js-yoso-detail, .yoso-detail')
                if yoso_detail:
                    individual_marks = {}
                    mark_rows = yoso_detail.select('tr, li, .yoso-item')
                    for mrow in mark_rows:
                        name_elem = mrow.select_one('th, .yoso-name, .name')
                        mark_cell = mrow.select_one('td, .yoso-mark, .mark')
                        if name_elem and mark_cell:
                            predictor_name = name_elem.get_text(strip=True)
                            predictor_mark = mark_cell.get_text(strip=True)
                            if predictor_name and predictor_mark:
                                individual_marks[predictor_name] = predictor_mark
                    horse_data['individual_marks'] = individual_marks
                else:
                    horse_data['individual_marks'] = {}
            else:
                horse_data['prediction_mark'] = ''
                horse_data['individual_marks'] = {}
            horse_data['horse_name'] = horse_name_elem.get_text(strip=True)
            horse_data['horse_name_link'] = horse_name_elem['href'] if horse_name_elem.has_attr('href') else ''
            kisyu_p = row.select_one('.kisyu')
            if kisyu_p:
                kisyu_text = kisyu_p.get_text(separator=' ', strip=True)
                age_match = re.search(r'([牡牝セ騸])(\d+)', kisyu_text)
                horse_data['sex'] = age_match.group(1) if age_match else ''
                horse_data['age'] = age_match.group(2) if age_match else ''
                horse_data['jockey'] = jockey_elem.get_text(strip=True) if jockey_elem else ''
                weight_match = re.search(r'\s(\d{2}(?:\.\d)?)\s*$', kisyu_text)
                if not weight_match:
                    weight_match = re.search(r'(\d{2}(?:\.\d)?)', kisyu_text.split(horse_data['jockey'])[-1] if horse_data['jockey'] else '')
                horse_data['weight'] = weight_match.group(1) if weight_match else ''
            else:
                horse_data['jockey'] = jockey_elem.get_text(strip=True) if jockey_elem else ''
                horse_data['sex'] = ''
                horse_data['age'] = ''
                horse_data['weight'] = ''
            tanpyo_elem = row.select_one('.tanpyo')
            horse_data['comment'] = tanpyo_elem.get_text(strip=True) if tanpyo_elem else ''
            all_tds = row.find_all('td')
            if all_tds:
                last_td = all_tds[-1]
                td_ps = last_td.find_all('p')
                if len(td_ps) >= 2:
                    odds_text = td_ps[1].get_text(strip=True) if len(td_ps) > 1 else ''
                    pop_text = td_ps[2].get_text(strip=True) if len(td_ps) > 2 else ''
                    odds_match = re.search(r'([\d.]+)', odds_text)
                    horse_data['odds'] = float(odds_match.group(1)) if odds_match else None
                    pop_match = re.search(r'(\d+)', pop_text)
                    horse_data['popularity'] = int(pop_match.group(1)) if pop_match else None
                else:
                    horse_data['odds'] = None
                    horse_data['popularity'] = None
            horse_data['odds_text'] = f"{horse_data.get('odds', '')} {horse_data.get('popularity', '')}人気" if horse_data.get('odds') else ''
            horses.append(horse_data)
    race_data['horses'] = horses

    # formation and comments
    boxsections = soup.select('.boxsection')
    for section in boxsections:
        title_elem = section.select_one('.title')
        if not title_elem:
            continue
        title = title_elem.get_text(strip=True)
        if title == '展開':
            pace_elem = section.select_one('p:not(.title)')
            if pace_elem and 'ペース' in pace_elem.get_text():
                race_data['pace'] = pace_elem.get_text(strip=True).replace('ペース', '').strip()
            formation = {}
            table = section.select_one('table')
            if table:
                for row in table.find_all('tr'):
                    ths = row.find_all('th')
                    tds = row.find_all('td')
                    for i, th in enumerate(ths):
                        if i < len(tds):
                            position = th.get_text(strip=True)
                            horses_text = tds[i].get_text(strip=True)
                            formation[position] = horses_text
            race_data['formation'] = formation
            all_ps = section.find_all('p')
            for p in all_ps:
                text = p.get_text(strip=True)
                if text and 'ペース' not in text and len(text) > 30:
                    race_data['formation_comment'] = text
                    break
        else:
            ps = section.find_all('p')
            for p in ps:
                text = p.get_text(strip=True)
                if text and len(text) > 50:
                    if 'race_comment' not in race_data:
                        race_data['race_comment'] = text
                    break

    return race_data
