from selenium import webdriver
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
import requests

# 追加したやつ
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# 現在の日付と時刻を取得
yesterday = datetime.now() - timedelta(days=1)

formatted_yesterday = yesterday.strftime('%m/%d')
spreadsheet_id = '1i9btDvkMiXTgEj_ENGLlEoJHneztXNl4AIprqxM7Z3c'


month, day = formatted_yesterday.split('/', 1)

# Chromeのダウンロード設定
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']

# サービスアカウントキーのファイルパスとスコープを使用して認証
creds = ServiceAccountCredentials.from_json_keyfile_name('/work/credentials.json', scope)

download_folder = '/work/csv/vakure'

# Chromeオプションを設定
chrome_options = Options()
chrome_options.add_experimental_option("prefs", {
    "download.default_directory": download_folder,
    "download.prompt_for_download": False,  # ダウンロードの確認ダイアログを表示しない
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
})


driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

             
# 以下、元のスクリプトに従って処理を進める
url = "https://vakure.com/"
driver.get(url)
driver.maximize_window()

mail_element = driver.find_element(By.NAME, "mail")
mail_element.send_keys("kazuki.fukuda.ab@gmail.com")
pass_element = driver.find_element(By.NAME, "pass")
pass_element.send_keys("kSquK1LW")

login_button = driver.find_element(By.XPATH, '//input[@value="ログイン"]')
login_button.click()


url = f"https://vakure.com/view.php?type=report&target=media&date_A_Y=2024&date_A_M={month}&date_A_D={day}&date_B_Y=2024&date_B_M={month}&date_B_D={day}&date_A=2024%2F{month}%2F{day}&date_B=2024%2F{month}%2F{day}&date_type=-1d&result_row=20"
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

vakure_worksheet_name = "アカウント固有番号一覧"
vakureSheet = client.open_by_key(spreadsheet_id).worksheet(vakure_worksheet_name)
v_cell_range = 'B4:C'
f_cell_range = 'H4:I'

v_vakureData = vakureSheet.get(v_cell_range)
f_vakureData = vakureSheet.get(f_cell_range)

# 指定したフォルダ内のすべてのCSVファイルを検索
csv_files = glob.glob(os.path.join(download_folder, '*.csv'))
print(f"ダウンロードフォルダ内のCSVファイル数: {len(csv_files)}")
print(f"CSVファイル一覧: {csv_files}")

# 最も新しいファイルを見つける
latest_file = max(csv_files, key=os.path.getmtime)

# 最も新しいCSVファイルを読み込む
df = pd.read_csv(latest_file)
new_data_list = []
for index, row in df.iterrows():
    # 例えば、2列目と3列目のデータを新しいリストに追加
    new_data_list.append([formatted_yesterday, row[0], row[2],row[4],row[7]])
v_vakure_data_dict = {row[0]: row[1] for row in v_vakureData}
f_vakure_data_dict = {row[0]: row[1] for row in f_vakureData}
processed_data_list = []

for data in new_data_list:
    if '/' in data[1]:
        processed_data = [d.strip() if isinstance(d, str) else d for d in data]
        before_slash, after_slash = processed_data[1].split('/', 1)
        if before_slash in v_vakure_data_dict:
            # v_vakureDataから対応する値を使用
            corresponding_value = v_vakure_data_dict[before_slash]
            processed_data_list.append([data[0], corresponding_value, after_slash, data[2],data[3],data[4]])
        elif before_slash in f_vakure_data_dict:
            # f_vakureDataから対応する値を使用
            corresponding_value = f_vakure_data_dict[before_slash]
            processed_data_list.append([data[0], corresponding_value, after_slash, data[2],data[3],data[4]])
        else:
            # どちらの辞書にも一致するものがない場合は、before_slashを使用
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

