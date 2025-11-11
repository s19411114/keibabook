import os
from src.utils.config import load_settings
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

class KeibaBookScraper:
    BASE_URL = "https://race.netkeiba.com/race/shutuba.html"

    def __init__(self, settings):
        self.settings = settings
        self.shutuba_url = settings['shutuba_url']

    async def _fetch_page_content(self, page, url):
        await page.goto(url, wait_until="domcontentloaded")
        content = await page.content()
        return content

    def _parse_race_data(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        race_data = {}

        # レース名とグレード
        racemei_p_elements = soup.select(".racemei p")
        if len(racemei_p_elements) > 1:
            race_data['race_name'] = racemei_p_elements[0].get_text(strip=True)
            race_data['race_grade'] = racemei_p_elements[1].get_text(strip=True)

        # 距離
        racetitle_sub_p_elements = soup.select(".racetitle_sub p")
        if len(racetitle_sub_p_elements) > 1:
            distance_text = racetitle_sub_p_elements[1].get_text(strip=True)
            # "1150m (ダート・右) 曇・良" のような形式から距離を抽出
            race_data['distance'] = distance_text.split(' ')[0]

        # 出馬表
        horses = []
        shutuba_table = soup.select_one(".syutuba_sp tbody")
        if shutuba_table:
            for row in shutuba_table.find_all('tr'):
                horse_num_elem = row.select_one(".umaban")
                horse_name_elem = row.select_one(".kbamei a")
                jockey_elem = row.select_one(".kisyu a")

                if horse_num_elem and horse_name_elem and jockey_elem:
                    horse_name_link = horse_name_elem['href'] if horse_name_elem.has_attr('href') else ""
                    horses.append({
                        'horse_num': horse_num_elem.get_text(strip=True),
                        'horse_name': horse_name_elem.get_text(strip=True),
                        'jockey': jockey_elem.get_text(strip=True),
                        'horse_name_link': horse_name_link
                    })
        race_data['horses'] = horses
        return race_data

    def _parse_training_data(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        training_data = {}

        training_table = soup.select_one("table.default.cyokyo tbody")
        if not training_table:
            return training_data

        rows = training_table.find_all('tr', recursive=False)
        current_horse_num = None
        
        i = 0
        while i < len(rows):
            row = rows[i]
            
            # 馬番、馬名、短評の行
            if row.select_one(".umaban") and row.select_one(".kbamei a"):
                horse_num_elem = row.select_one(".umaban")
                horse_name_elem = row.select_one(".kbamei a")
                tanpyo_elem = row.select_one(".tanpyo")

                current_horse_num = horse_num_elem.get_text(strip=True)
                training_data[current_horse_num] = {
                    'horse_name': horse_name_elem.get_text(strip=True),
                    'tanpyo': tanpyo_elem.get_text(strip=True) if tanpyo_elem else '',
                    'details': []
                }
                i += 1
                continue

            # 調教詳細の行
            elif current_horse_num and row.find('td', colspan='5'):
                detail_cell = row.find('td', colspan='5')
                
                elements = detail_cell.find_all(recursive=False)
                
                current_detail = None
                for elem in elements:
                    if elem.name == 'dl' and 'dl-table' in elem.get('class', []):
                        if current_detail:
                            training_data[current_horse_num]['details'].append(current_detail)
                        
                        current_detail = {}
                        date_location_elem = elem.select_one("dt.left")
                        oikiri_elem = elem.select_one("dt.right")
                        current_detail['date_location'] = date_location_elem.get_text(strip=True) if date_location_elem else ''
                        current_detail['追い切り方'] = oikiri_elem.get_text(strip=True) if oikiri_elem else ''
                        current_detail['times'] = []
                        current_detail['awase'] = ''

                    elif elem.name == 'table' and 'cyokyodata' in elem.get('class', []):
                        if current_detail:
                            time_elems = elem.select("tr.time td")
                            current_detail['times'] = [t.get_text(strip=True) for t in time_elems if t.get_text(strip=True)]
                            
                            awase_row = elem.select_one("tr.awase td.left")
                            if awase_row:
                                current_detail['awase'] = awase_row.get_text(strip=True)
                
                if current_detail:
                    training_data[current_horse_num]['details'].append(current_detail)
                
                i += 1
            else:
                i += 1
        return training_data

    def _parse_pedigree_data(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        pedigree_data = {}

        pedigree_table = soup.select_one(".PedigreeTable tbody")
        if pedigree_table:
            for row in pedigree_table.find_all('tr'):
                horse_num_elem = row.select_one(".HorseNum")
                father_elem = row.select_one(".Father")
                mother_elem = row.select_one(".Mother")
                mothers_father_elem = row.select_one(".MothersFather")

                if horse_num_elem and father_elem and mother_elem and mothers_father_elem:
                    horse_num = horse_num_elem.get_text(strip=True)
                    pedigree_data[horse_num] = {
                        'father': father_elem.get_text(strip=True),
                        'mother': mother_elem.get_text(strip=True),
                        'mothers_father': mothers_father_elem.get_text(strip=True)
                    }
        return pedigree_data

    def _parse_stable_comment_data(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        stable_comment_data = {}

        comment_divs = soup.select(".StableCommentTable .HorseComment")
        for comment_div in comment_divs:
            horse_num_elem = comment_div.select_one(".HorseNum")
            comment_elem = comment_div.select_one(".Comment")

            if horse_num_elem and comment_elem:
                horse_num = horse_num_elem.get_text(strip=True)
                stable_comment_data[horse_num] = comment_elem.get_text(strip=True)
        return stable_comment_data

    def _parse_previous_race_comment_data(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        previous_race_comment_data = {}

        comment_divs = soup.select(".PreviousRaceCommentTable .HorseComment")
        for comment_div in comment_divs:
            horse_num_elem = comment_div.select_one(".HorseNum")
            comment_elem = comment_div.select_one(".Comment")

            if horse_num_elem and comment_elem:
                horse_num = horse_num_elem.get_text(strip=True)
                previous_race_comment_data[horse_num] = comment_elem.get_text(strip=True)
        return previous_race_comment_data

    def _parse_horse_past_results_data(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        past_results = []

        results_table = soup.select_one(".HorsePastResultsTable tbody")
        if results_table:
            for row in results_table.find_all('tr'):
                columns = row.find_all('td')
                if len(columns) >= 7: # 日付, 開催, R, 着順, タイム, 騎手, 斤量
                    past_results.append({
                        'date': columns[0].get_text(strip=True),
                        'venue': columns[1].get_text(strip=True),
                        'race_num': columns[2].get_text(strip=True),
                        'finish_position': columns[3].get_text(strip=True),
                        'time': columns[4].get_text(strip=True),
                        'jockey': columns[5].get_text(strip=True),
                        'weight': columns[6].get_text(strip=True)
                    })
        return past_results

    async def scrape(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.settings.get("playwright_headless", True))
            page = await browser.new_page()
            try:
                # 血統ページのHTMLを取得して保存する
                pedigree_url = f"{'/'.join(self.settings['shutuba_url'].split('/')[:4])}/kettou/{self.settings['race_id']}"
                pedigree_html_content = await self._fetch_page_content(page, pedigree_url)
                with open("debug_pedigree.html", "w", encoding="utf-8") as f:
                    f.write(pedigree_html_content)
                
                # 今回はHTMLの取得が目的なので、ここで処理を中断するためにからの辞書を返す
                return {}

                # url = self.shutuba_url
                # html_content = await self._fetch_page_content(page, url)
                
                # # --- デバッグ用にHTMLをファイルに保存 ---
                # with open("debug_page.html", "w", encoding="utf-8") as f:
                #     f.write(html_content)
                # # ------------------------------------

                # race_data = self._parse_race_data(html_content)

                # # 調教データを取得してマージ
                # training_url = f"{'/'.join(self.settings['shutuba_url'].split('/')[:4])}/cyokyo/0/{self.settings['race_id']}"
                # training_html_content = await self._fetch_page_content(page, training_url)
                # with open("debug_training.html", "w", encoding="utf-8") as f:
                #     f.write(training_html_content)
                # parsed_training_data = self._parse_training_data(training_html_content)

                # for horse in race_data['horses']:
                #     horse_num = horse['horse_num']
                #     if horse_num in parsed_training_data:
                #         horse['training_data'] = parsed_training_data[horse_num]
                #     else:
                #         horse['training_data'] = {} # データがない場合は空の辞書

                # # 血統データを取得してマージ
                # pedigree_url = f"{'/'.join(self.settings['shutuba_url'].split('/')[:4])}/kettou/{self.settings['race_id']}"
                # pedigree_html_content = await self._fetch_page_content(page, pedigree_url)
                # with open("debug_pedigree.html", "w", encoding="utf-8") as f:
                #     f.write(pedigree_html_content)
                # parsed_pedigree_data = self._parse_pedigree_data(pedigree_html_content)

                # for horse in race_data['horses']:
                #     horse_num = horse['horse_num']
                #     if horse_num in parsed_pedigree_data:
                #         horse['pedigree_data'] = parsed_pedigree_data[horse_num]
                #     else:
                #         horse['pedigree_data'] = {} # データがない場合は空の辞書

                # # 厩舎の話データを取得してマージ
                # stable_comment_url = f"{'/'.join(self.settings['shutuba_url'].split('/')[:4])}/danwa/0/{self.settings['race_id']}"
                # stable_comment_html_content = await self._fetch_page_content(page, stable_comment_url)
                # with open("debug_stable_comment.html", "w", encoding="utf-8") as f:
                #     f.write(stable_comment_html_content)
                # parsed_stable_comment_data = self._parse_stable_comment_data(stable_comment_html_content)

                # for horse in race_data['horses']:
                #     horse_num = horse['horse_num']
                #     if horse_num in parsed_stable_comment_data:
                #         horse['stable_comment'] = parsed_stable_comment_data[horse_num]
                #     else:
                #         horse['stable_comment'] = "" # データがない場合は空文字列

                # # 前走コメントデータを取得してマージ
                # previous_race_comment_url = f"{'/'.join(self.settings['shutuba_url'].split('/')[:4])}/syoin/{self.settings['race_id']}"
                # previous_race_comment_html_content = await self._fetch_page_content(page, previous_race_comment_url)
                # with open("debug_previous_race_comment.html", "w", encoding="utf-8") as f:
                #     f.write(previous_race_comment_html_content)
                # parsed_previous_race_comment_data = self._parse_previous_race_comment_data(previous_race_comment_html_content)

                # for horse in race_data['horses']:
                #     horse_num = horse['horse_num']
                #     if horse_num in parsed_previous_race_comment_data:
                #         horse['previous_race_comment'] = parsed_previous_race_comment_data[horse_num]
                #     else:
                #         horse['previous_race_comment'] = "" # データがない場合は空文字列

                #     # 各馬の馬柱データを取得
                #     horse_detail_url = f"https://s.keibabook.co.jp{horse['horse_name_link']}" # horse_name_linkは後で追加
                #     horse_detail_html_content = await self._fetch_page_content(page, horse_detail_url)
                #     with open(f"debug_horse_{horse_num}.html", "w", encoding="utf-8") as f:
                #         f.write(horse_detail_html_content)
                #     horse_past_results = self._parse_horse_past_results_data(horse_detail_html_content)
                #     horse['past_results'] = horse_past_results

                # return race_data
            finally:
                await browser.close()