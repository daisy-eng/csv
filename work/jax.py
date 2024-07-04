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

# 現在の日付と時刻を取得
yesterday = datetime.now() - timedelta(days=1)
formatted_yesterday = yesterday.strftime('%m/%d')
spreadsheet_id = '1Ml7groJUJ76GEsLEpgQ9l5ftlqG1iXyqbY-o4ebSqak'


month, day = formatted_yesterday.split('/', 1)

# Chromeのダウンロード設定
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']

# サービスアカウントキーのファイルパスとスコープを使用して認証
creds = ServiceAccountCredentials.from_json_keyfile_name('/Users/miyashitahiroshinozomi/ALBINO/asp/credentials.json', scope)

download_folder = '/Users/miyashitahiroshinozomi/ALBINO/asp/csv/jax'
chrome_options = Options()
prefs = {
    "download.default_directory": "/Users/miyashitahiroshinozomi/ALBINO/asp/csv/jax",  # ダウンロード先のディレクトリを設定
    "download.prompt_for_download": False,  # ダウンロード時の確認ダイアログを表示しない
    "download.directory_upgrade": True,  # ダウンロードディレクトリのセキュリティ設定を有効化
    "safebrowsing.enabled": True  # セーフブラウジングを有効に保つ
}
chrome_options.add_experimental_option("prefs", prefs)

# WebDriverの初期化
driver = webdriver.Chrome(options=chrome_options)

# 以下、元のスクリプトに従って処理を進める
url = "https://j-a-x-affiliate.net/"
driver.get(url)
driver.maximize_window()

mail_element = driver.find_element(By.NAME, "mail")
mail_element.send_keys("albonia@japan-solution.jp")
pass_element = driver.find_element(By.NAME, "pass")
pass_element.send_keys("1234565")

login_button = driver.find_element(By.XPATH, '//input[@value="ログイン"]')
login_button.click()


url = f"https://j-a-x-affiliate.net/view.php?type=report&target=media&date_A_Y=2024&date_A_M={month}&date_A_D={day}&date_B_Y=2024&date_B_M={month}&date_B_D={day}&date_A=2024%2F{month}%2F{day}&date_B=2024%2F{month}%2F{day}&date_type=point&result_row=20&page=6"

driver.get(url)

download_link = driver.find_element(By.XPATH, '//a[@title="検索結果をCSVダウンロード"]')
download_link.click()

iframe = WebDriverWait(driver, 10).until(
    EC.frame_to_be_available_and_switch_to_it((By.ID, "TB_iframeContent"))
)
utf8_radio_button = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.XPATH, '//input[@type="radio" and @value="UTF-8"]'))
)

utf8_radio_button.click()
element_inside_iframe = WebDriverWait(driver, 10).until(
    EC.visibility_of_element_located((By.XPATH, '//input[@type="submit" and @value="CSVファイルをダウンロード"]'))
)

element_inside_iframe.click()

# iframeからメインコンテンツに戻る
driver.switch_to.default_content()

# ダウンロードリンクをクリックする前の.csvファイルの数を取得
initial_csv_count = len(glob.glob(os.path.join(download_folder, '*.csv')))

# ダウンロード完了を待つ
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

driver.quit()

client = gspread.authorize(creds)


# 指定したフォルダ内のすべてのCSVファイルを検索
csv_files = glob.glob(os.path.join(download_folder, '*.csv'))

# 最も新しいファイルを見つける
latest_file = max(csv_files, key=os.path.getmtime)

# 最も新しいCSVファイルを読み込む
df = pd.read_csv(latest_file)
new_data_list = []
for index, row in df.iterrows():
    # 例えば、2列目と3列目のデータを新しいリストに追加
    new_data_list.append([formatted_yesterday, row[0], row[2],row[6],row[7]])
processed_data_list = []

for data in new_data_list:
    
    if '/' in data[1]:
        processed_data = [d.strip() if isinstance(d, str) else d for d in data]
        print(data[2])
        before_slash, after_slash = processed_data[1].split('/', 1)
        print(before_slash,after_slash)
        processed_data_list.append([data[0], before_slash, after_slash, data[2],data[3],data[4]])
    else:
        # '/'が含まれていない場合は元のデータをそのまま使用
        processed_data_list.append([data[0], data[1], "", data[2],data[3],data[4]])

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

