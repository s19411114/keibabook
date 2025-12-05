"""
修正版: 血統データパーサーのテスト
実際のHTML構造に合わせて修正
"""
import sys
sys.path.insert(0, '/mnt/c/GeminiCLI/TEST/keibabook')

from bs4 import BeautifulSoup

# 血統データのパース（修正版）
print("=== 血統データ（Pedigree）のテスト（修正版） ===")
with open('debug_files/debug_pedigree.html', 'r', encoding='utf-8') as f:
    pedigree_html = f.read()

soup = BeautifulSoup(pedigree_html, 'html.parser')
pedigree_data = {}

# 実際のHTML構造: table.kettou.sandai
pedigree_tables = soup.select("table.kettou.sandai")
print(f"見つかった血統テーブル数: {len(pedigree_tables)}")

for idx, table in enumerate(pedigree_tables):
    print(f"\\nテーブル {idx + 1}:")
    # テーブル内のリンクを確認
    links = table.select("a.umalink_click")
    if links:
        print(f"  馬のリンク数: {len(links)}")
        # 最初のリンク（父馬）
        if len(links) > 0:
            father = links[0].get_text(strip=True).replace('\\n', ' ')
            print(f"  父: {father}")
        # 母馬のリンクを探す（hinbaクラス内）
        mother_links = table.select("td.hinba a.umalink_click")
        if mother_links:
            mother = mother_links[0].get_text(strip=True).replace('\\n', ' ')
            print(f"  母: {mother}")
            if len(mother_links) > 1:
                mothers_father = mother_links[1].get_text(strip=True).replace('\\n', ' ')
                print(f"  母父: {mothers_father}")

# 馬番を取得する方法を探す
print("\\n=== 馬番の取得方法を調査 ===")
# 出馬表ページから馬番と血統の対応を取る必要がありそう
umaban_elements = soup.select(".umaban")
print(f"馬番要素数: {len(umaban_elements)}")
if umaban_elements:
    for elem in umaban_elements[:3]:
        print(f"  馬番: {elem.get_text(strip=True)}")
