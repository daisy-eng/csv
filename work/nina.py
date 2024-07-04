from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import glob
import pandas as pd
import time
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from datetime import datetime, timedelta
import re

# 現在の日付と時刻を取得
yesterday = datetime.now() - timedelta(days=1)
formatted_yesterday = yesterday.strftime('%m/%d')
spreadsheet_id = '1Ml7groJUJ76GEsLEpgQ9l5ftlqG1iXyqbY-o4ebSqak'


month, day = formatted_yesterday.split('/', 1)

# Chromeのダウンロード設定
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']

# サービスアカウントキーのファイルパスとスコープを使用して認証
creds = ServiceAccountCredentials.from_json_keyfile_name('/Users/miyashitahiroshinozomi/ALBINO/asp/credentials.json', scope)

download_folder = '/Users/miyashitahiroshinozomi/ALBINO/asp/csv/nina'
chrome_options = Options()
prefs = {
    "download.default_directory": "/Users/miyashitahiroshinozomi/ALBINO/asp/csv/nina",  # ダウンロード先のディレクトリを設定
    "download.prompt_for_download": False,  # ダウンロード時の確認ダイアログを表示しない
    "download.directory_upgrade": True,  # ダウンロードディレクトリのセキュリティ設定を有効化
    "safebrowsing.enabled": True  # セーフブラウジングを有効に保つ
}
chrome_options.add_experimental_option("prefs", prefs)

# WebDriverの初期化
driver = webdriver.Chrome(options=chrome_options)

# 以下、元のスクリプトに従って処理を進める
url = "https://nina.webapp.pink/mediamanager/login/"
driver.get(url)
driver.maximize_window()

mail_element = driver.find_element(By.NAME, "loginId")
mail_element.send_keys("albona")
pass_element = driver.find_element(By.NAME, "loginPass")
pass_element.send_keys("cmKPtEKvQ0")

login_button = driver.find_element(By.XPATH, '//input[@value="ログイン"]')
login_button.click()

url = f"https://nina.webapp.pink/mediamanager/?startDate=2024-{month}-{day}&endDate=2024-{month}-{day}&noClickViewFlg=0&mediaId=&advertiserSiteId=&submit=%E6%A4%9C%E7%B4%A2"

driver.get(url)

# 少し待機してページが読み込まれるのを待つ（必要に応じて）
time.sleep(5)  # 5秒間待機、ページによっては調整が必要

# スクリーンショットを撮る
screenshot_filename = os.path.join(download_folder, f"login_page_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")

download_link = WebDriverWait(driver, 10).until(
    EC.visibility_of_element_located((By.XPATH, '//a[contains(@class, "btn-mini") and contains(@class, "btn-primary") and contains(@class, "btn") and contains(text(), "CSVダウンロード")]'))
)
download_link.click()

initial_csv_count = len(glob.glob(os.path.join(download_folder, '*.csv')))

timeout = 120  # 最大待機時間 (秒)
start_time = time.time()
while True:
    current_csv_count = len(glob.glob(os.path.join(download_folder, '*.csv')))
    if current_csv_count > initial_csv_count:
        break  # 新しい.csvファイルがダウンロードフォルダに追加された
    elif time.time() - start_time > timeout:
        print("ダウンロードが完了するのを待機中にタイムアウトしました。")
        break
    time.sleep(1)

print(f"スクリーンショットを保存しました: {screenshot_filename}")

driver.quit()

client = gspread.authorize(creds)

nina_worksheet_name = "データ参照元"
ninaSheet = client.open_by_key(spreadsheet_id).worksheet(nina_worksheet_name)
nina_cell_range = 'B3:C'

nina_Data = ninaSheet.get(nina_cell_range)
new_nina_Data = []
for row in nina_Data:
    # row[1]が存在するかどうかをチェック
    if len(row) > 1:
        number_value = int(row[1].replace('¥', '').replace(',', ''))
        new_nina_Data.append([row[0], number_value])
    else:
        # row[1]が存在しない場合、デフォルトの値として0を設定
        new_nina_Data.append([row[0], 0])
nina_data_dict =  {row[0]: row[1] for row in new_nina_Data}

# # 指定したフォルダ内のすべてのCSVファイルを検索
csv_files = glob.glob(os.path.join(download_folder, '*.csv'))

# # 最も新しいファイルを見つける
latest_file = max(csv_files, key=os.path.getmtime)

# # 最も新しいCSVファイルを読み込む
df = pd.read_csv(latest_file, encoding='shift_jis', on_bad_lines='warn')
new_data_list = []
processed_data_list = []
for index, row in df.iterrows():
    # row[2] が 0 でないことを確認
    if row[2] != 0:
        # 広告コードとサイト名から【】を除去
        cleaned_string_media = re.sub(r'【ALB】', '', row[0])
        # 新しい配列に追加
        # row[2]はクリック数
        new_data_list.append([formatted_yesterday, cleaned_string_media, row[1], row[2],row[3]])

for data in new_data_list:
    if data[2] in nina_data_dict:
        multiplication_result = nina_data_dict[data[2]] * data[4]
        processed_data_list.append([data[0],data[1],data[2],data[3],data[4],multiplication_result])
    else:
        # どちらの辞書にも一致するものがない場合は、before_slashを使用
        processed_data_list.append([data[0],data[1],data[2],data[3],data[4]])

print(processed_data_list)
# スプシに反映
sheet = client.open_by_key(spreadsheet_id).worksheet("参照元")
num_rows = len(sheet.get_all_values())
# A2セルから開始して、new_data_listの全データを一度にスプレッドシートに書き込む
start_row = num_rows + 1
end_row = start_row + len(processed_data_list) - 1
cell_range = f'A{start_row}:F{end_row}'  # ここでは、A列からC列までの範囲を指定しています。

# 全データを一度に書き込む
sheet.update(cell_range, processed_data_list, value_input_option='USER_ENTERED')

# ダウンロードしたファイルを削除
os.remove(latest_file)
print(f"ファイル {latest_file} が削除されました。")

