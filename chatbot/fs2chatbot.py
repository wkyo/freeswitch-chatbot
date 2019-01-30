# -*- coding: utf-8 -*-
"""
FreeSWITCH 1.8 or earlier only supports Python2

    T_T, sad story...

    !!! IMPORTANT !!!
    We are using UTF-8 encoding as default in most situations to avoid 
    confusion caused by inconsistent internal character encoding
    (UTF-8 and UNICODE) with Python2. In Pyhon2, string is a binaray 
    data encoded by some encoding, such as UTF-8, we can simply treat
    it as `char *`.
"""

import os
import codecs
import tempfile
import xml.etree.ElementTree as ET
import freeswitch as fs
import _utils.fuckjson as json
from _utils.patternfactory import singleton_decorator
from _utils.speech import BaiduTTS
from _utils.echobot import EchoBot


CHATBOT_DIR = os.path.dirname(__file__)
CHATBOT_CONF_PATH = [
    '/etc/freeswitch/chatbot/conf.json',
    os.path.join(CHATBOT_DIR, 'conf.json'),
]
CACHE_DIR = os.path.join(tempfile.gettempdir(), 'fs-chatbot')

# load script config from configure file
CHATBOT_CONF = {}
for _conf_pth in CHATBOT_CONF_PATH:
    try:
        with codecs.open(_conf_pth, 'rt') as fp:
            CHATBOT_CONF.update(json.loads(fp.read()))
    except:
        continue
    else:
        break

# make cache directory available
if not os.path.isdir(CACHE_DIR):
    os.mkdir(CACHE_DIR)

# parameters for `play_and_detect_speech`, this method supports ASR/TTS
# (playback and synthesis).
#
# Note: baidu unimrcp server only supports ASR, syhthesiser doesn't work.
# > https://freeswitch.org/confluence/display/FREESWITCH/mod_dptools
# 
# `UNI_ENGINE`: unimrcp engine
# In Python, `+` is optional for quoted string concatenation, ^_^
UNI_ENGINE = 'detect:unimrcp {start-input-timers=false,' \
        'no-input-timeout=5000,recognition-timeout=5000}'
# this will be ignored by baidu ASR, and `chat-empty` is also available
UNI_GRAMMAR = 'builtin:grammar/boolean?language=en-US;y=1;n=2'


def handler(session, args):
    """
    this function will be called by mod_python of FreeSWITCH, you should
    write all the code here
    """
    fs.consoleLog('info', '>>> start chatbot service')
    # session start
    session.answer()

    # welcome
    # answer_sound = sound_query('welcome-short')
    # answer_sound = 'ivr/ivr-welcome_to_freeswitch.wav'
    answer_sound = Synthesizer()('您好，请问需要什么帮助？')

    while session.ready():
        # here, we play anser sound and detect user input in a loop
        session.execute('play_and_detect_speech',
                answer_sound + UNI_ENGINE + UNI_GRAMMAR)
        asr_result =  session.getVariable('detect_speech_result')
        if asr_result is None:
            # if result is None, it means session closed or timeout
            fs.consoleLog('CRIT', '>>> ASR NONE')
            break
        try:
            text = asr2text(asr_result)
        except Exception as e:
            fs.consoleLog('CRIT', '>>> ASR result parse failed \n%s' % e)
            continue
        fs.consoleLog('CRIT', '>>> ASR result is %s' % text)
        # len will get correct length with unicode
        if text is None or len(unicode(text, encoding='utf-8')) < 2:
            fs.consoleLog('CRIT', '>>> ASR result TOO SHORT')
            # answer_sound = sound_query('inaudible')
            answer_sound = Synthesizer()('不好意思，我没有听清您的话，请再说一次。')
            continue
        # chat with robot
        text = Robot()(text)
        fs.consoleLog('CRIT', 'Robot result is %s' % text)
        if not text:
            text = '不好意思，我刚才迷失在人生的道路上了。请问您还需要什么帮助？'
        # speech synthesis
        answer_sound = Synthesizer()(text)
    
    # session close
    fs.msleep(800)
    session.hangup()


def sound_query(sound):
    """query specified sound path, only supports with WAV-16K"""
    sound_path = os.path.join(CHATBOT_DIR, 'sounds', '16000', sound + '.wav')
    if not os.path.isfile(sound_path):
        sound_path = None
    return sound_path


def asr2text(result):
    """fetch recognized text from asr result (xml)"""
    root = ET.fromstring(result)
    node = root.find('.//input[@mode="speech"]')
    text = None
    if node is not None and node.text:
        # node.text is unicode
        text = node.text.encode('utf-8')
    return text


@singleton_decorator
class Synthesizer:

    def __init__(self):
        self.client = BaiduTTS(
            CHATBOT_CONF['baidu']['apikey'],
            CHATBOT_CONF['baidu']['secret'],
            cache_dir=CACHE_DIR
        )
        self.audiofile = tempfile.NamedTemporaryFile(prefix='session_', suffix='.wav')

    def __call__(self, text):
        if isinstance(text, unicode):
            text = text.encode('utf-8')
        audio = self.client.synthesis(text)
        self.audiofile.seek(0)
        self.audiofile.truncate()
        self.audiofile.write(audio)
        self.audiofile.flush()
        return self.audiofile.name


@singleton_decorator
class Robot:

    def __init__(self):
        self.client = EchoBot()

    def __call__(self, text):
        return self.client.chat(text)
