import os
import time
import pandas as pd
import datetime
from tqdm import tqdm
import yfinance as yf
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import numpy as np

# Function to scrape ticker symbols from provided URLs
def scrape_stock_tickers(excel_path, base_dir="stock_tickers", update=False):
    df = pd.read_excel(excel_path)

    os.makedirs(base_dir, exist_ok=True)
    driver = webdriver.Chrome()

    for index, row in df.iterrows():
        code = row['Code']
        url = row['URL']
        print(f"Processing {code} from {url}")

        exchange_dir = os.path.join(base_dir, code)
        os.makedirs(exchange_dir, exist_ok=True)
        output_path = os.path.join(exchange_dir, "tickers.txt")

        if not update and os.path.exists(output_path):
            print(f"Skipping {code}: tickers.txt already exists.")
            continue

        driver.get(url)
        wait = WebDriverWait(driver, 3)
        tickers = []

        while True:
            rows = driver.find_elements(By.XPATH, "//table//tbody/tr")
            for row in rows:
                try:
                    ticker = row.find_element(By.XPATH, "./td[2]").text.strip()
                    tickers.append(ticker)
                except Exception as e:
                    print(f"Error extracting ticker: {e}")

            try:
                next_button = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//button[.//span[text()='Next']]")
                ))
                driver.execute_script("arguments[0].click();", next_button)
                time.sleep(1)
            except Exception:
                print("No more 'Next' button or timeout.")
                break

        with open(output_path, "w") as f:
            for ticker in tickers:
                f.write(ticker + "\n")

        print(f"Saved {len(tickers)} tickers for {code} to {output_path}")

    driver.quit()


# Function to download or update ticker historical data
def download_ticker_data_from_scraped_list(
    excel_path,
    base_dir="stock_tickers",
    start_date="1900-01-01",
    max_tickers_per_exchange=10,
    delay=0.5,
    update=False
):
    end_date = str(datetime.date.today())
    stock_exchanges = pd.read_excel(excel_path)
    stock_exchanges['Code'] = stock_exchanges['Code'].astype(str).str.strip()

    # Limit to first 5 exchanges
    stock_exchanges = stock_exchanges.head(5)

    def download_daily_data(ticker, save_path, update_mode=False):
        if update_mode and os.path.exists(save_path):
            try:
                existing_df = pd.read_csv(save_path, index_col=0, parse_dates=True)
                if not existing_df.empty:
                    last_date = existing_df.index[-1].date()
                    new_start = str(last_date + pd.Timedelta(days=1))
                    if pd.to_datetime(new_start) > pd.to_datetime(end_date):
                        return  # Already up to date
                    new_df = yf.download(ticker, start=new_start, end=end_date, interval="1d", progress=False)
                    if not new_df.empty:
                        combined_df = pd.concat([existing_df, new_df[~new_df.index.isin(existing_df.index)]])
                        combined_df.to_csv(save_path)
                        return True
            except Exception as e:
                print(f"Error updating {ticker}: {e}")
        else:
            try:
                df = yf.download(ticker, start=start_date, end=end_date, interval="1d", progress=False, auto_adjust=True)
                if not df.empty and "Close" in df.columns:
                    df.to_csv(save_path)
                    return True
            except Exception as e:
                print(f"Failed to download {ticker}: {e}")
        return False

    for _, row in stock_exchanges.iterrows():
        code = row['Code']

        suffix_value = row.get('YFinance Suffix', '')
        if pd.isna(suffix_value) or str(suffix_value).strip().lower() == 'unknown':
            suffix = ''
        else:
            suffix = str(suffix_value).strip()

        if suffix == '':
            print(f"Using no suffix for {code}")
        else:
            print(f"Using suffix '{suffix}' for {code}")

        ticker_file_path = os.path.join(base_dir, code, "tickers.txt")
        if not os.path.isfile(ticker_file_path):
            print(f"Ticker file not found for {code}, skipping.")
            continue

        with open(ticker_file_path, 'r') as f:
            tickers = [line.strip() for line in f if line.strip()]

        tickers = tickers[:max_tickers_per_exchange]
        save_folder = os.path.join(base_dir, code)
        os.makedirs(save_folder, exist_ok=True)

        for ticker in tqdm(tickers, desc=f"Processing {code}"):
            full_ticker = f"{ticker}{suffix}"
            save_path = os.path.join(save_folder, f"{ticker}.csv")

            if not os.path.exists(save_path) or update:
                download_daily_data(full_ticker, save_path, update_mode=update)
                time.sleep(delay)

        for ticker in tqdm(tickers, desc=f"Processing {code}"):
            full_ticker = ticker if not suffix else f"{ticker}{suffix}"
            save_path = os.path.join(save_folder, f"{ticker}.csv")
            print(suffix)

            if not os.path.exists(save_path) or update:
                download_daily_data(full_ticker, save_path, update_mode=update)
                time.sleep(delay)


# === Run both steps below as needed ===

# Step 1: Scrape tickers
scrape_stock_tickers(
    excel_path=r"C:\Users\FX6300\Desktop\Stock_exchange_data\stock_exchanges_with_suffixes.xlsx",
    base_dir="stock_tickers",
    update=False  # Change to True if you want to refresh tickers
)

# Step 2: Download data
download_ticker_data_from_scraped_list(
    excel_path=r"C:\Users\FX6300\Desktop\Stock_exchange_data\stock_exchanges_with_suffixes.xlsx",
    base_dir="stock_tickers",
    update=False  # Change to False to skip re-downloading existing data
)
