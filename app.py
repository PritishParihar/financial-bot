from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import pytz

app = Flask(__name__)

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
                   '{custom_indicator_22711_end} /  {custom_indicator_22714_start}'
                   'ema(  ema(  {custom_indicator_22712_start}"abs(  close - 1 candle ago close )"{custom_indicator_22712_end} , 25 ) , 13 )'
                   '{custom_indicator_22714_end} ) * 100"{custom_indicator_23679_end} <= 1 day ago  {custom_indicator_23680_start}'
                   'ema(  {custom_indicator_22715_start} "100 * (  {custom_indicator_22711_start}'
                   'ema(  ema(  {custom_indicator_22709_start} "close - 1 candle ago close"{custom_indicator_22709_end} , 25 ) , 13 )'
                   '{custom_indicator_22711_end} /  {custom_indicator_22714_start}'
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
        print(stock_data)
        
        TELEGRAM_TOKEN = '7449783431:AAHqe61k6R14Z_YismA2VEJYeXsACZbpgYg'
        CHAT_ID = '-1002199303920'
        strategy_name = "Strategy: TSI >= 0 Screener"
        
        # Convert DataFrame to Markdown table format for Telegram
        stock_data_str = stock_data.to_markdown(index=False)

        send_to_telegram(TELEGRAM_TOKEN, CHAT_ID, strategy_name)
        send_to_telegram(TELEGRAM_TOKEN, CHAT_ID, f"```\n{stock_data_str}\n```")

        return stock_data.to_html(index=False)

@app.route('/trigger', methods=['GET'])
def trigger():
    try:
        stock_data_html = execute_strategy()
        return stock_data_html, 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def schedule_task():
    scheduler = BackgroundScheduler()
    # Set the cron trigger to execute at 5 PM IST daily
    trigger = CronTrigger(hour=17, minute=0, timezone=pytz.timezone('Asia/Kolkata'))
    scheduler.add_job(execute_strategy, trigger)
    scheduler.start()

if __name__ == "__main__":
    schedule_task()
    app.run(host='0.0.0.0', port=9000)