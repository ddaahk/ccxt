# -*- coding: utf-8 -*-

# PLEASE DO NOT EDIT THIS FILE, IT IS GENERATED AND WILL BE OVERWRITTEN:
# https://github.com/ccxt/ccxt/blob/master/CONTRIBUTING.md#how-to-contribute-code

from ccxt.async.base.exchange import Exchange
import base64
import hashlib
import math
from ccxt.base.errors import ExchangeError


class btcturk (Exchange):

    def describe(self):
        return self.deep_extend(super(btcturk, self).describe(), {
            'id': 'btcturk',
            'name': 'BTCTurk',
            'countries': 'TR',  # Turkey
            'rateLimit': 1000,
            'has': {
                'CORS': True,
                'fetchTickers': True,
                'fetchOHLCV': True,
            },
            'timeframes': {
                '1d': '1d',
            },
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27992709-18e15646-64a3-11e7-9fa2-b0950ec7712f.jpg',
                'api': 'https://www.btcturk.com/api',
                'www': 'https://www.btcturk.com',
                'doc': 'https://github.com/BTCTrader/broker-api-docs',
            },
            'api': {
                'public': {
                    'get': [
                        'ohlcdata',  # ?last=COUNT
                        'orderbook',
                        'ticker',
                        'trades',   # ?last=COUNT(max 50)
                    ],
                },
                'private': {
                    'get': [
                        'balance',
                        'openOrders',
                        'userTransactions',  # ?offset=0&limit=25&sort=asc
                    ],
                    'post': [
                        'exchange',
                        'cancelOrder',
                    ],
                },
            },
            'fees': {
                'trading': {
                    'maker': 0.002 * 1.18,
                    'taker': 0.0035 * 1.18,
                },
            },
        })

    async def fetch_markets(self):
        response = await self.publicGetTicker()
        result = []
        for i in range(0, len(response)):
            market = response[i]
            id = market['pair']
            baseId = id[0:3]
            quoteId = id[3:6]
            base = self.common_currency_code(baseId)
            quote = self.common_currency_code(quoteId)
            baseId = baseId.lower()
            quoteId = quoteId.lower()
            symbol = base + '/' + quote
            precision = {
                'amount': 8,
                'price': 8,
            }
            active = True
            result.append({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'baseId': baseId,
                'quoteId': quoteId,
                'active': active,
                'info': market,
                'precision': precision,
                'limits': {
                    'amount': {
                        'min': math.pow(10, -precision['amount']),
                        'max': None,
                    },
                    'price': {
                        'min': math.pow(10, -precision['price']),
                        'max': None,
                    },
                    'cost': {
                        'min': None,
                        'max': None,
                    },
                },
            })
        return result

    async def fetch_balance(self, params={}):
        response = await self.privateGetBalance()
        result = {'info': response}
        codes = list(self.currencies.keys())
        for i in range(0, len(codes)):
            code = codes[i]
            currency = self.currencies[code]
            account = self.account()
            free = currency['id'] + '_available'
            total = currency['id'] + '_balance'
            used = currency['id'] + '_reserved'
            if free in response:
                account['free'] = self.safe_float(response, free)
                account['total'] = self.safe_float(response, total)
                account['used'] = self.safe_float(response, used)
            result[code] = account
        return self.parse_balance(result)

    async def fetch_order_book(self, symbol, limit=None, params={}):
        market = self.market(symbol)
        orderbook = await self.publicGetOrderbook(self.extend({
            'pairSymbol': market['id'],
        }, params))
        timestamp = int(orderbook['timestamp'] * 1000)
        return self.parse_order_book(orderbook, timestamp)

    def parse_ticker(self, ticker, market=None):
        symbol = None
        if market:
            symbol = market['symbol']
        timestamp = int(ticker['timestamp']) * 1000
        last = self.safe_float(ticker, 'last')
        return {
            'symbol': symbol,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'high': self.safe_float(ticker, 'high'),
            'low': self.safe_float(ticker, 'low'),
            'bid': self.safe_float(ticker, 'bid'),
            'bidVolume': None,
            'ask': self.safe_float(ticker, 'ask'),
            'askVolume': None,
            'vwap': None,
            'open': self.safe_float(ticker, 'open'),
            'close': last,
            'last': last,
            'previousClose': None,
            'change': None,
            'percentage': None,
            'average': self.safe_float(ticker, 'average'),
            'baseVolume': self.safe_float(ticker, 'volume'),
            'quoteVolume': None,
            'info': ticker,
        }

    async def fetch_tickers(self, symbols=None, params={}):
        await self.load_markets()
        tickers = await self.publicGetTicker(params)
        result = {}
        for i in range(0, len(tickers)):
            ticker = tickers[i]
            symbol = ticker['pair']
            market = None
            if symbol in self.markets_by_id:
                market = self.markets_by_id[symbol]
                symbol = market['symbol']
            result[symbol] = self.parse_ticker(ticker, market)
        return result

    async def fetch_ticker(self, symbol, params={}):
        await self.load_markets()
        tickers = await self.fetch_tickers()
        result = None
        if symbol in tickers:
            result = tickers[symbol]
        return result

    def parse_trade(self, trade, market):
        timestamp = trade['date'] * 1000
        return {
            'id': trade['tid'],
            'info': trade,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'symbol': market['symbol'],
            'type': None,
            'side': None,
            'price': trade['price'],
            'amount': trade['amount'],
        }

    async def fetch_trades(self, symbol, since=None, limit=None, params={}):
        market = self.market(symbol)
        # maxCount = 50
        response = await self.publicGetTrades(self.extend({
            'pairSymbol': market['id'],
        }, params))
        return self.parse_trades(response, market, since, limit)

    def parse_ohlcv(self, ohlcv, market=None, timeframe='1d', since=None, limit=None):
        timestamp = self.parse8601(ohlcv['Time'])
        return [
            timestamp,
            ohlcv['Open'],
            ohlcv['High'],
            ohlcv['Low'],
            ohlcv['Close'],
            ohlcv['Volume'],
        ]

    async def fetch_ohlcv(self, symbol, timeframe='1d', since=None, limit=None, params={}):
        await self.load_markets()
        market = self.market(symbol)
        request = {}
        if limit is not None:
            request['last'] = limit
        response = await self.publicGetOhlcdata(self.extend(request, params))
        return self.parse_ohlcvs(response, market, timeframe, since, limit)

    async def create_order(self, symbol, type, side, amount, price=None, params={}):
        await self.load_markets()
        order = {
            'PairSymbol': self.market_id(symbol),
            'OrderType': 0 if (side == 'buy') else 1,
            'OrderMethod': 1 if (type == 'market') else 0,
        }
        if type == 'market':
            if not('Total' in list(params.keys())):
                raise ExchangeError(self.id + ' createOrder requires the "Total" extra parameter for market orders(amount and price are both ignored)')
        else:
            order['Price'] = price
            order['Amount'] = amount
        response = await self.privatePostExchange(self.extend(order, params))
        return {
            'info': response,
            'id': response['id'],
        }

    async def cancel_order(self, id, symbol=None, params={}):
        return await self.privatePostCancelOrder({'id': id})

    def nonce(self):
        return self.milliseconds()

    def sign(self, path, api='public', method='GET', params={}, headers=None, body=None):
        if self.id == 'btctrader':
            raise ExchangeError(self.id + ' is an abstract base API for BTCExchange, BTCTurk')
        url = self.urls['api'] + '/' + path
        if api == 'public':
            if params:
                url += '?' + self.urlencode(params)
        else:
            self.check_required_credentials()
            nonce = str(self.nonce())
            body = self.urlencode(params)
            secret = base64.b64decode(self.secret)
            auth = self.apiKey + nonce
            headers = {
                'X-PCK': self.apiKey,
                'X-Stamp': nonce,
                'X-Signature': base64.b64encode(self.hmac(self.encode(auth), secret, hashlib.sha256, 'binary')),
                'Content-Type': 'application/x-www-form-urlencoded',
            }
        return {'url': url, 'method': method, 'body': body, 'headers': headers}
