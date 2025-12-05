# -*- coding: utf-8 -*-
"""
Netkeiba DB スクレイパー（過去レース・馬成績・血統・払い戻し取得）
元コード: c:\GeminiCLI\TEST\scraper.py を keibabook 環境用に移植
"""
import os
import time
import re
import random
import logging
from io import StringIO
from typing import List, Dict, Any, Optional
from pathlib import Path

import requests
import pandas as pd
from tqdm import tqdm
from bs4 import BeautifulSoup
from requests.exceptions import RequestException

from src.utils.logger import get_logger

logger = get_logger(__name__)

# === 設定 ===
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/118.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0 Mobile Safari/537.36",
]

# === ネットワーク関連 (Session / Jitter / ヘッダ毎回上書き) ===
def fetch_url(session, url, timeout=10, max_retries=3, backoff=1.5):
    """
    Session 利用、リトライ、指数バックオフ＋Jitter を組み合わせた安全な取得
    毎回ランダムな User-Agent を headers で渡す（Session.headers のみ依存しない）
    """
    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            headers = {
                "User-Agent": random.choice(USER_AGENTS),
                "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
            }
            resp = session.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            # encoding の推定だが、EUC-JP が来るサイトではフォールバックを明示
            resp.encoding = resp.apparent_encoding or "EUC-JP"
            # ランダムスリープで過負荷抑止
            time.sleep(random.uniform(0.8, 2.2))
            return resp
        except RequestException as exc:
            last_exc = exc
            # 復旧待ち時間に jitter を追加
            wait_time = (backoff ** attempt) + random.uniform(0.1, 0.5)
            logger.warning(f"Request attempt {attempt} failed for {url}: {exc}. Retrying in {wait_time:.1f} sec...")
            time.sleep(wait_time)
    logger.error(f"All retries failed for {url}: {last_exc}")
    raise last_exc

# === テキスト正規化 / HTML パース関連 ===
def normalize_text(text):
    """全角スペース/半角/大文字小文字などの揺れを吸収する簡易正規化"""
    if text is None:
        return ""
    text = text.replace("\u3000", " ").replace("　", " ").strip()
    return text.lower()

def parse_table_by_summary(html_text, summary_value):
    """
    summary 属性で対象 table を優先検索。
    なければ caption / 親要素テキスト / 直前見出しの近傍でフォールバック検索。
    検索では正規化を行い、日本語の全角/半角差や大文字小文字差を吸収する。
    """
    soup = BeautifulSoup(html_text, "html.parser")
    table = soup.find("table", attrs={"summary": summary_value})
    if table is not None:
        return table

    candidates = soup.find_all("table")
    summary_norm = normalize_text(summary_value)

    for t in candidates:
        caption = t.find("caption")
        if caption and summary_norm in normalize_text(caption.get_text()):
            table = t
            break
        parent = t.find_parent()
        if parent:
            parent_text = parent.get_text(separator=" ", strip=True)
            parent_text_norm = normalize_text(parent_text)
            if summary_norm in parent_text_norm:
                prev_sibling = t.find_previous_sibling()
                if prev_sibling and summary_norm in normalize_text(prev_sibling.get_text(strip=True)):
                    table = t
                    break

    if table is None:
        logger.debug(f"Table summary '{summary_value}' not found. HTML snippet (first 1000 chars):\n{soup.prettify()[:1000]}")
    return table

# === スキーマ検証 ===
def validate_schema(df, expected_columns, context_id):
    """
    取得 DataFrame の列が期待通りか検証する。
    欠けがある場合は False を返す。余分な列は INFO レベルで通知。
    失敗時に df.head() をデバッグログ出力。
    """
    if df.empty:
        logger.info(f"DataFrame is empty for {context_id}. Skipping schema validation.")
        return True

    actual_set = set(df.columns)
    expected_set = set(expected_columns)

    missing_cols = expected_set - actual_set
    extra_cols = actual_set - expected_set

    if missing_cols:
        logger.error(f"Schema validation FAILED for {context_id}. Missing columns: {missing_cols}")
        logger.debug(f"Sample df.head() for {context_id}:\n{df.head().to_string()}")
        return False

    if extra_cols:
        logger.info(f"Schema validation: {context_id} has extra columns (usually OK): {extra_cols}")

    logger.debug(f"Schema validation PASSED for {context_id}")
    return True

# === データ取得クラス ===
class Results:
    """Netkeibaレース結果スクレイパー"""
    # 必ず運用前に実際のヘッダ名で更新してください（例: 着順, 馬番, 馬名, 騎手, タイム）
    EXPECTED_COLUMNS = ['着順', '馬番', '馬名', '騎手', 'タイム']

    @staticmethod
    def scrape(race_id_list: List[str], session: requests.Session) -> pd.DataFrame:
        """
        レース結果を取得
        
        Args:
            race_id_list: レースIDリスト（例: ["202406030811"]）
            session: requests.Session オブジェクト
            
        Returns:
            レース結果 DataFrame
        """
        race_results = {}
        for race_id in tqdm(race_id_list, desc="Results"):
            try:
                url = "https://db.netkeiba.com/race/" + race_id
                resp = fetch_url(session, url)
                html_text = resp.text

                table = parse_table_by_summary(html_text, "レース結果")
                if table is None:
                    logger.warning(f"No 'レース結果' table found for {race_id}")
                    continue

                df = pd.read_html(StringIO(str(table)))[0]

                if not validate_schema(df, Results.EXPECTED_COLUMNS, f"Race:{race_id}"):
                    logger.error(f"Skipping race {race_id} due to schema mismatch.")
                    continue

                soup = BeautifulSoup(html_text, "html.parser")
                data_intro_div = soup.find("div", attrs={"class": "data_intro"})
                race_info_text = ""
                if data_intro_div:
                    p_tags = data_intro_div.find_all("p")
                    race_info_text = " ".join([p.get_text(separator=" ").strip() for p in p_tags])

                # 距離と種別: 全角/半角 m に対応
                m = re.search(r"(芝|ダート|障).*?(\d{1,4})[mｍ]", race_info_text)
                if m:
                    df["race_type"] = [m.group(1)] * len(df)
                    df["course_len"] = [int(m.group(2))] * len(df)
                else:
                    if "芝" in race_info_text: 
                        df["race_type"] = ["芝"] * len(df)
                    elif "ダート" in race_info_text or "ダ" in race_info_text: 
                        df["race_type"] = ["ダート"] * len(df)

                w = re.search(r"天候[:：\s]*([^\s/]+)", race_info_text)
                if w: 
                    df["weather"] = [w.group(1)] * len(df)

                g = re.search(r"(良|稍重|重|不良)", race_info_text)
                if g: 
                    df["ground_state"] = [g.group(1)] * len(df)

                d = re.search(r"(\d{4}年\d{1,2}月\d{1,2}日)", race_info_text)
                if d:
                    df["date"] = [d.group(1)] * len(df)
                else:
                    date_tag = soup.find("span", attrs={"class": "race_date"})
                    if date_tag: 
                        df["date"] = [date_tag.get_text(strip=True)] * len(df)

                # horse_id / jockey_id を table から抽出。長さ不一致は警告して補完
                if table:
                    horse_links = table.find_all("a", href=re.compile(r"^/horse/"))
                    horse_id_list = [re.findall(r"\d+", a["href"])[0] for a in horse_links]
                    jockey_links = table.find_all("a", href=re.compile(r"^/jockey/"))
                    jockey_id_list = [re.findall(r"\d+", a["href"])[0] for a in jockey_links]

                    if len(horse_id_list) == len(df):
                        df["horse_id"] = horse_id_list
                    else:
                        logger.warning(f"horse_id count mismatch for {race_id}: table={len(df)} ids={len(horse_id_list)}")
                        df["horse_id"] = (horse_id_list + [None] * len(df))[:len(df)]

                    if len(jockey_id_list) == len(df):
                        df["jockey_id"] = jockey_id_list
                    else:
                        logger.warning(f"jockey_id count mismatch for {race_id}: table={len(df)} ids={len(jockey_id_list)}")
                        df["jockey_id"] = (jockey_id_list + [None] * len(df))[:len(df)]
                else:
                    logger.warning(f"result table object was missing for {race_id}")

                df.index = [race_id] * len(df)
                race_results[race_id] = df

            except Exception as e:
                logger.exception(f"Error scraping race {race_id}: {e}")
                continue

        if race_results:
            return pd.concat(race_results.values(), sort=False)
        logger.info("No race results scraped.")
        return pd.DataFrame()

class HorseResults:
    """Netkeiba馬成績スクレイパー"""
    # 必ず運用前に実ページのヘッダで更新してください
    EXPECTED_COLUMNS = ['日付', '開催', 'レース名', '着順']

    @staticmethod
    def scrape(horse_id_list: List[str], session: requests.Session) -> pd.DataFrame:
        """
        馬の過去成績を取得
        
        Args:
            horse_id_list: 馬IDリスト
            session: requests.Session オブジェクト
            
        Returns:
            馬成績 DataFrame
        """
        horse_results = {}
        for horse_id in tqdm(horse_id_list, desc="HorseResults"):
            try:
                url = f"https://db.netkeiba.com/horse/{horse_id}"
                resp = fetch_url(session, url)
                html_text = resp.text

                table = parse_table_by_summary(html_text, "履歴")
                if table is None:
                    soup = BeautifulSoup(html_text, "html.parser")
                    candidates = soup.find_all("table")
                    if candidates:
                        logger.warning(f"Using first table fallback for horse {horse_id}. This might be an unintended table.")
                        table = candidates[0]
                    else:
                        logger.warning(f"No table found for horse {horse_id}")
                        continue

                df = pd.read_html(StringIO(str(table)))[0]

                if not validate_schema(df, HorseResults.EXPECTED_COLUMNS, f"Horse:{horse_id}"):
                    logger.error(f"Skipping horse {horse_id} due to schema mismatch.")
                    continue

                df.index = [horse_id] * len(df)
                horse_results[horse_id] = df

            except Exception as e:
                logger.exception(f"Error scraping horse {horse_id}: {e}")
                continue

        if horse_results:
            return pd.concat(horse_results.values(), sort=False)
        logger.info("No horse results scraped.")
        return pd.DataFrame()

class Peds:
    """Netkeiba血統スクレイパー"""
    # 必ず運用前に実ページのヘッダで更新してください（ただし Peds は構造が多様）
    EXPECTED_COLUMNS = ['父', '母', '母父']

    @staticmethod
    def scrape(horse_id_list: List[str], session: requests.Session) -> pd.DataFrame:
        """
        血統情報を取得
        
        Args:
            horse_id_list: 馬IDリスト
            session: requests.Session オブジェクト
            
        Returns:
            血統 DataFrame
        """
        peds_results = {}
        for horse_id in tqdm(horse_id_list, desc="Peds"):
            try:
                url = f"https://db.netkeiba.com/horse/ped/{horse_id}"
                resp = fetch_url(session, url)
                html_text = resp.text

                table = parse_table_by_summary(html_text, "血統") or parse_table_by_summary(html_text, "系統")
                if table is None:
                    soup = BeautifulSoup(html_text, "html.parser")
                    candidates = soup.find_all("table")
                    if candidates:
                        logger.warning(f"Using first table fallback for pedigree {horse_id}. This might be an unintended table.")
                        table = candidates[0]
                    else:
                        logger.warning(f"No pedigree table found for {horse_id}")
                        continue

                df = pd.read_html(StringIO(str(table)))[0]

                # Peds は列構造が崩れやすいので簡易チェック
                if df.shape[1] < 2:
                    logger.warning(f"Pedigree table for {horse_id} looks small ({df.shape[0]}x{df.shape[1]}). Check integrity.")

                df.index = [horse_id] * len(df)
                peds_results[horse_id] = df

            except Exception as e:
                logger.exception(f"Error scraping pedigree for {horse_id}: {e}")
                continue

        if peds_results:
            return pd.concat(peds_results.values(), sort=False)
        logger.info("No pedigree data scraped.")
        return pd.DataFrame()

class Return:
    """Netkeiba払い戻しスクレイパー"""
    # 必ず運用前に実ページのヘッダで更新してください
    EXPECTED_COLUMNS = ['単勝', '複勝', '枠連', '馬連']

    @staticmethod
    def scrape(race_id_list: List[str], session: requests.Session) -> pd.DataFrame:
        """
        払い戻し情報を取得
        
        Args:
            race_id_list: レースIDリスト
            session: requests.Session オブジェクト
            
        Returns:
            払い戻し DataFrame
        """
        return_results = {}
        for race_id in tqdm(race_id_list, desc="Return"):
            try:
                url = f"https://db.netkeiba.com/race/{race_id}"
                resp = fetch_url(session, url)
                html_text = resp.text

                table = parse_table_by_summary(html_text, "払い戻し")
                if table is None:
                    logger.warning(f"No '払い戻し' table for {race_id}")
                    continue

                df = pd.read_html(StringIO(str(table)))[0]

                if not validate_schema(df, Return.EXPECTED_COLUMNS, f"Return:{race_id}"):
                    logger.error(f"Skipping return {race_id} due to schema mismatch.")
                    continue

                df.index = [race_id] * len(df)
                return_results[race_id] = df

            except Exception as e:
                logger.exception(f"Error scraping return for {race_id}: {e}")
                continue

        if return_results:
            return pd.concat(return_results.values(), sort=False)
        logger.info("No return data scraped.")
        return pd.DataFrame()


class NetkeibaDBScraper:
    """Netkeiba DB スクレイパーの統合インターフェース"""
    
    def __init__(self, output_dir: str = "data/netkeiba_archive"):
        """
        初期化
        
        Args:
            output_dir: 出力ディレクトリ
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        })
    
    def scrape_all(self, race_id_list: List[str]) -> Dict[str, pd.DataFrame]:
        """
        全データを一括取得
        
        Args:
            race_id_list: レースIDリスト
            
        Returns:
            {"results": DataFrame, "horses": DataFrame, "peds": DataFrame, "returns": DataFrame}
        """
        logger.info(f"Starting scraping for {len(race_id_list)} races. Please ensure robots.txt and site terms are respected.")
        
        # robots.txt を自動チェック（非強制）
        try:
            r = self.session.get("https://db.netkeiba.com/robots.txt", timeout=5)
            r.raise_for_status()
            logger.debug(f"robots.txt:\n{r.text[:1000]}")
        except Exception:
            logger.info("Could not fetch robots.txt; please verify crawl rules manually.")
        
        results = {}
        
        # 1) 払い戻し
        returns = Return.scrape(race_id_list, self.session)
        if not returns.empty:
            try:
                out_path = self.output_dir / "returns.csv"
                returns.to_csv(out_path, index=True, encoding='utf-8-sig')
                logger.info(f"Saved returns: {out_path}")
                results["returns"] = returns
            except Exception:
                logger.exception("Failed to save returns.csv")
        
        # 2) レース結果
        results_df = Results.scrape(race_id_list, self.session)
        if not results_df.empty:
            try:
                out_path = self.output_dir / "results.csv"
                results_df.to_csv(out_path, index=True, encoding='utf-8-sig')
                logger.info(f"Saved results: {out_path}")
                results["results"] = results_df
            except Exception:
                logger.exception("Failed to save results.csv")
            
            # 3) 馬ID を取得して馬成績・血統を取得
            horse_id_list = results_df.get("horse_id", pd.Series()).dropna().unique().tolist()
            if horse_id_list:
                logger.info(f"{len(horse_id_list)} unique horse IDs found; scraping horses and peds...")
                
                horse_df = HorseResults.scrape(horse_id_list, self.session)
                if not horse_df.empty:
                    try:
                        out_path = self.output_dir / "horses.csv"
                        horse_df.to_csv(out_path, index=True, encoding='utf-8-sig')
                        logger.info(f"Saved horses: {out_path}")
                        results["horses"] = horse_df
                    except Exception:
                        logger.exception("Failed to save horses.csv")
                
                peds_df = Peds.scrape(horse_id_list, self.session)
                if not peds_df.empty:
                    try:
                        out_path = self.output_dir / "peds.csv"
                        peds_df.to_csv(out_path, index=True, encoding='utf-8-sig')
                        logger.info(f"Saved peds: {out_path}")
                        results["peds"] = peds_df
                    except Exception:
                        logger.exception("Failed to save peds.csv")
            else:
                logger.info("No horse_id found in results; skipping horse/peds scraping.")
        
        logger.info("Scraping finished.")
        return results
    
    def close(self):
        """セッションをクローズ"""
        self.session.close()
