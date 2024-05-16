import requests
import json, os, tqdm

from time import sleep
from time import time
from json import dumps, load
from urllib.parse import urljoin, urlencode
from uuid import UUID
from base64 import b64encode
from hashlib import sha1
from requests import Session
from os import urandom
from binascii import hexlify
from hmac import new
from websocket import WebSocket, WebSocketConnectionClosedException
from yarl import URL
from pytz import timezone as pytz_timezone
from json_minify import json_minify


DEVKEY = 'e7309ecc0953c6fa60005b2765f99dbbc965c8e9'
SIGKEY = 'dfa5ed192dda6e88a12fe12130dc6206b1251e44'
PREFIX = "19"



class Client:
    api = "https://service.aminoapps.com/api/v1/"
    def __init__(self, device=None, proxies=None) -> None:
        self.device = self.update_device(device or self.generate_device())
        self.proxies = proxies or {}
        self.session = Session()
        self.socket = WebSocket()
        self.socket_thread = None
        self.sid = None
        self.auid = None
        self.Transaction = lambda: str(UUID(hexlify(urandom(16)).decode('ascii')))
    
    @property
    def connected(self):
        return isinstance(self.socket, WebSocket) and self.socket.connected

    def build_headers(self, data=None, content_type=None):
        headers = {
            "NDCDEVICEID": self.device,
            "SMDEVICEID":
                "36934779-e39a-4af7-9f98-9e737929598c",
            "Accept-Language": 'en-US',
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
            "User-Agent": "Apple iPhone12,1 iOS v15.5 Main/3.12.2",
            "Host": "service.aminoapps.com",
            "Accept-Encoding": "gzip",
            "Connection": "Keep-Alive"
        }
        if content_type:
            headers["Content-Type"] = content_type
        if data:
            headers["NDC-MSG-SIG"] = self.generate_signature(data)
        if self.sid:
            headers["NDCAUTH"] = "sid=%s" % self.sid
        if self.auid:
            headers["AUID"] = self.auid
        return headers

    def generate_signature(self, data):
        return b64encode(
            bytes.fromhex(PREFIX) + new(
                bytes.fromhex(SIGKEY),
                data.encode("utf-8"),
                sha1
            ).digest()
        ).decode("utf-8")

    def generate_device(self, info=None):
        data = bytes.fromhex(PREFIX) + (info or os.urandom(20))
        return data.hex() + new(
            bytes.fromhex(DEVKEY),
            data, sha1
        ).hexdigest()

    def update_device(self, device):
        return self.generate_device(bytes.fromhex(device)[1:21])

    def request(self, method, path, json=None, minify=False, ndcId=0, scope=False):
        ndc = (f'g/s-x{ndcId}/' if scope else f'x{ndcId}/s/') if ndcId else 'g/s/'
        url = urljoin(self.api, urljoin(ndc, path.removeprefix('/')))
        data, method = None, method.upper()
        if method in ['GET']:
            params = json  # Alteração aqui para usar json como parâmetros de consulta
            if params:
                if not url.count('?'):
                    url += '?'
                url += urlencode(params)
        elif method in ['POST']:
            data = dumps(json or {})
            if minify:
                data = json_minify(data)
        else:
            raise NotImplementedError(method) from None
        headers = self.build_headers(data)
        return self.session.request(
            method=method,
            url=url,
            data=data,
            headers=headers,
            proxies=self.proxies
        ).json()

    def login(self, email, password):
        data = self.request("POST", "auth/login", {
            "email": email,
            "secret": "0 %s" % password,
            "deviceID": self.device,
            "ClientType": 100,
            "action": "normal",
            "timestamp": int(time() * 1000)})
        self.sid = data.get("sid")
        self.auid = data.get("auid")
        return data
    
    def get_from_link(self, link):
        return self.request('GET', 'link-resolution', {'q': link})

    def join_community(self, ndcId, invitationId=None):
        data = {"timestamp": int(time() * 1000)}
        if invitationId:
            data["invitationId"] = invitationId
        return self.request('POST', f'community/join?sid={self.sid}&auid={self.auid}', data, ndcId=ndcId)

    def send_coins(self, quantity: int, blogId: str, ndcId):
       data = {"coins": quantity, "tippingContext": { "transactionId": self.Transaction()}, "timestamp": int(time() * 1000)}
       return self.request("POST", f"blog/{blogId}/tipping", data, ndcId = ndcId)

    def get_wallet_info(self, totalCoins: bool = False):
        if totalCoins:
            return self.request('GET', 'wallet', None)["wallet"]["totalCoins"]
        else:
            return self.request('GET', 'wallet', None)

class Transfer:
    def __init__(self, blog: str, client = Client()):
        self.blog = blog
        self.client = client
    def run(self):
       client= self.client
       blog = self.blog
       with open("config.json", "rb") as file:
           config = json.load(file)
       for account in config["accounts"]:
            email, password = account["email"], account["password"]
            client.login(email = email, password= password)
            coins = client.get_wallet_info(totalCoins = True)
            print(f"\n : \033[47;31m Transferidor \033[m : \n\n : \033[47;31m Coins Restantes \033[m : {coins}\n : \033[47;31m Conta \033[m : {email}\n : \033[47;31m Dev \033[m : Dupp\n")
            login = client.login(email, password)
            get = client.get_from_link(link = blog)["linkInfoV2"]["extensions"]["linkInfo"]["objectId"]
            comId = client.get_from_link(link = blog)["linkInfoV2"]["extensions"]["linkInfo"]["ndcId"]
            print(" : \033[47;31m Login \033[m : %s" % (login["api:message"]))
            print(" : \033[47;31m Blog \033[m : OK")
            quantity = int(input(" : \033[47;31m Coins \033[m : "))
            count = 0
            for coin in tqdm.tqdm(range(0, quantity, 500)):
                sending = client.send_coins(quantity = quantity, blogId = get, ndcId = comId)
                print(" : \033[47;31m Sending \033[m : %s" % (sending["api:message"]))
                sleep(5)
                if sending["api:message"] == "OK":
                    count += 500
                elif count == 4000:
                    count = 0
                    print(" : \033[47;31m Sendig \033[m : Waiting 5 minutes to avoid interruptions...")
                    sleep(300)
                os.system("clear")

blog = input(" : \033[47;31m Blog \033[m : ")
transfer = Transfer(blog= blog)
transfer.run()
