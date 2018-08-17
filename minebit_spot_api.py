# !/usr/bin/python
# -*- coding: utf-8 -*-

import base64
import hmac
import hashlib
import json
import sys

import urllib
import urllib2
import time

reload(sys)
sys.setdefaultencoding('utf8')

# timeout in 5 seconds:
TIMEOUT = 5

API_URL = 'api-test.minebit.com/openapi'

SCHEME = 'https'

# language setting: 'zh-CN', 'en':
LANG = 'zh-CN'

DEFAULT_GET_HEADERS = {
    'Accept': 'application/json',
    'Accept-Language': LANG,
    "Content-type": "application/x-www-form-urlencoded",
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36',
}

DEFAULT_POST_HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Accept-Language': LANG,
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36',
}

class Dict(dict):

    def __init__(self, **kw):
        super(dict, **kw).__init__()

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value

def _toDict(d):
    return Dict(**d)

class ApiError(BaseException):
    pass

class ApiNetworkError(BaseException):
    pass

class MinebitApiClient(object):

    def __init__(self, appKey, appSecret):
        '''
        Init api client object, by passing appKey and appSecret.
        '''
        self._access_key = appKey
        self._access_secret = appSecret.encode('utf-8') # change to bytes
    
    def get(self, path, qery_string=None):
        '''
        Send a http get request and return json object.
        '''
        qs = ""
        if qery_string is not None:
          keys = sorted(qery_string.keys())
          qs = '&'.join(['%s=%s' % (key, self._encode(qery_string[key])) for key in keys])
        url = '%s://%s%s' % (SCHEME, API_URL, path)
        if qs != "":
          url = '%s?%s' % (url, qs)
        timestamp = self._utc()
        sign = self._sign('GET', url, timestamp)
        return self._call('GET', url, sign, timestamp)

    def post(self, path, post_data={}, need_sign=True):
        '''
        Send a http post request and return json object.
        '''
        url = '%s://%s%s' % (SCHEME, API_URL, path)
        timestamp = self._utc()
        post_data["accesskey"] = self._access_key
        post_data["timestamp"] = str(timestamp)
        sign = None
        if need_sign:
          sign = self._sign('POST', url, timestamp, post_data)
        if sign:
            post_data["signature"] = sign
        data = json.dumps(post_data).encode('utf-8')
        #print "post param:",data,",url=",url
        return self._call('POST', url, sign, timestamp, data)

    def _call(self, method, url, sign, timestamp, data=None):
        headers = DEFAULT_GET_HEADERS if method=='GET' else DEFAULT_POST_HEADERS
        req = urllib2.Request(url, data=data, headers=headers)
        resp = urllib2.urlopen(req, timeout=TIMEOUT)
        if resp.getcode() != 200:
          raise ApiNetworkError('Bad response code: %s %s' % (resp.getcode(), resp.reason))
        return self._parse(resp.read())

    def _parse(self, text):
        #print('Response:\n%s' % text)
        result = json.loads(text)
        #if result["status"] == "success":
        #    return result
        #err_msg = '%s : %s' % (result["status"], result["msg"])
        #raise ApiError(str(err_msg))
        return result

    def _sign(self, method, url, ts, post_data={}):
        keys = sorted(post_data.keys())
        post_data_str = '&'.join(['%s=%s' % (key, self._encode(str(post_data[key]))) for key in keys])
        payload = '%s&secretkey=%s' % (post_data_str, self._access_secret)
        sign = hashlib.md5(payload.encode("utf8")).hexdigest().upper()
        return sign

    def _utc(self):
        return str(int(time.time()*1000))

    def _encode(self, s):
        return urllib.quote(s, safe='')

    def change_rate(self, coin = ''):
      params = {
        "coin":coin
      }
      return self.post("/v1/market/change_rate", params)

    def ticker(self, symbols = ''):
      params = {
        "symbols":symbols
      }
      return self.post("/v1/market/quote", params)

    def depth(self, symbol = '', fillter_type = 1):
      params = {
        "symbol":symbol,
        "fillter_type":int(fillter_type)
      }
      return self.post("/v1/market/depth", params)

    def order(self, symbol = '', price = '', amount = '', order_type = ''):
      params = {
        "symbol":symbol,
        "price":str(price),
        "amount":str(amount),
        "type":order_type,
      }
      return self.post("/v1/trade/order", params)

    def cancel_order(self, symbol = '', order_id = ''):
      params = {
        "symbol":symbol,
        "order_id":str(order_id)
      }
      return self.post("/v1/trade/cancel_order", params)

    def order_info(self, order_id = ''):
      params = {
        "order_id":str(order_id)
      }
      return self.post("/v1/trade/order_info", params)

    def pending_orders(self, symbol = '', offset = 0, limit = 10):
      params = {
        "symbol":symbol,
        "offset":0,
        "limit":10
      }
      return self.post("/v1/trade/pending_orders", params)

    def finished_orders(self, symbol = '', offset = 0, limit = 10, start_time = 0, end_time = 0, side = 0):
      params = {
        "symbol":symbol,
        "offset":0,
        "limit":10
      }
      return self.post("/v1/trade/finished_orders", params)

    def balances(self):
      params = {
      }
      return self.post("/v1/trade/balances", params)

    def balance(self, coin=None):
      params = {
        "coin":coin
      }
      return self.post("/v1/trade/balance", params)

if __name__ == "__main__":
  symbol = "eth_btc"
  order_type = "buy"
  price =  0.07
  amount = 0.02
  api = MinebitApiClient("Rg2H9uEQ9WvaxjhUMjDTKdcA63cnfQWo", "Km4lNIIoF9kVM50hDdQUkTct4iP1mBP0")
  #print "coin change rate:\r\n",api.change_rate("btc")
  #print "ticker:\r\n",api.ticker(symbol)
  #print "orderbook depth:\r\n",api.depth(symbol, 1)
  #print "place order:\r\n",api.order(symbol=symbol, price="0.07", amount="0.1", order_type="limit_buy")
  #print "cancel order:\r\n",api.cancel_order(symbol=symbol, order_id="1865")
  #print "get order detail:\r\n",api.order_info(order_id="1865")
  #print "get all pending orders:\r\n",api.pending_orders(symbol)
  #print "get all finished orders:\r\n",api.finished_orders(symbol)
  #print "get all balances:\r\n",api.balances()
  print "get balance of target coin:\r\n",api.balance(coin="eth")
