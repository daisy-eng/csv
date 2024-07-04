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
options = webdriver.ChromeOptions()

prefs = {
     "download.default_directory": os.path.abspath(download_folder),  # ダウンロード先のディレクトリを設定
     "download.prompt_for_download": False,  # ダウンロード時の確認ダイアログを表示しない
     "download.directory_upgrade": True,  # ダウンロードディレクトリのセキュリティ設定を有効化
     "safebrowsing.enabled": True  # セーフブラウジングを有効に保つ
}

options.add_argument("--headless=new")
options.add_experimental_option("prefs", prefs)

# WebDriverの初期化
driver = webdriver.Remote(
             command_executor = 'http://selenium:4444/wd/hub',
             options = options
             )


url = 'https://www.jra.go.jp/' # テストでアクセスするURLを指定
driver.get(url)
print(driver)

time.sleep(3)
driver.save_screenshot('test.png') # アクセスした先でスクリーンショットを取得
print("ダウンロード完了")
driver.quit()