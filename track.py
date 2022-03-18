from typing import Tuple
import requests
import re
from bs4 import BeautifulSoup
import json
import os
import shutil
from gmail import GMail, Message
from time import sleep
import random
import sys

AVARAGE_INTERVAL = 2 * 3600 # Seconds
RANDOM_RANGE_INTERVAL = 1000
HEADERS = {
    'Host': 'www.amazon.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:70.0) Gecko/20100101 Firefox/70.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'TE': 'Trailers'
}
SESSION = requests.Session()
USER_DATA_FILE = 'user_data.json'


def get_user_data():
    if not os.path.isfile(USER_DATA_FILE):
        shutil.copyfile(f'.{USER_DATA_FILE}', USER_DATA_FILE)
        print(f"Initiated program, modify {USER_DATA_FILE} to your configuration, then run this file again")
        exit(0)

    data_file = open(USER_DATA_FILE)
    return json.load(data_file)


def check_amazon_product(url: str) -> Tuple[str, float]:
    soup = request_sender(url)
    product_name = soup.find(id='productTitle').get_text().strip()
    price = soup.find(id='price_inside_buybox').get_text()
    price = float(re.findall(r'\d+\.\d+', price)[0])

    return product_name, price


def request_sender(url):
    page = SESSION.get(url, headers=HEADERS)
    return BeautifulSoup(page.content, 'html.parser')


def send_mail_alert(product_url : str, product_name : str, current_price : float, warn_price : float) -> None:
    msg = Message('Amazon product price Alert',to=receiver,text='Your product: '
    f'{product_name} is currently listed for {current_price}$\n'
    f'You set an alert on this product at {warn_price}$.\n'
    f'Product link: {product_url}')
    gmail.send(msg)


def main():
    while True:
        for url, warn_price in tracked_products.items():
            product_name, current_price = check_amazon_product(url)
            if current_price <= warn_price:
                print(f"MATCH! {product_name} in {url} is currently sold for {current_price}$")
                current_try = tries = 5
                while not gmail.is_connected():
                    print(f"Lost connection to gmail, trying to reconnect ({tries - current_try}/{tries})")
                    if current_try <= 0: break
                    gmail.connect()
                    current_try -= 1
                else:
                    send_mail_alert(url, product_name, current_price, warn_price)
        sleep(AVARAGE_INTERVAL + ((random.random() * 2 - 1) * RANDOM_RANGE_INTERVAL))


data = get_user_data()
sender_user = "Amazon Price Tracker <{}>".format(data["sender_gmail_user"])
gmail = GMail(sender_user, data["sender_gmail_password"])
receiver = data["receiver_mail"]
gmail.connect()
tracked_products = data["tracked_products"]

if __name__ == '__main__':
    if "--daemon" in sys.argv:
        import daemon
        with daemon.DaemonContext():
            print("Starting tracker process, to check if the proccess is alive run:\n"
            "\"ps ax | grep tracker.py\" if it is alive there should be a python3 \"tracker.py\" in the output")
            main()
    else:
        main()