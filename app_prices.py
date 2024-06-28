import requests
from base64 import b64encode
from Crypto.PublicKey.RSA import construct
from Crypto.Cipher import PKCS1_v1_5
import datetime
import time
from flask import Flask
import json
import threading
import os

app = Flask(__name__)


@app.route("/prices")
def prices():
    return json.dumps(prices)


@app.route("/ping")
def ping():
    return 'pong'


def encrypt(password, modulus, exponent):
    password = password.encode()

    modulus = int(modulus, 16)
    exponent = int(exponent, 16)

    pubkey = construct((modulus, exponent))
    pubkey = PKCS1_v1_5.new(pubkey)
    encrypted = pubkey.encrypt(password)

    return b64encode(encrypted).decode()


def get_session(login, password):
    s = requests.Session()

    r1 = s.post('https://steamcommunity.com/login/getrsakey/', data={'username': login})
    rsa_pass = encrypt(password, r1.json()["publickey_mod"], r1.json()["publickey_exp"])
    timestamp = r1.json()["timestamp"]

    s.post('https://steamcommunity.com/login/dologin/',
           data={'password': rsa_pass,
                 'username': login, 'twofactorcode': '', 'emailauth': '', 'loginfriendlyname': '',
                 'captchagid': '-1', 'captcha_text': '',
                 'emailsteamid': '',
                 'rsatimestamp': timestamp, 'remember_login': 'true'})

    return s.cookies


def get_items(start_item):
    while True:
        res = requests.get('https://steamcommunity.com/market/search/render/?query=&count=100&search_descriptions=0&'
                             'sort_column=name&sort_dir=asc&appid=' + appID + '&norender=1&start=' + start_item)
        items = res.json()
        if items is not None and items.get('success') is True:
            return items
        else:
            print(res.text)
            time.sleep(10)


def update_all_prices():
    global prices

    items = get_items('0')
    total_count = items['total_count']
    for i in range(len(items['results'])):
        if items['results'][i]['sell_listings'] > min_listings:
            price = items['results'][i]['sell_price'] / 100
            prices[items['results'][i]['hash_name']] = price
    
    print(total_count//100)
    for j in range(1, total_count//100):
        print(j)
        items = get_items(str(j*100))
        for i in range(len(items['results'])):
            if items['results'][i]['sell_listings'] > min_listings:
                price = items['results'][i]['sell_price'] / 100
                prices[items['results'][i]['hash_name']] = price


def price_updater():
    while True:
        update_all_prices()
        time.sleep(600)


if __name__ == "__main__":
    prices = {}

    session_cookies = get_session('login', 'password')
    
    appID = '730'
    min_listings = 30

    threading.Thread(target=price_updater).start()
    app.run(host='0.0.0.0', port=os.environ.get('PORT'))



