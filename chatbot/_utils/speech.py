# -*- coding: utf-8 -*-

import os
# import json
import time
import urllib
import codecs
import requests
from . import fuckjson as json


class BaiduTTS:

    def __init__(self, apikey, secret, cache_dir=None):
        self.apikey = apikey
        self.secret = secret
        self.timeout = 5

        # set default
        self._cache_dir = cache_dir
        self._token_name = 'baidu.token.json'
        self._token_path = None
        self._raw_token = None
        # create local cache directory
        if self._cache_dir and not os.path.isdir(self._cache_dir):
            try:
                os.makedirs(self._cache_dir)
            except:
                self._cache_dir = None
        # load local token
        if self._cache_dir and os.path.isdir(self._cache_dir):
            self._token_path = os.path.join(self._cache_dir, self._token_name)
            if os.path.isfile(self._token_path):
                with codecs.open(self._token_path, 'rt', encoding='utf-8') as fp:
                    self._raw_token = json.loads(fp.read())
                    if 'timestamp' not in self._raw_token:
                        self._raw_token = None

    @property
    def cache_dir(self):
        return self._cache_dir

    @property
    def raw_token(self):
        if not self._raw_token or time.time() - float(self._raw_token['timestamp']) + 1000.0 > float(self._raw_token['expires_in']):
            self._raw_token = self.fetch_token()
            self._raw_token['timestamp'] = time.time()
            print('update token ' + self._raw_token['access_token'])
            # update local token
            if self._token_path:
                try:
                    with codecs.open(self._token_path, 'wt', encoding='utf-8') as fp:
                        fp.write(json.dumps(self._raw_token, ensure_ascii=False))
                except Exception as e:
                    print('failed to dump baidu token\n' + str(e) + '\n')
        return self._raw_token

    @property
    def token(self):
        return self.raw_token['access_token']

    def fetch_token(self):
        token_uri = 'https://openapi.baidu.com/oauth/2.0/token'
        response = requests.get(token_uri, params={
            'grant_type': 'client_credentials',
            'client_id': self.apikey,
            'client_secret': self.secret
        }, timeout=self.timeout)
        token = response.json(encoding='utf-8')
        token['timestamp'] = time.time()
        return token

    def synthesis(self, text):
        synthesis_uri = 'http://tsn.baidu.com/text2audio'
        params = {
            'tex': urllib.quote(text),
            'tok': self.token,
            'cuid': '08:00:27:19:e9:4f',  # virtual mac
            'ctp': '1',  # web api
            'lan': 'zh',  # language
            'spd': '5',
            'pit': '5',
            'vol': '5',
            'per': '0',
            'aue': '6',  # wav format
        }
        response = requests.post(
            synthesis_uri, data=params, timeout=self.timeout)
        response_type = response.headers['Content-Type']
        if response_type == 'audio/wav':
            pass
        elif response_type == 'application/json':
            error_json = response.json(encoding='utf-8')
            raise RuntimeError(
                'tts failed - code {} - {}'.format(
                    error_json.get('err_no'),
                    error_json.get('err_msg')))
        else:
            raise RuntimeError('unsupported data')
        return response.content
