import tkinter as tk
import requests,json
from web3 import Web3
from eth_account.messages import encode_defunct
from datetime import datetime
from pypasser import reCaptchaV3

frame = tk.Tk()
frame.title("RXC Sync")
frame.geometry('265x126')


def get_nonce(address):
    try:
        reCaptcha_response = reCaptchaV3('https://www.google.com.ph/recaptcha/api2/anchor?ar=1&k=6LeZh4IcAAAAAI7foL4X_gcEHdXquHXfc39JU_kY&co=aHR0cHM6Ly9yeGMucmFuLm5ldHdvcms6NDQz&hl=en&v=QENb_qRrX0-mQMyENQjD6Fuj&size=invisible&cb=ys0l0yutd9i2')
        url = "https://rxc-prod-api.ran.network/metamask/request"
        r = requests.post(url,data={"address": address,"g-recaptcha-response": reCaptcha_response})
        nonce = r.json()
        nonce = nonce['data']
    except pypasser.exceptions.ConnectionError:
        lbl.config(text = "Can't get Captcha Response")
        lbl.place(x=55,y=100)
    except requests.exceptions.ConnectTimeout:
        lbl.config(text = "Connection timeout Please Retry")
        lbl.place(x=55,y=100)


    return nonce

def get_token(address,signature):
    try:
        url = "https://rxc-prod-api.ran.network/metamask/verify"
        r = requests.post(url,data={"address": address,"signature": signature})
        session = r.json()
    except requests.exceptions.ConnectTimeout:
        lbl.config(text = "Connection timeout Please Retry")
        lbl.place(x=55,y=100)

    return session

def get_session(address,private_key):
    nonce = get_nonce(address)
    bsc = "https://data-seed-prebsc-1-s1.binance.org:8545/"
    web3 = Web3(Web3.HTTPProvider(bsc))
    message = encode_defunct(text=nonce)
    signed_message = web3.eth.account.sign_message(message, private_key=private_key)

    session = get_token(address,web3.toHex(signed_message.signature))
    #print(session)
    #print(session['token'])
    return session

def get_user():
    try:
        session_file = open('session.txt','r')
        session_file = session_file.read()
        session_file = session_file.split("|")
        session = get_session(session_file[0],session_file[1])
        
        url_pilot = "https://rxc-prod-api.ran.network/pilot/list"
        r_pilot = requests.get(url_pilot,headers={'Authorization': 'Bearer {}'.format(session['token'])},timeout=None)
        list = r_pilot.json()
 
        if (len(list['data']['pilot']) == 0 and len(list['data']['owned']) == 0):
            lbl.config(text = "No Pilot/Character Found in Wallet")
            lbl.place(x=55,y=100)
        else:
            url = "https://rxc-prod-api.ran.network/pilot/sync"
            r = requests.post(url,headers={'Authorization': 'Bearer {}'.format(session['token'])},timeout=None)
            sync = r.json()
            
            url_sync = "https://rxc-prod-api.ran.network/account/game/sync"
            r_sync = requests.post(url_sync,headers={'Authorization': 'Bearer {}'.format(session['token'])},timeout=None)

            url_logout = "https://rxc-prod-api.ran.network/logout"
            r_logout = requests.post(url_logout,headers={'Authorization': 'Bearer {}'.format(session['token'])},timeout=None,data={})
            
            lbl.config(text = "[{}] - {}".format(session['user']['user']['username'],"Sync Complete"))
            lbl.place(x=55,y=100)
    except requests.exceptions.ConnectTimeout:
        lbl.config(text = "Connection timeout Please Retry")
        lbl.place(x=55,y=100)

# Button Creation
SyncButton = tk.Button(frame,
                        text = "Sync", 
                        command = get_user,
                        width=15,height=5)
SyncButton.place(x=5,y=11)


exitButton = tk.Button(frame,
                        text = "Exit", 
                        command = frame.destroy,
                        width=15,height=5)
exitButton.place(x=140,y=11)


lbl = tk.Label(frame, text = "")
lbl.pack()
frame.mainloop()
