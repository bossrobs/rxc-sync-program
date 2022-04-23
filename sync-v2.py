#import module
from tkinter import *
from tkinter import messagebox
from turtle import width
import requests,json
from web3 import Web3
from eth_account.messages import encode_defunct
from datetime import datetime
from pypasser import reCaptchaV3
import pypasser

# Top level window
frame = Tk()
frame.title("RXC Sync")
frame.geometry('315x137')
  

options = []

options_file = open('data.json','r')
optionsfile = options_file.read()
optionsfile = json.loads(optionsfile)

i = 0
for user in optionsfile['data']:
    options.insert(i,user)
    i += 1



def get_characters(address):
    abi = '[{"inputs":[{"internalType":"address","name":"player","type":"address"}],"name":"getCharactersOfAddress","outputs":[{"internalType":"uint256[]","name":"","type":"uint256[]"},{"components":[{"internalType":"uint256","name":"tokenId","type":"uint256"},{"internalType":"uint256","name":"chaClass","type":"uint256"},{"internalType":"uint256","name":"chaSchool","type":"uint256"},{"internalType":"uint256","name":"chaStRemain","type":"uint256"},{"internalType":"uint256","name":"parentMaleTokenId","type":"uint256"},{"internalType":"uint256","name":"parentFemaleTokenId","type":"uint256"},{"internalType":"uint256","name":"breedCount","type":"uint256"},{"internalType":"uint256","name":"bornTimeStamp","type":"uint256"},{"internalType":"uint256","name":"transferCooldown","type":"uint256"},{"internalType":"uint256","name":"generation","type":"uint256"},{"internalType":"bool","name":"isBlocked","type":"bool"}],"internalType":"struct RxcCharacters.Character[]","name":"","type":"tuple[]"}],"stateMutability":"view","type":"function","constant":true,"signature":"0xcea28d7f"}]'

    TokenAddress = "0xED778A5e4eF180E52c2ec9d863Bf9Ff419036B46"
    bsc = "https://bsc-dataseed.binance.org/"
    web3 = Web3(Web3.HTTPProvider(bsc))
    contract_address = web3.toChecksumAddress(TokenAddress)
    abi = json.loads(json.dumps(abi))
    contract = web3.eth.contract(address=contract_address, abi=abi)
    Wallet_Data = json.dumps(contract.functions.getCharactersOfAddress(address).call())
    characters = json.loads(Wallet_Data)
    character_count = len(characters[0])
    
    return character_count

def get_nonce(address):
    try:
        reCaptcha_response = reCaptchaV3('https://www.google.com.ph/recaptcha/api2/anchor?ar=1&k=6LeZh4IcAAAAAI7foL4X_gcEHdXquHXfc39JU_kY&co=aHR0cHM6Ly9yeGMucmFuLm5ldHdvcms6NDQz&hl=en&v=QENb_qRrX0-mQMyENQjD6Fuj&size=invisible&cb=ys0l0yutd9i2')
        url = "https://rxc-prod-api.ran.network/metamask/request"
        r = requests.post(url,data={"address": address,"g-recaptcha-response": reCaptcha_response})
        nonce = r.json()
        nonce = nonce['data']

        return nonce
    except pypasser.exceptions.ConnectionError:
        messagebox.showerror("Error","Can't Get Captcha")
        
    

def get_token(address,signature):
    url = "https://rxc-prod-api.ran.network/metamask/verify"
    r = requests.post(url,data={"address": address,"signature": signature})
    session = r.json()
    return session

def get_session(address,private_key):
    nonce = get_nonce(address)
    bsc = "https://data-seed-prebsc-1-s1.binance.org:8545/"
    web3 = Web3(Web3.HTTPProvider(bsc))
    message = encode_defunct(text=nonce)
    signed_message = web3.eth.account.sign_message(message, private_key=private_key)

    session = get_token(address,web3.toHex(signed_message.signature))
    return session

def syncer(session):
    try:
        url = "https://rxc-prod-api.ran.network/pilot/sync"
        r = requests.post(url,headers={'Authorization': 'Bearer {}'.format(session['token'])},timeout=None)
        sync = r.json()
                    
        url_sync = "https://rxc-prod-api.ran.network/account/game/sync"
        r_sync = requests.post(url_sync,headers={'Authorization': 'Bearer {}'.format(session['token'])},timeout=None)

        url_logout = "https://rxc-prod-api.ran.network/logout"
        r_logout = requests.post(url_logout,headers={'Authorization': 'Bearer {}'.format(session['token'])},timeout=None,data={})
                    
        messagebox.showinfo("Info", "Sync Success for [{}]".format(session['user']['user']['username']))
    except requests.exceptions.ConnectTimeout:
        messagebox.showerror("Error", "Connection Timeout")

def sync_me(address,private_key):
    try:
        session = get_session(address,private_key)
        checker_url = "https://rxc-prod-api.ran.network/pilot/list"
        checker = requests.get(checker_url,headers={'Authorization': 'Bearer {}'.format(session['token'])},timeout=None)
        pilot_list = checker.json()
        character_count = get_characters(address)
        if character_count == 0:
            if(len(pilot_list['data']['owned']) == 0 and len(pilot_list['data']['pilot']) == 0):
                messagebox.showerror("Error","No character was found in address")
            else:
                syncer(session)
        else:
            syncer(session)

    except requests.exceptions.ConnectTimeout:
        messagebox.showerror("Error", "Connection Timeout")

    
def show():
    user = clicked.get()
    sync_me(optionsfile['data'][user]['address'],optionsfile['data'][user]['private_key'])




clicked = StringVar()
clicked.set( options[0] )

drop = OptionMenu( frame , clicked , *options)
drop.config(width=40)
drop.place(x=17,y=14)
  
button = Button( frame , text = "Sync" , command = show, width=39, height=3 )
button.place(x=17,y=70)


frame.mainloop()
