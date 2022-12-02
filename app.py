from flask import Flask
from flask import render_template, redirect, request, session, send_from_directory
import urllib
import requests
import os
from steampy.client import SteamClient, Asset
from collections import namedtuple
import json
import threading
import time

app = Flask(__name__)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/style.css')
def style():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'style.css')


@app.route('/script.js')
def script():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'script.js')


def canceller(bot, tradeofferid):
    time.sleep(60)
    bot.cancel_trade_offer(tradeofferid)


@app.route('/send_trade', methods=['POST'])
def send_trade():
    if session.get('steamid') and session.get('tradelink'):
        user_ids = request.args.to_dict()['my_ids'].split(',')
        bot_ids = request.args.to_dict()['bot_ids'].split(',')
        bot = int(request.args.to_dict()['bot'])

        if get_price_of_items(session['steamid'], user_ids) > get_price_of_items(bots_steamids[bot], bot_ids):
            user_asset = []
            bot_asset = []

            for i in range(len(user_ids)):
                user_asset.append(Asset(user_ids[i], game))

            if bot_ids != ['']:
                for i in range(len(bot_ids)):
                    bot_asset.append(Asset(bot_ids[i], game))

            trade = bots[bot].make_offer_with_url(bot_asset, user_asset, session['tradelink'], trade_message)

            if trade.get('strError'):
                return str(json.dumps({'error': trade['strError'], 'tradeofferid': 'error'}))
            else:
                threading.Thread(target=canceller, args=(bots[bot], trade['tradeofferid'])).start()
                return str(json.dumps({'tradeofferid': trade['tradeofferid']}))

    return str(json.dumps({'error': 'Set up your tradelink! Or bot or you lost some items. Try again.', 'tradeofferid': 'error'}))


@app.route('/get_user_inventory', methods=['POST'])
def get_user_inventory():
    if session.get('steamid'):
        r = requests.get('http://steamcommunity.com/inventory/' + session['steamid'] + '/' + appID + '/' + contextID + '?l=english&count=5000')
        inventory = r.json()
        i = 0
        inventory_to_return = []
        descriptions = inventory.get('descriptions')
        if descriptions:
            for j in range(len(descriptions)):
                if inventory['descriptions'][j]['tradable'] == 1 and prices.get(inventory['descriptions'][j]['market_hash_name']):
                    inventory_to_return.append([])
                    inventory_to_return[i].append(inventory['assets'][j]['assetid'])
                    inventory_to_return[i].append(inventory['descriptions'][j]['market_hash_name'])
                    inventory_to_return[i].append(inventory['descriptions'][j]['icon_url'])
                    inventory_to_return[i].append(prices[inventory['descriptions'][j]['market_hash_name']])
                    i += 1

            return str(json.dumps(inventory_to_return))

    return '[]'


@app.route('/get_bots_inventory', methods=['POST'])
def get_bots_inventory():
    inventory_to_return = []
    i = 0
    for bot in range(len(bots_steamids)):
        r = requests.get('http://steamcommunity.com/inventory/' + bots_steamids[bot] + '/' + appID + '/' + contextID + '?l=english&count=5000')
        inventory = r.json()
        descriptions = inventory.get('descriptions')
        if descriptions:
            for j in range(len(descriptions)):
                if inventory['descriptions'][j]['tradable'] == 1 and prices.get(inventory['descriptions'][j]['market_hash_name']):
                    inventory_to_return.append([])
                    inventory_to_return[i].append(inventory['assets'][j]['assetid'])
                    inventory_to_return[i].append(inventory['descriptions'][j]['market_hash_name'])
                    inventory_to_return[i].append(inventory['descriptions'][j]['icon_url'])
                    inventory_to_return[i].append(prices[inventory['descriptions'][j]['market_hash_name']])
                    inventory_to_return[i].append(bot)
                    i += 1

    return str(json.dumps(inventory_to_return))


@app.route('/set_tradelink', methods=['POST'])
def set_tradelink():
    if session.get('steamid'):
        tradelink = request.args.to_dict()['tradelink']
        start = tradelink.find('https://steamcommunity.com/tradeoffer/new/?partner=') + 51
        end = tradelink.find('&token=')
        if start != 50 and end != -1 and str(int(session['steamid'])-76561197960265728) == tradelink[start:end]:
            try:
                duration = bots[0].get_escrow_duration(tradelink)
            except ValueError:
                pass
            else:
                if duration == 0:
                    session['tradelink'] = tradelink
                    return 'success'

    return 'fail'


@app.route("/login")
def auth_with_steam():
    params = {
        'openid.ns': "http://specs.openid.net/auth/2.0",
        'openid.identity': "http://specs.openid.net/auth/2.0/identifier_select",
        'openid.claimed_id': "http://specs.openid.net/auth/2.0/identifier_select",
        'openid.mode': 'checkid_setup',
        'openid.return_to': request.url_root + 'validate',
        'openid.realm': request.url_root
    }

    auth_url = 'https://steamcommunity.com/openid/login?' + urllib.parse.urlencode(params)

    return redirect(auth_url)


@app.route("/validate")
def validate():
    jsn = request.args.to_dict()

    params = {
        'openid.ns': "http://specs.openid.net/auth/2.0",
        'openid.sig': jsn['openid.sig'],
        'openid.mode': 'check_authentication'
    }

    for key in jsn["openid.signed"].split(','):
        params['openid.' + key] = jsn['openid.'+key]

    r = requests.post('https://steamcommunity.com/openid/login?' + urllib.parse.urlencode(params))

    if r.text.split('\n')[1].split(':')[1] == 'true':
        steamid = request.args.to_dict()['openid.claimed_id'].split('/')[-1]
        session['steamid'] = steamid
        session['personaname'], session['avatar'] = GetPlayerSummaries(steamid)
        return redirect(request.url_root)
    else:
        return "Some problems occurred. Wait a while and try again."


@app.route('/logout')
def logout():
    for key in list(session.keys()):
        session.pop(key, None)
    return redirect(request.url_root)


@app.route("/")
def index():
    return render_template('index.html')


def GetPlayerSummaries(steamid):
    r = requests.get('http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key=' + steam_api_key + '&steamids=' + steamid)
    return r.json()['response']['players'][0]['personaname'], r.json()['response']['players'][0]['avatarmedium']


def get_price_of_items(steamid, items):
    r = requests.get('http://steamcommunity.com/inventory/' + steamid + '/' + appID + '/' + contextID + '?l=english&count=5000')
    inventory = r.json()
    price = 0
    descriptions = inventory.get('descriptions')
    if descriptions:
        for j in range(len(descriptions)):
            if inventory['descriptions'][j]['tradable'] == 1 and prices.get(inventory['descriptions'][j]['market_hash_name']) and inventory['assets'][j]['assetid'] in items:
                price += prices[inventory['descriptions'][j]['market_hash_name']]

    return price


def login_bot(username, password, steamid, shared_secret, identity_secret):
    steam_client = SteamClient('')

    steam_client.login(username, password, '''{
        "steamid": "''' + steamid + '''",
        "shared_secret": "''' + shared_secret + '''",
        "identity_secret": "''' + identity_secret + '''"
    }''')

    return steam_client


def login_bots(bots_json):
    bots = []
    bots_steamids = []
    last_bot = len(bots_json) - 1
    for i in range(last_bot):
        bots_steamids.append(bots_json[i]['steamid'])
        bots.append(login_bot(bots_json[i]['username'], bots_json[i]['password'], bots_json[i]['steamid'],
                              bots_json[i]['shared_secret'], bots_json[i]['identity_secret']))
        time.sleep(30)
    bots_steamids.append(bots_json[last_bot]['steamid'])
    bots.append(login_bot(bots_json[last_bot]['username'], bots_json[last_bot]['password'],
                          bots_json[last_bot]['steamid'], bots_json[last_bot]['shared_secret'],
                          bots_json[last_bot]['identity_secret']))
    return bots, bots_steamids
    
 
def prices_updater():
    global prices

    while True:
        prices = requests.get('https://steamprices-api.herokuapp.com/prices').json()
        time.sleep(3600)

    
def bot_relloger():
    global bots, bots_steamids

    while True:
        time.sleep(43200)
        bots, bots_steamids = login_bots(config["bots"])
    

if __name__ == "__main__":
    config = json.loads(open(app.root_path + '/config.json').read())
    
    bots, bots_steamids = login_bots(config["bots"])
    appID = config["appID"]
    contextID = config["contextID"]
    trade_message = config["trade_message"]
    steam_api_key = config["steam_api_key"]
    
    PredefinedOptions = namedtuple('PredefinedOptions', ['app_id', 'context_id'])
    game = PredefinedOptions(appID, contextID)
    
    prices = {}
    threading.Thread(target=prices_updater).start()
    
    threading.Thread(target=bot_relloger).start()
    
    app.secret_key = "whatasupersecretkey"
    app.debug = True
    app.run(port=1010, use_reloader=False)
