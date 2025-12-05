"""
デバッグHTMLファイルからデータ抽出をテスト（修正版）
"""
import sys
sys.path.insert(0, '/mnt/c/GeminiCLI/TEST/keibabook')

from src.scrapers.keibabook import KeibaBookScraper

# テスト用の設定
settings = {
    'race_type': 'jra',
    'race_id': 'test',
    'shutuba_url': 'test',
    'skip_duplicate_check': True
}

scraper = KeibaBookScraper(settings)

# 血統データのパース
print("=== 血統データ（Pedigree）のテスト ===")
with open('debug_files/debug_pedigree.html', 'r', encoding='utf-8') as f:
    pedigree_html = f.read()

pedigree_data = scraper._parse_pedigree_data(pedigree_html)
print(f"取得した馬の数: {len(pedigree_data)}")
if pedigree_data:
    # 最初の3頭のデータを表示
    for idx in range(min(3, len(pedigree_data))):
        print(f"\\n馬 {idx + 1} のデータ:")
        print(pedigree_data[idx])
else:
    print("⚠️ 血統データが取得できませんでした")

print("\\n" + "="*50 + "\\n")

# 調教データのパース
print("=== 調教データ（Training）のテスト ===")
with open('debug_files/debug_training.html', 'r', encoding='utf-8') as f:
    training_html = f.read()

training_data = scraper._parse_training_data(training_html)
print(f"取得した馬の数: {len(training_data)}")
if training_data:
    # 最初の馬のデータを表示
    first_horse_num = list(training_data.keys())[0]
    print(f"\\n馬番 {first_horse_num} のデータ:")
    print(training_data[first_horse_num])
else:
    print("⚠️ 調教データが取得できませんでした")

print("\\n" + "="*50)
print("\\n✅ テスト完了！")
print(f"血統データ: {len(pedigree_data)}頭分")
print(f"調教データ: {len(training_data)}頭分")
