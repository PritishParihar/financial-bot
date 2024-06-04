import streamlit as st
import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
from datetime import datetime, timedelta
import pytz
import schedule
import time as time_module

# Define constants
CHARTINK_URL = 'https://chartink.com/screener/process'
CONDITION = {
    'scan_clause': '( {57960} ( latest {custom_indicator_23679_start}"(  {custom_indicator_22711_start}'
                   'ema(  ema(  {custom_indicator_22709_start} "close - 1 candle ago close"{custom_indicator_22709_end} , 25 ) , 13 )'
                   '{custom_indicator_22711_end} /  {custom_indicator_22714_start}'
                   'ema(  ema(  {custom_indicator_22712_start}"abs(  close - 1 candle ago close )"{custom_indicator_22712_end} , 25 ) , 13 )'
                   '{custom_indicator_22714_end} ) * 100"{custom_indicator_23679_end} < 0 and latest {custom_indicator_23680_start}'
                   'ema(  {custom_indicator_22715_start} "100 * (  {custom_indicator_22711_start}'
                   'ema(  ema(  {custom_indicator_22709_start} "close - 1 candle ago close"{custom_indicator_22709_end} , 25 ) , 13 )'
                   '{custom_indicator_22711_end} /  {custom_indicator_22714_start}'
                   'ema(  ema(  {custom_indicator_22712_start}"abs(  close - 1 candle ago close )"{custom_indicator_22712_end} , 25 ) , 13 )'
                   '{custom_indicator_22714_end} )"{custom_indicator_22715_end} , 13 )'
                   '{custom_indicator_23680_end} < 0 and latest {custom_indicator_23679_start}"(  {custom_indicator_22711_start}'
                   'ema(  ema(  {custom_indicator_22709_start} "close - 1 candle ago close"{custom_indicator_22709_end} , 25 ) , 13 )'
                   '{custom_indicator_22711_end} /  {custom_indicator_22714_start}'
                   'ema(  ema(  {custom_indicator_22712_start}"abs(  close - 1 candle ago close )"{custom_indicator_22712_end} , 25 ) , 13 )'
                   '{custom_indicator_22714_end} ) * 100"{custom_indicator_23679_end} > latest {custom_indicator_23680_start}'
                   'ema(  {custom_indicator_22715_start} "100 * (  {custom_indicator_22711_start}'
                   'ema(  ema(  {custom_indicator_22709_start} "close - 1 candle ago close"{custom_indicator_22709_end} , 25 ) , 13 )'
                   '{custom_indicator_22711_end} /  {custom_indicator_22714_start}'
                   'ema(  ema(  {custom_indicator_22712_start}"abs(  close - 1 candle ago close )"{custom_indicator_22712_end} , 25 ) , 13 )'
                   '{custom_indicator_22714_end} )"{custom_indicator_22715_end} , 13 )'
                   '{custom_indicator_23680_end} and 1 day ago  {custom_indicator_23679_start}"(  {custom_indicator_22711_start}'
                   'ema(  ema(  {custom_indicator_22709_start} "close - 1 candle ago close"{custom_indicator_22709_end} , 25 ) , 13 )'
                   '{custom_indicator_22711_end} /  1 day ago {custom_indicator_22714_start}'
                   'ema(  ema(  {custom_indicator_22712_start}"abs(  close - 1 candle ago close )"{custom_indicator_22712_end} , 25 ) , 13 )'
                   '{custom_indicator_22714_end} )"{custom_indicator_23679_end} <= 1 day ago {custom_indicator_23680_start}'
                   'ema(  {custom_indicator_22715_start} "100 * (  {custom_indicator_22711_start}'
                   'ema(  ema(  {custom_indicator_22709_start} "close - 1 candle ago close"{custom_indicator_22709_end} , 25 ) , 13 )'
                   '{custom_indicator_22711_end} /  1 day ago {custom_indicator_22714_start}'
                   'ema(  ema(  {custom_indicator_22712_start}"abs(  close - 1 candle ago close )"{custom_indicator_22712_end} , 25 ) , 13 )'
                   '{custom_indicator_22714_end} )"{custom_indicator_22715_end} , 13 )'
                   '{custom_indicator_23680_end} ) ) '
}

def fetch_csrf_token(session, url):
    response = session.get(url)
    soup = bs(response.content, "lxml")
    return soup.find("meta", {"name": "csrf-token"})["content"]

def fetch_stock_data(session, url, condition, headers):
    response = session.post(url, headers=headers, data=condition)
    return pd.DataFrame(response.json()["data"])

def send_to_telegram(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    return requests.post(url, data=payload).json()

def execute_strategy():
    with requests.Session() as session:
        csrf_token = fetch_csrf_token(session, CHARTINK_URL)
        headers = {"X-Csrf-Token": csrf_token}
        stock_data = fetch_stock_data(session, CHARTINK_URL, CONDITION, headers)
        
        TELEGRAM_TOKEN = '7449783431:AAHqe61k6R14Z_YismA2VEJYeXsACZbpgYg'
        CHAT_ID = '-4287405834'
        strategy_name = "Strategy: TSI >= 0 Screener"
        
        # Convert DataFrame to Markdown table format for Telegram
        stock_data_str = stock_data.to_markdown(index=False)

        send_to_telegram(TELEGRAM_TOKEN, CHAT_ID, strategy_name)
        send_to_telegram(TELEGRAM_TOKEN, CHAT_ID, f"```\n{stock_data_str}\n```")

        return stock_data

def job():
    execute_strategy()

def schedule_daily_job():
    ist = pytz.timezone('Asia/Kolkata')
    target_time = datetime.now(ist).replace(hour=7, minute=50, second=0, microsecond=0)
    if datetime.now(ist) > target_time:
        target_time += timedelta(days=1)

    seconds_until_target = (target_time - datetime.now(ist)).total_seconds()
    schedule.every().day.at("7:50").do(job)

    time.sleep(seconds_until_target)
    while True:
        schedule.run_pending()
        time_module.sleep(1)

def main():
    st.title("Stock Screener and Telegram Notifier")

    if st.button('Run Strategy'):
        with st.spinner('Executing strategy...'):
            try:
                stock_data = execute_strategy()
                st.success("Strategy executed successfully!")
                st.dataframe(stock_data)
            except Exception as e:
                st.error(f"Error executing strategy: {str(e)}")

    st.write("This app runs a stock screening strategy and sends the results to a Telegram channel.")

if __name__ == "__main__":
    main()
    schedule_daily_job()
