# safe pedigree fetcher (small-queue by default)
import json, time, random, hashlib, datetime, requests, re, urllib.parse
from pathlib import Path
from bs4 import BeautifulSoup

USER_AGENT = 'keibabook-scraper/1.0 (+mailto:hiro_str@rakumail.jp)'
BASE_DELAY = 3.0
JITTER_RATIO = 0.5
OCCASIONAL_SLOW_P = 0.05
MAX_RETRY = 3
TIMEOUT = 20

def sha1(s): return hashlib.sha1(s.encode('utf-8')).hexdigest()
def now_iso(): return datetime.datetime.now().astimezone().isoformat()
def jitter_sleep():
    base = BASE_DELAY * (1 + random.uniform(-JITTER_RATIO, JITTER_RATIO))
    if random.random() < OCCASIONAL_SLOW_P:
        base += random.uniform(3.0,6.0)
    time.sleep(max(0.5, base))

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
            # minimal structured capture: try to get father/mother/mother's father labels
            def find_label(patterns):
                for p in patterns:
                    el = s.find(text=re.compile(p))
                    if el:
                        block = el.parent.get_text(" ", strip=True)
                        m = re.search(p + r'[:：\s]*([^\s　<>]+)', block)
                        if m: return m.group(1)
                return None
            sire = find_label([r'父', r'種牡馬'])
            dam = find_label([r'母'])
            damsire = find_label([r'母父', r'母の父'])
            # best-effort collect name-like tokens for gens 2/3
            name_cands=[]
            for el in s.find_all(['a','td','th','li','div','span']):
                t = el.get_text(" ", strip=True)
                if not t or len(t)>120: continue
                parts = re.split(r'[/\s、\(\)　]+', t)
                for p in parts:
                    if 2<=len(p)<=24 and re.search(r'[\u4e00-\u9fff\u30a0-\u30ff]', p):
                        name_cands.append(p)
            # heuristic fill
            g2 = {}
            filt = [x for x in name_cands if x not in (sire, dam, damsire)]
            for i,k in enumerate(['paternal_grandsire','paternal_granddam','maternal_grandsire','maternal_granddam']):
                g2[k] = filt[i] if i < len(filt) else None
            g3 = [x for x in filt[4:12]] if len(filt)>4 else []
            pedigree = {'url':url,'fetched_at': now_iso(), 'levels': {'1':{'sire':sire,'dam':dam,'damsire':damsire}, '2':g2, '3':g3}, 'raw_snippet': s.get_text(" ", strip=True)[:2000]}
            with open(dest, 'w', encoding='utf-8') as fh:
                import json; json.dump(pedigree, fh, ensure_ascii=False, indent=2)
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
                    import json; json.dump({'url':url,'error':str(e)}, fh, ensure_ascii=False, indent=2)
        finally:
            jitter_sleep()
    if not ok:
        print('failed to fetch after retries:', url)
print('done')
