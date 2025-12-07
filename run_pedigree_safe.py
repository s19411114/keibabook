import json, time, random, hashlib, datetime, requests, re, urllib.parse
from pathlib import Path
from bs4 import BeautifulSoup

USER_AGENT = 'keibabook-scraper/1.0 (+mailto:hiro_str@rakumail.jp)'
BASE_DELAY = 3.0
JITTER_RATIO = 0.5
OCCASIONAL_SLOW_P = 0.05
MAX_RETRY = 3
TIMEOUT = 20
UI_BLACKLIST = {'マイページ','ログイン','ログアウト','全メニュー','サポート','会社概要','プライバシーポリシー','お問い合わせ'}

def sha1(s): return hashlib.sha1(s.encode('utf-8')).hexdigest()
def now_iso(): return datetime.datetime.now().astimezone().isoformat()
def jitter_sleep():
    base = BASE_DELAY * (1 + random.uniform(-JITTER_RATIO, JITTER_RATIO))
    if random.random() < OCCASIONAL_SLOW_P:
        base += random.uniform(3.0,6.0)
    time.sleep(max(0.5, base))

def is_name_candidate(tok):
    if not tok: return False
    tok = tok.strip()
    if len(tok) < 2 or len(tok) > 24: return False
    if re.search(r'[A-Za-z0-9@:/\-_]', tok): return False
    if tok in UI_BLACKLIST: return False
    if not re.search(r'[\u4e00-\u9fff\u30a0-\u30ff]', tok): return False
    return True

pq = Path('pedigree_queue_small.json')
if not pq.exists():
    pq = Path('pedigree_queue.json')
if not pq.exists():
    print('no pedigree_queue found; abort'); raise SystemExit(0)

urls = json.load(open(pq,encoding='utf-8'))
store_dir = Path('pedigree_store'); store_dir.mkdir(parents=True, exist_ok=True)

for url in urls:
    pid = sha1(url); dest = store_dir / f'{pid}.json'
    if dest.exists():
        print('skip (exists):', url); continue
    ok = False
    for attempt in range(1, MAX_RETRY+1):
        try:
            print('fetching:', url, '(attempt', attempt, ')')
            r = requests.get(url, timeout=TIMEOUT, headers={'User-Agent': USER_AGENT})
            r.raise_for_status()
            s = BeautifulSoup(r.text, 'lxml')
            pedigree_section = None
            # prefer explicit pedigree containers
            selectors = [
                ("section", {"id": re.compile('pedigree|血統', re.I)}),
                ("div", {"class": re.compile('pedigree|血統', re.I)}),
                ("table", {"class": re.compile('pedigree|血統', re.I)}),
                ("div", {"id": re.compile('pedigree|血統', re.I)}),
            ]
            for name,attrs in selectors:
                try:
                    el = s.find(name, attrs=attrs)
                    if el and len(el.get_text(" ",strip=True))>10:
                        pedigree_section = el
                        break
                except Exception as e:
                    print('selector check error', e)
                    continue
            # fallback: first table that contains explicit labels
            if not pedigree_section:
                for tbl in s.select('table'):
                    t = tbl.get_text(" ", strip=True)
                    if re.search(r'父[:：\s]|種牡馬|母[:：\s]|母父|血統', t):
                        pedigree_section = tbl
                        break
            # label-driven extraction
            def extract_by_labels(sec):
                txt = sec.get_text(" ", strip=True)
                res = {'sire': None, 'dam': None, 'damsire': None}
                # direct patterns
                for lab, key in [(r'父','sire'),(r'種牡馬','sire'),(r'母の父|母父','damsire'),(r'母','dam')]:
                    m = re.search(lab + r'[:：\s]*([^\s　<>]{2,24})', txt)
                    if m and is_name_candidate(m.group(1)):
                        res[key] = m.group(1)
                # table-cell fallback within sec
                for tr in sec.select('tr'):
                    cells = [c.get_text(" ",strip=True) for c in tr.find_all(['th','td'])]
                    if len(cells)>=2:
                        k = cells[0]; v = cells[1]
                        if re.search(r'父|種牡馬', k) and is_name_candidate(v): res['sire']=v
                        if re.search(r'母$', k) and is_name_candidate(v): res['dam']=v
                        if re.search(r'母父|母の父', k) and is_name_candidate(v): res['damsire']=v
                return res
            lvl1 = {'sire':None,'dam':None,'damsire':None}
            if pedigree_section:
                lvl1 = extract_by_labels(pedigree_section)
            # page-level fallback but strict filtering (avoid UI tokens)
            if not any(lvl1.values()):
                page_txt = s.get_text(" ", strip=True)
                for lab, key in [(r'父','sire'),(r'種牡馬','sire'),(r'母の父|母父','damsire'),(r'母','dam')]:
                    m = re.search(lab + r'[:：\s]*([^\s　<>]{2,24})', page_txt)
                    if m and is_name_candidate(m.group(1)):
                        lvl1[key] = m.group(1)
            # level2/3 heuristic candidates from pedigree_section or page but filtered
            name_cands = []
            search_scope = pedigree_section if pedigree_section else s
            for el in search_scope.find_all(['a','td','th','li','div','span']):
                t = el.get_text(" ", strip=True)
                if not t or len(t)>120: continue
                parts = re.split(r'[\/\s、\(\)　]+', t)
                for p in parts:
                    if is_name_candidate(p) and p not in name_cands:
                        name_cands.append(p)
            g2_keys = ['paternal_grandsire','paternal_granddam','maternal_grandsire','maternal_granddam']
            g2 = {}
            filt = [x for x in name_cands if x not in (lvl1.get('sire'), lvl1.get('dam'), lvl1.get('damsire'))]
            for i,k in enumerate(g2_keys):
                g2[k] = filt[i] if i < len(filt) else None
            g3 = [x for x in filt[4:12]] if len(filt)>4 else []
            pedigree = {'url':url,'fetched_at': now_iso(), 'levels': {'1':lvl1, '2':g2, '3':g3}, 'raw_snippet': (pedigree_section.get_text(" ",strip=True)[:2000] if pedigree_section else s.get_text(" ",strip=True)[:2000])}
            with open(dest, 'w', encoding='utf-8') as fh:
                json.dump(pedigree, fh, ensure_ascii=False, indent=2)
            print('saved:', dest)
            ok = True
            break
        except Exception as e:
            print('error', e)
            if attempt < MAX_RETRY:
                time.sleep(30 * attempt)
                continue
            else:
                with open(dest, 'w', encoding='utf-8') as fh:
                    json.dump({'url':url,'error':str(e)}, fh, ensure_ascii=False, indent=2)
        finally:
            jitter_sleep()
    if not ok:
        print('failed to fetch after retries:', url)
print('done')
