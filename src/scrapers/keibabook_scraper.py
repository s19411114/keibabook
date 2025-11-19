#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
keibabook_scraper.py
- 地方競馬の「出馬表（syutuba）」と「馬柱（nouryoku_html）」の両ページに対応したJSON保存ツール（試作）
- 1ページ=1ファイルで、ページ内のテーブル群を可能な限り「そのまま」抽出してJSON化します
- 12Rのみ保存の試験運用オプション（--require-12r）付き
- かんたんGUI（--gui）同梱：URL貼付・保存先・ページ種別（自動/出馬表/馬柱）を選んで実行

依存:
  pip install requests beautifulsoup4 lxml
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse, urljoin
from urllib import robotparser

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup, Tag

# ---- HTTP セッション設定 -----------------------------------------------------

DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


def build_session(user_agent: str, timeout: int, retries: int = 3, backoff: float = 0.5) -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ja,en-US;q=0.7,en;q=0.5",
        "Cache-Control": "no-cache",
    })
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET", "HEAD"]),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.request_timeout = timeout  # type: ignore[attr-defined]
    return session


def is_allowed_by_robots(url: str, user_agent: str) -> bool:
    try:
        parsed = urlparse(url)
        robots_url = urljoin(f"{parsed.scheme}://{parsed.netloc}", "/robots.txt")
        rp = robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        return bool(rp.can_fetch(user_agent, url))
    except Exception:
        # 取得できない場合は許可扱い（必要に応じて False に変更）
        return True


def fetch_html(session: requests.Session, url: str) -> Tuple[str, str, int]:
    resp = session.get(url, timeout=getattr(session, "request_timeout", 15))
    if not resp.encoding or resp.encoding.lower() == "iso-8859-1":
        resp.encoding = resp.apparent_encoding or "utf-8"
    return resp.url, resp.text, resp.status_code


# ---- データモデル ------------------------------------------------------------

@dataclass
class RaceMeta:
    url: str
    final_url: str
    title: Optional[str] = None
    date: Optional[str] = None        # 例: 2025-10-03
    track: Optional[str] = None       # 例: 川崎/大井 etc.
    race_no: Optional[int] = None     # 例: 12
    race_name: Optional[str] = None
    start_time: Optional[str] = None  # 例: 20:50
    distance: Optional[str] = None    # 例: ダ1600m / 芝1200m
    weather: Optional[str] = None     # 例: 晴
    going: Optional[str] = None       # 例: 良/重 など


@dataclass
class TableData:
    label: str
    headers: List[str]
    rows: List[Dict[str, Any]]


@dataclass
class PageData:
    meta: RaceMeta
    page_type: str                   # "entry" | "pillar" | "auto" | "unknown"
    tables: List[TableData]
    notes: Dict[str, Any]


# ---- パース共通ユーティリティ ------------------------------------------------

def norm_text(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def extract_race_meta(soup: BeautifulSoup, url: str, final_url: str) -> RaceMeta:
    meta = RaceMeta(url=url, final_url=final_url)

    # title
    if soup.title:
        meta.title = norm_text(soup.title.get_text(" ", strip=True))

    # 日付（YYYY年M月D日 -> YYYY-MM-DD）
    page_text = soup.get_text(" ", strip=True)
    m = re.search(r"(20\d{2})年\s*(\d{1,2})月\s*(\d{1,2})日", page_text)
    if m:
        y, mo, d = m.groups()
        meta.date = f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"

    # R番号（12R/第12競走 など）
    for txt in [meta.title or "", page_text]:
        m1 = re.search(r"(\d{1,2})\s*R\b", txt)
        m2 = re.search(r"第\s*(\d{1,2})\s*競走", txt)
        if m1:
            meta.race_no = int(m1.group(1))
            break
        if m2:
            meta.race_no = int(m2.group(1))
            break

    # 競馬場（ヒューリスティック）
    tracks = ("川崎","大井","門別","盛岡","名古屋","佐賀","園田","高知","浦和","船橋","金沢","帯広","水沢","笠松","姫路")
    for t in tracks:
        if (meta.title and t in meta.title) or (page_text and t in page_text):
            meta.track = t
            break

    # 距離/発走/天候/馬場
    m_dist = re.search(r"(芝|ダート|ダ)\s*([0-9]{3,4})\s*m", page_text)
    if m_dist:
        meta.distance = f"{m_dist.group(1)}{m_dist.group(2)}m".replace("ダ", "ダ")

    m_time = re.search(r"(発走|出走)\s*[:：]?\s*([0-2]?\d:[0-5]\d)", page_text)
    if m_time:
        meta.start_time = m_time.group(2)

    m_weather = re.search(r"天候\s*[:：]\s*([^\s・/]+)", page_text)
    if m_weather:
        meta.weather = m_weather.group(1)

    m_going = re.search(r"(馬場|馬場状態)\s*[:：]\s*([^\s・/]+)", page_text)
    if m_going:
        meta.going = m_going.group(2)

    # レース名候補（大見出し）
    h_candidates: List[str] = []
    for tag_name in ("h1", "h2", "h3"):
        for h in soup.find_all(tag_name):
            text = norm_text(h.get_text(" ", strip=True))
            if text and any(k in text for k in ("R", "競走", "レース", "出馬", "出走", "馬柱", "能力")):
                h_candidates.append(text)
    if h_candidates:
        meta.race_name = sorted(h_candidates, key=len, reverse=True)[0]

    return meta


def detect_page_type_from_url(url: str) -> Optional[str]:
    u = urlparse(url).path.lower()
    if "nouryoku_html" in u:
        return "pillar"
    if "syutuba" in u:
        return "entry"
    return None


def detect_page_type(url: str, soup: BeautifulSoup) -> str:
    t = detect_page_type_from_url(url)
    if t:
        return t
    doc = soup.get_text(" ", strip=True)
    if "馬柱" in doc or "能力" in doc:
        return "pillar"
    if "出馬表" in doc or "出走表" in doc:
        return "entry"
    return "unknown"


def nearest_heading_label(tbl: Tag) -> Optional[str]:
    # 近傍の見出しテキストを取得（同階層→親方向→前方兄弟）
    # 1) caption
    cap = tbl.find("caption")
    if cap:
        t = norm_text(cap.get_text(" ", strip=True))
        if t:
            return t
    # 2) aria-label / data-title / title
    for attr in ("aria-label", "data-title", "title"):
        v = tbl.get(attr)
        if isinstance(v, str) and v.strip():
            return norm_text(v)
    # 3) 前方の見出し
    prev = tbl
    for _ in range(8):  # 近傍だけ
        prev = prev.previous_sibling
        if prev is None:
            break
        if isinstance(prev, Tag) and prev.name in ("h1", "h2", "h3", "h4"):
            t = norm_text(prev.get_text(" ", strip=True))
            if t:
                return t
    # 4) class/id から命名
    cid = []
    if tbl.get("id"):
        cid.append(f"#{tbl['id']}")
    if tbl.get("class"):
        cid.append("." + ".".join(tbl.get("class")))
    if cid:
        return "table(" + ",".join(cid) + ")"
    return None


def parse_table_to_rows(table: Tag) -> Tuple[List[str], List[Dict[str, Any]]]:
    rows = table.find_all("tr")
    if not rows:
        return [], []

    # ヘッダ行（thを含む連続領域）を抽出
    header_rows: List[List[str]] = []
    data_start = 0
    for i, tr in enumerate(rows):
        ths = tr.find_all("th")
        if ths:
            header_rows.append([norm_text(th.get_text(" ", strip=True)) for th in ths])
        else:
            data_start = i
            break
    if not header_rows:
        # thなし → 最初行をヘッダ扱い
        first = rows[0]
        header_rows = [[norm_text(td.get_text(" ", strip=True)) for td in first.find_all(["td", "th"])]]
        data_start = 1

    # 複数行ヘッダのマージ
    header = header_rows[0]
    for extra in header_rows[1:]:
        merged: List[str] = []
        for idx in range(max(len(header), len(extra))):
            a = header[idx] if idx < len(header) else ""
            b = extra[idx] if idx < len(extra) else ""
            if a and b:
                merged.append(f"{a}:{b}")
            else:
                merged.append(a or b)
        header = merged

    # データ行
    parsed: List[Dict[str, Any]] = []
    for tr in rows[data_start:]:
        tds = tr.find_all("td")
        if not tds:
            continue
        cells = [norm_text(td.get_text(" ", strip=True)) for td in tds]
        row: Dict[str, Any] = {}
        for i, cell in enumerate(cells[:len(header)]):
            key = header[i] if i < len(header) else f"col_{i}"
            key = key or f"col_{i}"
            row[key] = cell
            # href があればリンクも保存
            a = tds[i].find("a", href=True)
            if a and a["href"]:
                row[key + "_link"] = a["href"]
        parsed.append(row)

    # 空白ヘッダ補完
    header = [h if h else f"col_{i}" for i, h in enumerate(header)]
    return header, parsed


def extract_all_tables(soup: BeautifulSoup) -> List[TableData]:
    tables: List[TableData] = []
    for idx, tbl in enumerate(soup.find_all("table")):
        headers, rows = parse_table_to_rows(tbl)
        if not headers and not rows:
            continue
        label = nearest_heading_label(tbl) or f"table_{idx+1}"
        tables.append(TableData(label=label, headers=headers, rows=rows))
    return tables


# ---- スクレイプ本体 ---------------------------------------------------------

def scrape_page(url: str, session: requests.Session, page_type_hint: str = "auto") -> PageData:
    final_url, html, status = fetch_html(session, url)
    if status >= 400 or not html:
        raise RuntimeError(f"HTTP error {status} for {url}")

    soup = BeautifulSoup(html, "lxml")
    meta = extract_race_meta(soup, url, final_url)

    detected = detect_page_type(url, soup)
    page_type = detected if page_type_hint == "auto" else page_type_hint
    if page_type == "auto":
        page_type = detected

    tables = extract_all_tables(soup)

    # 補助メタ
    notes: Dict[str, Any] = {}
    for p, k in (("og:title", 'meta[property="og:title"]'),
                 ("og:description", 'meta[property="og:description"]')):
        el = soup.select_one(k)
        if el and el.get("content"):
            notes[p] = el["content"]

    return PageData(meta=meta, page_type=page_type, tables=tables, notes=notes)


# ---- 保存系 -----------------------------------------------------------------

def safe_slug(text: str) -> str:
    text = norm_text(text)
    text = re.sub(r"[\\/:*?\"<>|]+", "_", text)
    text = re.sub(r"\s+", "_", text)
    return text[:100] if text else "page"


def build_filename(meta: RaceMeta, page_type: str) -> str:
    parts: List[str] = []
    if meta.date:
        parts.append(meta.date)
    if meta.track:
        parts.append(meta.track)
    if meta.race_no is not None:
        parts.append(f"{meta.race_no}R")
    # ページ種別
    if page_type in ("entry", "pillar"):
        parts.append(page_type)
    # レース名
    if meta.race_name:
        parts.append(safe_slug(meta.race_name))
    elif meta.title:
        parts.append(safe_slug(meta.title))
    fname = "_".join(parts) if parts else "race_page"
    return f"{fname}.json"


def save_json(out_dir: str, data: PageData, pretty: bool = True) -> str:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    out_path = Path(out_dir) / build_filename(data.meta, data.page_type)
    payload = {
        "meta": asdict(data.meta),
        "page_type": data.page_type,
        "tables": [asdict(t) for t in data.tables],
        "notes": data.notes,
        "source": {
            "fetched_at": int(time.time()),
        },
    }
    with open(out_path, "w", encoding="utf-8") as f:
        if pretty:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        else:
            json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    return str(out_path)


# ---- CLI/GUI ----------------------------------------------------------------

def run_cli_single(
    url: str,
    out_dir: str,
    require_12r: bool,
    respect_robots: bool,
    pretty: bool,
    user_agent: str,
    timeout: int,
    page_type_hint: str,
) -> int:
    if respect_robots and not is_allowed_by_robots(url, user_agent):
        print(f"[SKIP] robots.txt により取得不可: {url}", file=sys.stderr)
        return 3

    session = build_session(user_agent=user_agent, timeout=timeout)
    try:
        data = scrape_page(url, session, page_type_hint=page_type_hint)
    except Exception as e:
        print(f"[ERROR] 取得/解析に失敗: {e}", file=sys.stderr)
        return 2

    if require_12r and data.meta.race_no is not None and data.meta.race_no != 12:
        print(f"[SKIP] {data.meta.race_no}R と判定。--require-12r 指定のためスキップ。", file=sys.stderr)
        return 4

    out_path = save_json(out_dir, data, pretty=pretty)
    print(f"[OK] 保存しました: {out_path}")
    return 0


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="地方競馬 出馬表/馬柱ページをJSON保存（試作・12R対応）")
    p.add_argument("url", help="対象URL（出馬表: .../syutuba/..., 馬柱: .../nouryoku_html/...）")
    p.add_argument("--out-dir", default="outputs", help="保存先ディレクトリ（既定: outputs）")
    p.add_argument("--require-12r", action="store_true", help="12Rページ以外は保存しない（既定: オフ）")
    p.add_argument("--respect-robots", action="store_true", help="robots.txt を尊重（既定: オフ）")
    p.add_argument("--no-pretty", action="store_true", help="JSONを圧縮保存（既定: 整形ON）")
    p.add_argument("--timeout", type=int, default=15, help="HTTPタイムアウト秒（既定: 15）")
    p.add_argument("--user-agent", default=DEFAULT_UA, help="User-Agent（既定: Chrome相当）")
    p.add_argument(
        "--page-type",
        choices=("auto", "entry", "pillar"),
        default="auto",
        help="ページ種別のヒント（auto=自動判定）",
    )
    p.add_argument("--gui", action="store_true", help="簡易GUIを起動")
    return p


def launch_gui() -> None:
    try:
        import tkinter as tk
        from tkinter import ttk, filedialog, messagebox
    except Exception as e:
        print(f"[ERROR] GUIモジュールを読み込めません: {e}", file=sys.stderr)
        sys.exit(2)

    root = tk.Tk()
    root.title("出馬表/馬柱スクレイパー（試作）")

    url_var = tk.StringVar(value="")
    out_var = tk.StringVar(value=str(Path("outputs").resolve()))
    r12_var = tk.BooleanVar(value=True)
    robots_var = tk.BooleanVar(value=False)
    pretty_var = tk.BooleanVar(value=True)
    timeout_var = tk.IntVar(value=15)
    ua_var = tk.StringVar(value=DEFAULT_UA)
    page_type_var = tk.StringVar(value="auto")

    def browse_out():
        d = filedialog.askdirectory(initialdir=out_var.get() or ".", title="保存先フォルダを選択")
        if d:
            out_var.set(d)

    def paste_examples(kind: str):
        if kind == "entry":
            url_var.set("https://s.keibabook.co.jp/chihou/syutuba/2025171003121112")
            page_type_var.set("entry")
        else:
            url_var.set("https://s.keibabook.co.jp/chihou/nouryoku_html/2025171003121112")
            page_type_var.set("pillar")

    def run_now():
        url = url_var.get().strip()
        if not url:
            messagebox.showerror("エラー", "URLを入力してください。")
            return
        root.config(cursor="watch")
        root.update_idletasks()
        code = run_cli_single(
            url=url,
            out_dir=out_var.get(),
            require_12r=r12_var.get(),
            respect_robots=robots_var.get(),
            pretty=pretty_var.get(),
            user_agent=ua_var.get(),
            timeout=timeout_var.get(),
            page_type_hint=page_type_var.get(),
        )
        root.config(cursor="")
        if code == 0:
            messagebox.showinfo("完了", "保存に成功しました。")
        elif code == 4:
            messagebox.showwarning("スキップ", "12Rではないためスキップしました。")
        else:
            messagebox.showerror("失敗", f"処理が失敗しました（コード: {code}）。")

    frm = ttk.Frame(root, padding=12)
    frm.grid(sticky="nsew")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    r = 0
    ttk.Label(frm, text="URL（出馬表 or 馬柱）:").grid(row=r, column=0, sticky="w")
    ttk.Entry(frm, textvariable=url_var, width=80).grid(row=r, column=1, sticky="ew", columnspan=3)
    r += 1

    ttk.Label(frm, text="ページ種別ヒント:").grid(row=r, column=0, sticky="w")
    ttk.Combobox(frm, textvariable=page_type_var, values=("auto", "entry", "pillar"), width=10, state="readonly").grid(row=r, column=1, sticky="w")
    ttk.Button(frm, text="出馬表例を貼る", command=lambda: paste_examples("entry")).grid(row=r, column=2, padx=6, sticky="w")
    ttk.Button(frm, text="馬柱例を貼る", command=lambda: paste_examples("pillar")).grid(row=r, column=3, padx=6, sticky="w")
    r += 1

    ttk.Label(frm, text="保存先:").grid(row=r, column=0, sticky="w")
    ttk.Entry(frm, textvariable=out_var, width=80).grid(row=r, column=1, sticky="ew", columnspan=2)
    ttk.Button(frm, text="参照...", command=browse_out).grid(row=r, column=3, padx=6, sticky="w")
    r += 1

    ttk.Label(frm, text="User-Agent:").grid(row=r, column=0, sticky="w")
    ttk.Entry(frm, textvariable=ua_var, width=80).grid(row=r, column=1, sticky="ew", columnspan=3)
    r += 1

    ttk.Label(frm, text="タイムアウト(秒):").grid(row=r, column=0, sticky="w")
    ttk.Entry(frm, textvariable=timeout_var, width=10).grid(row=r, column=1, sticky="w")
    r += 1

    ttk.Checkbutton(frm, text="12R以外は保存しない (--require-12r)", variable=r12_var).grid(row=r, column=0, columnspan=4, sticky="w")
    r += 1
    ttk.Checkbutton(frm, text="robots.txt を尊重 (--respect-robots)", variable=robots_var).grid(row=r, column=0, columnspan=4, sticky="w")
    r += 1
    ttk.Checkbutton(frm, text="JSONを整形して保存（オフで圧縮）", variable=pretty_var).grid(row=r, column=0, columnspan=4, sticky="w")
    r += 1

    ttk.Button(frm, text="実行", command=run_now).grid(row=r, column=0, pady=(10, 0), sticky="w")
    ttk.Button(frm, text="閉じる", command=root.destroy).grid(row=r, column=1, pady=(10, 0), sticky="w")

    for c in range(4):
        frm.columnconfigure(c, weight=1)

    root.mainloop()


def main() -> None:
    args = build_argparser().parse_args()
    if args.gui:
        launch_gui()
        return
    code = run_cli_single(
        url=args.url,
        out_dir=args.out_dir,
        require_12r=args.require_12r,
        respect_robots=args.respect_robots,
        pretty=not args.no_pretty,
        user_agent=args.user_agent,
        timeout=args.timeout,
        page_type_hint=args.page_type,
    )
    sys.exit(code)


if __name__ == "__main__":
    main()
