#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""素人Wiki用スクリプト用ライブラリ"""
import os as _os
import sys as _sys
import re as _re
import time as _time
import sqlite3 as _sqlite3
import urllib.parse as _up
import fileinput as _fileinput
import pickle as _pickle
import webbrowser as _webbrowser
import unicodedata as _unicodedata
from operator import itemgetter as _itemgetter
from multiprocessing import Process as _Process
from collections import namedtuple as _namedtuple
from tempfile import gettempdir as _gettempdir, mkstemp as _mkstemp
from shutil import rmtree as _rmtree
from difflib import HtmlDiff as _HtmlDiff
from http.client import HTTPException as _HTTPException
from pathlib import Path as _Path
from itertools import chain as _chain

try:
    import httplib2 as _httplib2
except ImportError:
    raise SystemExit('httplib2(python3用)をインストールしてください。')

try:
    from lxml.html import fromstring as _fromstring
except ImportError:
    raise SystemExit('lxml(python3用)をインストールしてください。')

try:
    from pyperclip import copy as _ppccopy
except ImportError:
    pass


__version__ = 20150512

VERBOSE = 0

RECHECK = False

BASEURL = 'http://www.dmm.co.jp'
BASEURL_SMM = 'http://supermm.jp'
BASEURL_SSW = 'http://sougouwiki.com'
BASEURL_ACT = 'http://actress.dmm.co.jp'

ACTURL_BASE = 'http://actress.dmm.co.jp'
ACTURL = ACTURL_BASE + '/-/detail/=/actress_id={}/'

SVC_URL = {'http://www.dmm.co.jp/mono/dvd/':       'dvd',
           'http://www.dmm.co.jp/rental/':         'rental',
           'http://www.dmm.co.jp/digital/videoa/': 'video',
           'http://www.dmm.co.jp/digital/videoc/': 'ama'}

RETLABEL = {'series': 'シリーズ',
            'label':  'レーベル',
            'maker':  'メーカー'}

# 送信防止措置依頼されている女優
HIDE_NAMES = {'1023995': '立花恭子',
              '1024279': '藤崎かすみ',
              '1026305': '北野ひな'}

_SERVICEDIC = {
    'all':    ('', ''),
    'dvd':    ('n1=FgRCTw9VBA4GCF5WXA__/n2=Aw1fVhQKX19XC15nV0AC/',
               'mono/dvd'),
    'rental': ('n1=FgRCTw9VBA4GF1RWR1cK/n2=Aw1fVhQKX0JIF25cRVI_/',
               'rental'),
    'video':  ('n1=FgRCTw9VBA4GAVhfWkIHWw__/n2=Aw1fVhQKX1ZRAlhMUlo5QQgBU1lR/',
               'digital/videoa'),
    'ama':    ('n1=FgRCTw9VBA4GAVhfWkIHWw__/n2=Aw1fVhQKX1ZRAlhMUlo5QQgBU1lT/',
               'digital/videoc')
}

# 除外キーワード
_OMITWORDS = {'総集編':      '総集編',
              'BEST':       '総集編',
              'Best':       '総集編',
              'ベスト':      '総集編',
              'COMPLETE':   '総集編',
              'コンプリート': '総集編',
              '総編版':      '総集編',

              'アウトレット': 'アウトレット',
              '廉価版':      'アウトレット',

              '復刻版':       '復刻盤',
              '復刻盤':       '復刻盤',

              'DMM初回限定':  '限定盤',
              'DMM限定':     '限定盤',
              '数量限定':     '限定盤',
              '枚限定':       '限定盤',
              '初回限定版':    '限定盤',
}
# 【混ぜるな危険】
#  'コレクション'
#  '保存版'
#  '大全集'
#  '全集'

_OMITTYPE = ('イメージビデオ', '総集編', 'アウトレット', '復刻盤', '限定盤', 'UMD')

# 総集編・再収録専門そうなやつ
# 品番プレフィクス(URL上のもの)
_OMNI_PREFIX = (
    '118bst',         # プレステージの総集編
    '118dcm',         # プレステージの総集編
    '118dcx',         # プレステージの総集編
    '118ful',         # プレステージの総集編
    '118kmx',         # プレステージの総集編
    '118mzq',         # プレステージの総集編
    '118pet',         # プレステージの総集編
    '118ppb',         # プレステージの総集編
    '118ppt',         # プレステージの総集編
    '118pre',         # プレステージの総集編
    '118spa',         # プレステージの総集編
    '118spp',         # プレステージの総集編
    '118tgbe',        # プレステージの総集編
    '118tre',         # プレステージの総集編
    '118zesp',        # プレステージの総集編
    '13box',          # グローリークエストの総集編
    '13gqe',          # グローリークエストの総集編
    '13qq',           # グローリークエストの総集編
    '13rvg',          # グローリークエストの総集編
    '13sqv',          # グローリークエストの総集編
    '13ysr',          # グローリークエストの総集編
    '143umd',         # グローバルメディアエンタテインメントの総集編
    '15ald',          # 桃太郎映像出版の総集編
    '15mofd',         # 桃太郎映像出版の総集編
    '164sbdd',        # サイドビーの総集編レーベル クスコ
    '164sbhe',        # サイドビーの総集編レーベル HEROINE
    '17dbr',          # ルビーの総集編シリーズ
    '17hrd',          # ルビーの総集編
    '17kmk',          # ルビーの総集編シリーズ
    '187jame',        # スタイルアートjam/妄想族の総集編
    '187slba',        # スタイルアートLOVE BETES/妄想族の総集編
    '18alsp',         # タカラ映像の総集編
    '18mbox',         # タカラ映像の総集編
    '18mght',         # タカラ映像の総集編
    '1svomn',         # サディスティックビレッジの総集編
    '21issd',         # アウダースジャパンの総集編
    '21pssd',         # アウダースジャパンの総集編
    '23aukb',         # U＆Kの総集編
    '23uksp',         # U＆Kの総集編
    '24hfd',          # ドリームチケットの総集編
    '28drn',          # DRAGON（ハヤブサ） 総集編専門レーベル
    '28gen',          # GIGA TON 総集編専門レーベル
    '28wed',          # EIGHT MAN 総集編専門レーベル
    '29cxaz',         # ジャネス/ladiesの総集編
    '29cwaz',         # ジャネス/ladiesの総集編
    '29djsh',         # ジャネスの総集編
    '29djsj',         # ジャネスの総集編
    '29hwaz',         # ジャネスの総集編
    '2apao',          # オーロラプロジェクト・アネックスの総集編 (レンタル)
    '2bdclb',         # ワープエンタテインメントの総集編
    '2bom',           # BoinBB/ABCの総集編 (レンタル)
    '2box',           # ワープエンタテインメントの総集編
    '2clb',           # ワープエンタテインメントの総集編
    '2koze',          # ローグ・プラネット（フェチ）/妄想族の総集編 (レンタル)
    '2ptko',          # パツキン/ABCの総集編 (レンタル)
    '2slba',          # スタイルアート/妄想族の総集編 (レンタル)
    '2spbox',         # ワープエンタテインメントの総集編
    '2swac',          # 湘南/妄想族の総集編 (レンタル)
    '2tomn',          # TEPPANの総集編 (レンタル)
    '2wpw',           # ワープエンタテインメントの総集編
    '2wsp',           # ワープエンタテインメントの総集編
    '2ycc',           # ワープエンタテインメントの総集編
    '30dmbk',         # MAZO BOYS CLUB (未来フューチャー) の総集編
    '30dsmo',         # BS (未来フューチャー) の総集編
    '33awtb',         # AVS collector’sの総集編
    '33avsb',         # AVS collector’sの総集編
    '33avsw',         # AVS collector’sの総集編
    '33nopc',         # AVS collector’sの総集編
    '33acec',         # AVS collector’sの総集編
    '33dphb',         # AVS collector’sの総集編
    '33dphc',         # AVS collector’sの総集編
    '33dpnw',         # AVS collector’sの総集編
    '33dsfb',         # AVS collector’sの総集編
    '33exbs',         # AVS collector’sの総集編
    '33igub',         # AVS collector’sの総集編
    '33ncgb',         # AVS collector’sの総集編
    '33plzb',         # AVS collector’sの総集編
    '33zosb',         # AVS collector’sの総集編
    '3bmw',           # ワンズファクトリーの総集編
    '3mmb',           # 桃太郎ベスト (レンタル)
    '3naw',           # ワンズファクトリーの総集編
    '3swf',           # ワンズファクトリーの総集編
    '3veq',           # VENUSの総集編 (レンタル)
    '434dfda',        # デジタルアークの総集編
    '434dgtl',        # デジタルアークの総集編
    '434gkdfda',      # デジタルアークの総集編
    '434kcda',        # デジタルアークの総集編
    '49cadv',         # クリスタル映像の総集編
    '4atk',           # Attackers BEST 総集編専門レーベル (レンタル)
    '4idb',           # アイポケの総集編 (レンタル)
    '4jus',           # マドンナ/Madonnaの総集編 (レンタル)
    '4kib',           # kira☆kiraの総集編 (レンタル)
    '4kwb',           # kawaiiの総集編 (レンタル)
    '4hndb',          # 本中の総集編 (レンタル)
    '4mby',           # 溜池ゴローの総集編 (レンタル)
    '4mib',           # ムーディーズの総集編 (レンタル)
    '4mitb',          # 蜜月の総集編 (レンタル)
    '4mkck',          # E-BODYの総集編 (レンタル)
    '4mvb',           # エムズビデオグループの総集編 (レンタル)
    '4obe',           # マドンナ/Obasanの総集編 (レンタル)
    '4ons',           # S1の総集編 (レンタル)
    '4pbd',           # プレミアムの総集編 (レンタル)
    '4ppb',           # OPPAIの総集編 (レンタル)
    '4tmbt',          # teamZEROの総集編 (レンタル)
    '4tywd',          # 乱丸の総集編 (レンタル)
    '4vvv',           # ヴィの総集編 (レンタル)
    '51cma',          # シネマジックの総集編
    '55boya',         # BO-YA TMAの総集編レーベル
    '55hsrm',         # SCREAM 総集編専門レーベル
    '55id',           # TMAの総集編
    '5atk',           # Attackers BEST 総集編専門レーベル (レンタル)
    '5cra',           # クロスの総集編 (レンタル)
    '5krb',           # カルマ/BEST 総集編専門レーベル (レンタル)
    '5mkck',          # E-BODYの総集編 (レンタル)
    '83sbb',          # マルクス兄弟の総集編
    '83scf',          # マルクス兄弟の総集編
    '84bdhyaku',      # 100人 KMPの総集編レーベル
    '84hyaku',        # 100人 KMPの総集編レーベル
    '84hyas',         # 100人 KMPの総集編レーベル
    '9onsd',          # S1の総集編(BD)
    'abcb',           # ABC/妄想族の総集編
    'anhd',           # アンナと花子の総集編
    'atkd',           # Attackers BEST 総集編専門レーベル
    'apao',           # オーロラプロジェクト・アネックスの総集編
    'avsw',           # AVS collector’s の総集編
    'bcdp',           # 総集編メーカー BACK DROP
    'bijc',           # 美人魔女の総集編
    'bomn',           # BoinBB/ABCの総集編
    'bmw',            # ワンズファクトリーの総集編
    'cnz',            # キャンディの総集編
    'corb',           # たぶんCOREの総集編
    'crad',           # クロスの総集編
    'crmn',           # 痴ロモン/妄想族 総集編レーベル
    'daid',           # ダイナマイトエンタープライズの総集編
    'dazd',           # ダスッ！の総集編
    'dgtl',           # デジタルアークの総中編
    'emac',           # DX（エマニエル）の総集編
    'fabs',           # FAプロの総集編
    'h_066fabr',      # FAプロの総集編 (レンタル)
    'h_066fabs',      # FAプロの総集編
    'h_066rabs',      # FAプロ 竜二ベスト
    'h_068mxsps',     # マキシングの総集編
    'h_086abba',      # センタービレッジの総集編
    'h_086cbox',      # センタービレッジの総集編
    'h_086cvdx',      # センタービレッジの総集編
    'h_086euudx',     # センタービレッジの総集編
    'h_086ferax',     # センタービレッジの総集編
    'h_086gomu',      # センタービレッジの総集編
    'h_086hhedx',     # センタービレッジの総集編
    'h_086hthdx',     # センタービレッジの総集編
    'h_086honex',     # センタービレッジの総集編
    'h_086iannx',     # センタービレッジの総集編
    'h_086jrzdx',     # センタービレッジの総集編
    'h_086oita',      # センタービレッジの総集編
    'h_086qizzx',     # センタービレッジの総集編
    'h_108mobsp',     # モブスターズの総集編
    'h_127ytr',       # NONの総集編
    'h_175dbeb',      # BabyEntertainmentの総集編
    'h_175dxdb',      # BabyEntertainmentの総集編
    'h_179dmdv',      # ゲインコーポレーションの総集編
    'h_213agemix',    # SEX Agentの総集編 (レンタル)
    'h_213ageom',     # SEX Agentの総集編
    'h_237swat',      # シリーズ ○○三昧 プラネットプラスの総集編シリーズ
    'h_254kanz',      # 完全盤 STAR PARADISEの総集編レーベル
    'h_254mgdn',      # MEGADON STAR PARADISEの総集編レーベル
    'h_254wnxg',      # VOLUME STAR PARADISEの総集編レーベル
    'h_443hpr',       # 催眠研究所の総集編シリーズ
    'h_479gah',       # GO AHEAD 総集編レーベル (GALLOP)
    'h_479gfs',       # SPECIAL GIFT 総集編レーベル (GALLOP)
    'h_479gft',       # GIFT 総集編レーベル (GALLOP)
    'h_479gfx',       # GIFT DX 総集編レーベル (GALLOP)
    'h_479gne',       # NEO GIFT 総集編レーベル (GALLOP)
    'h_537odfg',      # ワンダフルの総集編
    'h_540exta',      # エクストラ 総集編専門レーベル
    'h_543rlod',      # 乱熟 総集編メーカー
    'h_543rloh',      # 乱熟 総集編メーカー
    'h_543rloj',      # 乱熟 総集編メーカー
    'h_543rlok',      # 乱熟 総集編メーカー
    'h_543rloi',      # 乱熟 総集編メーカー
    'h_544yuyg',      # ケンシロウプロジェクトの総集編
    'h_797impa',      # impact（サンワソフト）の総集編
    'h_838chao',      # CHAOS（Pandora）総集編レーベル (Pandra)
    'h_865jkn',       # 総集編シリーズ 完熟肉汁つゆだく交尾集
    'hjbb',           # はじめ企画の総集編
    'hndb',           # 本中の総集編
    'hoob',           # AVS collector’sの総集編
    'idbd',           # アイポケの総集編
    'jfb',            # Fitchの総集編
    'jomn',           # ABC/妄想族の総集編
    'jusd',           # マドンナ/Madonnaの総集編
    'kibd',           # kira☆kiraの総集編
    'koze',           # ローグ・プラネット（フェチ）/妄想族の総集編
    'krbv',           # カルマ/BEST 総集編専門レーベル
    'kwbd',           # kawaiiの総集編
    'mbyd',           # 溜池ゴローの総集編
    'mibd',           # ムーディーズの総集編
    'mitb',           # 蜜月の総集編
    'mkck',           # E-BODYの総集編
    'mmb',            # 桃太郎ベスト
    'mvbd',           # エムズビデオグループの総集編
    'n_1155dslb',     # グラッソの復刻版(?)
    'obe',            # マドンナ/Obasanの総集編
    'onsd',           # S1の総集編
    'oomn',           # お母さん.com/ABCの総集編
    'rbb',            # ROOKIEの総集編
    'pbd',            # プレミアムの総集編
    'ppbd',           # OPPAIの総集編
    'ptko',           # パツキン/ABCの総集編
    'rabs',           # FAプロ 竜二ベスト
    'slba',           # スタイルアート/妄想族の総集編
    'stol',           # 変態紳士倶楽部の総集編
    'swac',           # 湘南/妄想族の総集編
    'tmbt',           # teamZEROの総集編
    'tomn',           # TEPPANの総集編
    'tywd',           # 乱丸の総集編
    'veq',            # VENUSの総集編
    'vero',           # VENUSの総集編
    'veve',           # VENUSの総集編
    'vvvd',           # ヴィの総集編

    '15awad12',       # 桃太郎映像出版の総集編作品
    '15rawa012',      # 桃太郎映像出版の総集編作品 (レンタル)
    '15rsen167',      # 桃太郎映像出版の総集編作品 (レンタル)
    '15send167',      # 桃太郎映像出版の総集編作品
    '4bf249',         # BeFreeの総集編作品
    '84okax014',      # おかず。の総集編作品
    '84rokax014r',    # おかず。の総集編作品 (レンタル)
    '84umso013',      # UMANAMIの総集編作品
    'bf249',          # BeFreeの総集編作品
    'bf315',          # BeFreeの総集編作品
    'bf374',          # BeFreeの総集編作品
    'bf375',          # BeFreeの総集編作品
    'bf392',          # BeFreeの総集編作品
    'bnsps382',       # ながえSTYLEの総集編作品
    'h_093r18306',    # チェリーズの総集編作品
    'h_093r18308',    # チェリーズの総集編作品
    'emaf324',        # フォーディメンション（エマニエル）の総集編か再利用作品
    'h_254vnds3141',  # ネクストイレブンの総集編作品
    'h_606ylw4303',   # Yellow Moon (Mellow Moon) の総集編作品
    'h_606ylw4308',   # Yellow Moon (Mellow Moon) の総集編作品
    'h_746rssr051r',  # SOSORUの総集編作品 (レンタル)
    'h_746rssr081r',  # SOSORUの総集編作品 (レンタル)
    'h_746ssr051',    # SOSORUの総集編作品
    'h_746ssr081',    # SOSORUの総集編作品
    'h_970kagh023',   # かぐや姫（メロウムーン）の総集編作品
    'h_970kagh023r',  # かぐや姫（メロウムーン）の総集編作品 (レンタル)
    'h_970kagh015',   # かぐや姫（メロウムーン）の総集編作品
    'h_970kagh015r',  # かぐや姫（メロウムーン）の総集編作品 (レンタル)
)
# 品番正規表現
_OMNI_PATTERN = (
    _re.compile(r'^(?:[hn]_)?\d*aaj'),  # AV30
    _re.compile(r'^(?:837?)?sbb'),      # コレクターズエディション (マルクス兄弟)
)

# イメージビデオ専門レーベル
_IV_PREFIX = (
    'h_803pnch',    # Panchu
    )

_ROOKIE = ('rki', '9rki')

# 既定のリンク先は同名別女優がいるためリダイレクトにできない女優をあらかじめ登録
_REDIRECTS = {'黒木麻衣':  '花野真衣',
              '若菜あゆみ': '若菜あゆみ(人妻)',
              '藤原ひとみ': '藤原ひとみ(kawaii*)',
              '佐々木玲奈': '佐々木玲奈(2013)',
              'すみれ':    '東尾真子',
              'EMIRI':    '丘咲エミリ',
              '松嶋葵':    '松嶋葵（2014）',
              '和久井ナナ': 'ふわりゆうき'}

HIDE_NAMES_V = HIDE_NAMES.values()

_CACHEDIR = _Path(_gettempdir()) / 'dmm2ssw_cache'
_RDRDFILE = 'redirects'


p_number = _re.compile(r'\d+')
p_delim = _re.compile(r'[/／,、]')
p_inbracket = _re.compile(r'[(（]')
p_interlink = _re.compile(r'(\[\[.+?\]\])')
p_linkpare = _re.compile(r'\[\[(.+?)(?:>(.+?))?\]\]')
p_hiragana = _re.compile(r'[ぁ-ゞー]')
p_neghirag = _re.compile(r'[^ぁ-ゞー]')

sp_pid = (_re.compile(r'^(?:[hn]_)?\d*([a-z]+)(\d+).*', _re.I), r'\1-\2')


t_wikisyntax = str.maketrans('[]~', '［］～')
t_filename = str.maketrans(r'/:<>?"\*|;', '_' * 10)


_DummyResp = _namedtuple('DummyResp', 'status,fromcache')


def ownname(path):
    return _Path(path).stem

_OWNNAME = ownname(__file__)


class Verbose:
    """デバッグ用情報の出力"""
    def __init__(self, ownname, verbose):
        self._ownname = ownname
        self.verbose = verbose

    def __call__(self, *msg):
        if self.verbose:
            msg = ''.join(str(m) for m in msg)
            print('({0}): >>> {1}'.format(self._ownname, msg),
                  file=_sys.stderr, flush=True)

verbose = Verbose(_OWNNAME, VERBOSE)


class Emsg:
    """標準エラー出力へメッセージ出力"""
    _msglevel = {'E': 'ERROR',
                 'W': 'WARN',
                 'I': 'INFO'}

    def __init__(self, ownname):
        self._ownname = ownname

    def __call__(self, level, *msg):
        msg = ''.join('{}'.format(m) for m in msg)
        m = '({}:{}) {}'.format(self._ownname, self._msglevel[level], msg)
        if level == 'W':
            m = '\033[1;33m{}\033[0m'.format(m)
        elif level == 'E':
            m = '\033[1;31m{}\033[0m'.format(m)
        print(m, file=_sys.stderr, flush=True)

        if level == 'E':
            # エラーなら終了
            raise SystemExit()

_emsg = Emsg(_OWNNAME)


class Summary:
    """作品情報格納用"""
    __slots__ = ('url',
                 'media',
                 'release',
                 'time',
                 'title',
                 'title_dmm',
                 'subtitle',
                 'actress',
                 'size',
                 'director',
                 'series',
                 'series_id',
                 'label',
                 'label_id',
                 'maker',
                 'maker_id',
                 'list_type',
                 'list_page',
                 'pid',
                 'cid',
                 'image_sm',
                 'image_lg',
                 'number',
                 'genre',
                 'note',
                 'others')

    def __init__(self,
                 url='',
                 media='',
                 release='',
                 time='',
                 title='',
                 title_dmm='',
                 subtitle='',
                 actress=[],
                 size='',
                 director=[],
                 series='',
                 series_id='',
                 label='',
                 label_id='',
                 maker='',
                 maker_id='',
                 list_type='',
                 list_page='',
                 pid='',
                 cid='',
                 image_sm='',
                 image_lg='',
                 number=0,
                 genre=[],
                 note=[],
                 others=[]):
        for key in self.__slots__:
            value = eval(key)
            if isinstance(value, list):
                setattr(self, key, value[:])
            else:
                setattr(self, key, value)

    def __contains__(self, key):
        return hasattr(self, key)

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __call__(self, *keys):
        return self.values(*keys)

    def __iter__(self):
        return iter(self.__slots__)

    def keys(self):
        return self.__slots__

    def values(self, *keys):
        attrs = keys or self.__slots__
        return list(getattr(self, k) for k in attrs)

    def items(self, *args):
        attrs = args or self.__slots__
        return list((a, getattr(self, a)) for a in attrs)

    def stringize(self, *args):
        attrs = args or self.__slots__
        for a in attrs:
            v = getattr(self, a)
            if a == 'note' and not v:
                break
            if isinstance(v, int):
                v = str(v) if v else ''
            elif isinstance(v, list):
                v = ','.join(v)
            yield v

    def tsv(self, *args):
        attrs = args or self.__slots__
        return '\t'.join(self.stringize(*attrs))

    def __set(self, attr, other, overwrite):
        this = getattr(self, attr)
        if isinstance(other, list):
            other = other.copy()
        if not this or overwrite:
            setattr(self, attr, other)

    def merge(self, otherobj, overwrite=False):
        if hasattr(otherobj, 'keys'):
            for key in otherobj:
                val = otherobj[key]
                if val:
                    self.__set(key, val, overwrite)
        else:
            for key, val in otherobj:
                if val:
                    self.__set(key, val, overwrite)

    def update(self, otherobj):
        self.merge(otherobj, overwrite=True)


def sub(p_list, string, n=False):
    """re.sub()、re.subn()ラッパー"""
    return p_list[0].subn(p_list[1], string) if n \
        else p_list[0].sub(p_list[1], string)


def copy2clipboard(string):
    """クリップボードへコピー"""
    try:
        _ppccopy(string)
    except NameError:
        _emsg('W', 'Python pyperclip モジュールがインストールされていないためクリップボードにはコピーされません。')


def quote(string, safe='/', encoding='euc_jisx0213', errors=None):
    """URL埋め込みように文字列をクオート"""
    return _up.quote(string, safe=safe, encoding=encoding,
                     errors=errors).replace('-', '%2d')


def unquote(string, encoding='euc_jisx0213', errors='replace'):
    """文字列をアンクオート"""
    return _up.unquote(string, encoding=encoding, errors=errors)


def _clip_pname(url):
    """WikiページのURLからページ名を取得"""
    return unquote(url.rsplit('/', 1)[-1])


_t_nl = str.maketrans('', '', '\r\n')


def rm_nlcode(string):
    """改行文字を除去"""
    return string.translate(_t_nl)


_t_pidsep = str.maketrans('', '', '+-')


def rm_hyphen(string):
    """ハイフンを除去"""
    return string.translate(_t_pidsep)


def extr_num(string):
    """文字列から数値だけ抽出"""
    return p_number.findall(string)


p_list_article = _re.compile(r'/article=(.+?)/')


def get_article(url):
    """DMM URLからarticle=部を抽出"""
    return p_list_article.findall(url)[0]


def files_exists(mode, *files):
    """同名のファイルが存在するかどうかチェック"""
    for f in files:
        if f in {_sys.stdin, _sys.stdout}:
            continue
        verbose('file: ', f)
        isexist = _os.path.exists(f)
        if mode == 'r' and not isexist:
            _emsg('E', 'ファイルが見つかりません: ', f)
        elif mode == 'w' and isexist:
            _emsg('E', '同名のファイルが存在します (-r で上書きします): ', f)


def inprogress(msg):
    """「{}中...」メッセージ"""
    if not VERBOSE:
        print('{}  '.format(msg), end='\r', file=_sys.stderr, flush=True)


def gen_no_omits(no_omit=None):
    """除外しない対象セットの作成"""
    if isinstance(no_omit, int):
        return set(_OMITTYPE[:no_omit])
    elif no_omit is None:
        return set(_OMITTYPE)
    else:
        return set(_OMITTYPE[i] for i in no_omit)


def le80bytes(string, encoding='euc_jisx0213'):
    """Wikiページ名最大長(80バイト)チェック"""
    return len(bytes(string, encoding)) <= 80


def gen_ntfcols(tname, fsource: 'sequence'):
    """表形式ヘッダから名前付きタプルを作成"""
    if isinstance(fsource, str):
        fsource = ('TITLE' if c == 'SUBTITLE' else c
                   for c in fsource.replace('~', '').split('|'))
    return _namedtuple(tname, fsource, rename=True)


class __OpenUrl:
    """URLを開いて読み込む"""
    _p_charset = _re.compile(r'charset=([a-zA-Z0-9_-]+);?')

    def __init__(self):
        if VERBOSE > 1:
            _httplib2.debuglevel = 1
        self.__http = _httplib2.Http(str(_CACHEDIR))
        self.__wait = dict()

    def __sleep(self):
        _time.sleep(5)

    def _url_openerror(self, name, info, url):
        """URLオープン時のエラーメッセージ"""
        _emsg('E',
              'URLを開く時にエラーが発生しました ({})。詳細: {}, url={}'.format(
                  name, info, url))

    def _resolve_charset(self, resp, html):
        """文字エンコーディングの解決"""
        # HTTPレスポンスから取得
        c_type = self._p_charset.findall(resp['content-type'])
        if c_type:
            verbose('charset from resp.')
            return c_type[0]

        # HTMLヘッダから取得
        c_type = self._p_charset.findall(_fromstring(html).xpath(
            '//meta[@http-equiv="Content-Type"]')[0].get('content', False))
        if c_type:
            verbose('charset from meta.')
            return c_type[0]

    def __call__(self, url, charset=None, set_cookie=None, cache=True,
                 method='GET', to_elems=True):
        verbose('open url: ', url)

        if method == 'HEAD':
            to_elems = False

        site = _up.urlparse(url).netloc
        if not site:
            _emsg('E', '不正なURL?: ', url)

        if cache:
            maxage = '7200' if site == 'sougouwiki.com' else '86400'
            headers = {'cache-control': 'private, max-age={}'.format(maxage)}
        else:
            headers = dict()

        if set_cookie:
            headers['cookie'] = set_cookie
        verbose('http headers: ', headers)

        for i in range(5):

            try:
                self.__wait[site].is_alive()
            except KeyError:
                pass
            else:
                verbose('joinning wait_', site)
                self.__wait[site].join()

            try:
                resp, html = self.__http.request(
                    url, headers=headers, method=method)
            except _httplib2.HttpLib2Error as e:
                self._url_openerror(
                    e.__class__.__name__, ", ".join(e.args), url)
            except _HTTPException as e:
                if e == 'got more than 100 headers':
                    if '/limit=60/' in url:
                        _emsg('E', '(おそらくサーバー側に問題のある)HTTP例外です。')
                    else:
                        url = url.replace('/limit=120/', '/limit=60/')
                resp = _DummyResp(status=0, fromcache=False)
            verbose('http resp: ', resp)
            verbose('fromcache: ', resp.fromcache)

            if not resp.fromcache:
                verbose('start wait_', site)
                self.__wait[site] = _Process(target=self.__sleep, daemon=True)
                self.__wait[site].start()

            # HTTPステータスがサーバ/ゲートウェイの一時的な問題でなければ終了
            if resp.status and not 500 <= resp.status <= 504:
                if resp.status not in {200, 404}:
                    _emsg('W', 'HTTP status: ', resp.status)
                break

        else:
            verbose('over 5 cnt with status 50x')
            return resp, ''

        if charset or not to_elems:
            encoding = charset or self._resolve_charset(resp, html)
            verbose('encoding: ', encoding)

            try:
                html = html.decode(encoding, 'ignore')
            except UnboundLocalError:
                _emsg('E', 'HTMLの読み込みに失敗しました: resp=', resp)

        return resp, _fromstring(html) if to_elems else html

open_url = __OpenUrl()


def norm_uc(string):
    """unicode正規化"""
    return _unicodedata.normalize('NFKC', string)


def check_omitword(title):
    """タイトル内の除外キーワードチェック"""
    for key in filter(lambda k: k in title, _OMITWORDS):
        verbose('omit key, word: {}, {}'.format(key, _OMITWORDS[key]))
        yield _OMITWORDS[key], key


def check_omitprfx(cid, prefix=_OMNI_PREFIX, patn=_OMNI_PATTERN):
    """隠れ総集編チェック(プレフィクス版)"""
    return any(cid.startswith(p) for p in prefix) or \
        any(p.search(cid) for p in patn)


_p_omnivals = (
    # 「20人/名」以上
    _re.compile(r'(?:[2-9]\d|\d{3,})(?:人[^目]?|名)'),
    _re.compile(r'(?:[二弐][一二三四五六七八九十〇壱弐参拾百千万億兆]+|[三四五六七八九参百千][一二三四五六七八九十〇壱弐参拾百千万億兆]+|[一二三四五六七八九壱弐参百千][一二三四五六七八九十〇壱弐参拾百千万億兆]{2,})(?:人[^目]?|名)'),

    # 「50(連)(発/射|SEX)」以上
    _re.compile(r'(?:[5-9]\d|\d{3,})(?:連?[発射]|SEX)'),
    _re.compile(r'(?:[五六七八九][一二三四五六七八九十〇壱弐参拾百千万億兆]+|[一二三四五六七八九百千][一二三四五六七八九十〇壱弐参拾百千万億兆]{2,})連?[発射]'),

    # 「15本番」以上
    _re.compile(r'(?:1[5-9]|[2-9]\d|\d{3,})本番'),
    _re.compile(r'(?:[一十拾][五六七八九〇壱弐参拾百千万億兆]|[二三四五六七八九弐参百][一二三四五六七八九十〇壱弐参拾百千万億兆]|[一二三四五六七八九壱弐参拾百千][一二三四五六七八九十〇壱弐参拾百千万億兆]{2,})本番'),
    # 「4時間」以上
    _re.compile(r'(?:[4-9]|\d{2,})時間'),
    _re.compile(r'(?:[四五六七八九十拾百千]|[一二三四五六七八九十壱弐参拾百千][一二三四五六七八九十〇壱弐参拾百千万億兆]+)時間'),

    # 「240分」以上
    _re.compile(r'(?:2[4-9]\d|[3-9]\d{2}|\d{4,})分'),
    _re.compile(r'(?:[二弐][四五六七八九百千万億兆][一二三四五六七八九十〇壱弐参百千万億兆]+|[三四五六七八九参百千万億兆][一二三四五六七八九十〇壱弐参拾百千万億兆]{2}|[一二三四五六七八九十〇壱弐参拾百千万億兆]{4,})分'),

    # 「(全)(n)タイトル」
    _re.compile(r'(?:全|\d+)タイトル'),
    _re.compile(r'(?:全|[一二三四五六七八九十〇壱弐参拾百千万億兆]+)タイトル'),
)


def check_omnivals(title):
    """隠れ総集編チェック(関連数値編)"""
    title = norm_uc(title)
    hit = tuple(_chain.from_iterable(p.findall(title) for p in _p_omnivals))
    if len(hit) > 1:
        return hit


_p_ge4h = _re.compile(r'(?:[4-9]|\d{2,})時間')
_p_ge200m = _re.compile(r'(?:[2-9]\d{2}|\d{4,})分')


def is_omnirookie(cid, title):
    """ROOKIE隠れ総集編チェック"""
    if check_omitprfx(cid, _ROOKIE):
        # ROOKIEチェック
        hh = _p_ge4h.findall(title)
        mmm = _p_ge200m.findall(title)
        return hh, mmm
    else:
        return None, None


def check_omit(title, cid, omit_suss_4h=None, no_omits=set()):
    """
    除外対象かどうかチェック

    除外対象なら対象の情報を返す。
    """
    # 除外作品チェック (タイトル内の文字列から)
    for key, word in filter(lambda k: k[0] not in no_omits,
                            check_omitword(title)):
        return key, word

    if '総集編' not in no_omits:
        # 隠れ総集編チェック(タイトル内の数値から)
        omnivals = check_omnivals(title)
        if omnivals:
            return '総集編', omnivals

        # 隠れ総集編チェック(cidから)
        if check_omitprfx(cid):
            return '総集編', cid

        # 総集編容疑メーカー
        if omit_suss_4h:
            hh, mmm = is_omnirookie(cid, title)
            if hh or mmm:
                return '総集編', omit_suss_4h + '(4時間以上)'

    if 'イメージビデオ' not in no_omits:
        # 隠れIVチェック
        if check_omitprfx(cid, _IV_PREFIX):
            return 'イメージビデオ', cid


class DMMTitleListParser:
    """一覧ページの解析"""
    _sp_tsuffix = (_re.compile(r' - \S*( - DMM.R18)?$'), '')

    def __init__(self, no_omits=set(_OMITTYPE), patn_pid=None, show_info=True):
        self._no_omits = no_omits
        self._patn_pid = patn_pid
        self._show_info = show_info
        self.omitted = 0
        self.priurl = ''
        self.article = []

    def _get_article(self, he):
        """アーティクル名の取得"""
        try:
            article = he.find('head/title').text.strip()
        except AttributeError:
            article = ''

        # wiki構文と衝突する文字列の置き換え
        article = article.translate(t_wikisyntax)
        article = sub(self._sp_tsuffix, article)

        return article

    def _ret_titles(self, titles):
        """作品タイトルとURLの取得"""
        def omit(key, word):
            if self._show_info or VERBOSE:
                _emsg('I', 'ページを除外しました: cid={}, {:<20}'.format(
                    cid, 'reason=("{}", "{}")'.format(key, word)))
            self.omitted += 1

        for ttl in titles:
            t_el = ttl.find('a')
            title = t_el.text
            path = t_el.get('href')
            url = _up.urljoin(BASEURL, path)

            pid, cid = gen_pid(url, self._patn_pid)
            cid = cid.lstrip('79')

            # 除外作品チェック
            omitinfo = check_omit(title, cid, no_omits=self._no_omits)
            if omitinfo:
                omit(*omitinfo)
            else:
                yield url, Summary(url=url, title=title, pid=pid, cid=cid)

    def _ret_nextpage(self, he):
        """ページネーション処理"""
        try:
            pagin = he.find_class(
                'list-boxpagenation')[0].xpath('.//a[text()="次へ"]')
        except IndexError:
            return False

        return _up.urljoin(BASEURL, pagin[0].get('href')) if pagin else False

    def __call__(self, he):
        """解析実行"""
        self.article.append((self._get_article(he), self.priurl))

        self.nexturl = self._ret_nextpage(he)

        return self._ret_titles(he.find_class('ttl'))


_p_splitpid1 = _re.compile(r'[+-]')
_p_splitpid2 = _re.compile(r'([a-z]+)(\d+)', _re.I)


def split_pid(pid):
    """品番をプレフィクスと連番に分離"""
    try:
        prefix, serial = _p_splitpid1.split(pid)
    except ValueError:
        prefix, serial = _p_splitpid2.findall(pid)[0]

    return prefix, serial


def sort_by_id(products, reverse=False):
    """
    品番をソート

    桁数が揃ってない品番もソート
    """
    def _make_items(products, maxdigit):
        """URL(キー)と桁を揃えた品番"""
        for url in products:
            prefix, serial = split_pid(products[url].pid)
            yield url, '{0}{1:0>{2}}'.format(prefix, serial, maxdigit)

    maxdigit = max(extr_num(products[p].pid)[0] for p in products)

    return (url for url, pid in sorted(_make_items(products, maxdigit),
                                       key=_itemgetter(1),
                                       reverse=reverse))


class NotKeyIdYet:
    """品番が key_id になるまで True を返す"""
    def _is_start_pid(self, pid):
        prefix, serial = split_pid(pid)
        return prefix == self._key_id[0] and serial < self._key_id[1]

    def __init__(self, key_id, key_type, attr, if_inactive=False):
        if not key_id:
            self._match = lambda x: if_inactive

        else:
            if key_type == 'start':

                if attr == 'pid':
                    self._key_id = split_pid(key_id)
                    self._match = self._is_start_pid

                elif attr == 'cid':
                    self._key_id = key_id
                    self._match = lambda cid: cid < self._key_id

                else:
                    raise ValueError('Invalid value: attr({})'.format(attr))

            elif key_type == 'last':

                if attr == 'pid':
                    self._key_id = rm_hyphen(key_id)
                    self._match = lambda pid: rm_hyphen(pid) != self._key_id

                elif attr == 'cid':
                    self._key_id = key_id
                    self._match = lambda cid: cid != self._key_id

                else:
                    raise ValueError('Invalid value: attr({})'.format(attr))

            else:
                raise ValueError('Invalid value: key_id({})'.format(key_id))

    def __call__(self, cand):
        return self._match(cand)


def from_dmm(listparser, priurls, pages_last=0,
             key_id=None, key_type=None, idattr='pid',
             ignore=False, show_info=True):
    """DMMから作品一覧を取得"""
    verbose('Start parsing DMM list pages')

    match_key_id = NotKeyIdYet(key_id, key_type, idattr, if_inactive=True)

    for purl in priurls:

        listparser.priurl = purl

        searchurl = _up.urljoin(purl, 'limit=120/view=text/')
        pages = 1

        while searchurl:

            if show_info:
                inprogress('(一覧: {} ページ)  '.format(pages))

            resp, he = open_url(searchurl)
            if resp.status != 200 and ignore:
                return ((False, False),)

            if resp.status == 404:
                _emsg('E',
                      '指定した条件でページは見つかりませんでした: url=',
                      searchurl)
            elif resp.status != 200:
                _emsg('E',
                      'URLを開く際にエラーが発生しました: staus=',
                      resp.status)

            # HTMLの解析
            for url, prop in listparser(he):

                yield url, prop

                if not match_key_id(getattr(prop, idattr)):
                    p = pages + 1
                    pages_last = min((pages_last, p)) if pages_last else p
                    verbose('set pages last: ', pages_last)

            pages += 1
            verbose('Pages : {} > {}'.format(pages, pages_last))

            searchurl = listparser.nexturl
            verbose('nexturl: ', searchurl)

            if pages_last and pages > pages_last:
                verbose('reached pages_last')
                break

    verbose('Parsing list pages finished')


_p_name = _re.compile(
    r'(?P<fore>[\w>]*)?(?P<paren>[(（][\w>]*[）)])?(?P<back>[\w>]*)?')


def parse_names(name):
    """
    出演者情報の解析(rawテキスト)

    dmm2ssw.py -a オプション渡しとTSVからインポート用
    """
    verbose('Parsing name...')

    # カッコ括りの付記の分割
    m = _p_name.search(name)

    if any(m.groups()):
        shown = m.group('fore') or m.group('back')
        parened = m.group('paren') or ''
    else:
        shown = name
        parened = ''

    if shown.endswith('人目') and not parened:
        # n人目だったときのカッコ内送り
        parened = '({})'.format(shown)
        shown = ''

    # リダイレクト先の取得
    if '>' in shown:
        shown, dest = shown.split('>')
    else:
        dest = ''

    verbose('name prepared: {}, {}, {}'.format(shown, dest, parened))
    return shown, dest, parened


_p_etc = _re.compile(r'ほか\w*?計(\d+)名')


def ret_numofpfmrs(etc):
    """ほか計n名を取得"""
    number = None

    m = _p_etc.findall(etc)

    if m:
        number = int(m[0])
    elif etc == 'ほか':
        number = -1
    elif etc == 'ほか数名':
        number = -2

    return number


def cvt2int(item):
    """数値だけ取り出してintに変換"""
    return int(extr_num(item)[0]) if item else 0


def from_tsv(files):
    """タイトル一覧をファイルからインポートするジェネレータ(TSV)"""
    files_exists('r', *files)
    verbose('from tsv file: {}'.format(files))

    with _fileinput.input(files=files) as f:
        for row in f:
            # タブ区切りなので改行を明示して除去してタブを明示して分割
            row = tuple(c.strip() for c in row.rstrip('\n').split('\t'))

            # 女優名がある場合分割
            try:
                actress = p_delim.split(row[3]) if row[3] else []
            except IndexError:
                _emsg('E', '正しいインポートファイル形式ではないようです。')

            # 処理用に女優名を要素解析
            actress = list(parse_names(a) for a in actress)
            numcols = len(row)
            number = cvt2int(row[4]) if numcols > 4 else 0
            director = p_delim.split(row[5]) if numcols > 5 else []
            note = row[6] if numcols > 6 else []

            yield row[0], Summary(url=row[0],
                                  title=row[1],
                                  pid=row[2],
                                  actress=actress.copy(),
                                  number=number,
                                  director=director.copy(),
                                  note=note)


class _FromWiki:
    """タイトル一覧をウィキテキスト(表形式)からインポート"""
    def __init__(self):
        self.article = ''

    def _parse_names(self, name):
        """出演者情報の解析(ウィキテキスト)"""
        shown = dest = parened = ''

        for e in filter(None, p_interlink.split(name)):

            # いったん丸カッコ括りを解く
            elem = e.strip().strip('()')

            if elem.startswith('[['):
                shown = elem.strip('[]')
                if '>' in shown:
                    shown, dest = shown.split('>')
                else:
                    dest = ''
            else:
                parened = '({})'.format(elem)

        verbose('name prepared: {}, {}, {}'.format(shown, dest, parened))
        return shown, dest, parened

    def __call__(self, files, rawpfmrs=False):
        verbose('from wiki: ', files)

        self.article = ''
        Cols = None

        with _fileinput.input(files) as fd:
            for row in fd:

                row = row.strip()

                if row.startswith('*[[') and not self.article:
                    self.article = p_linkpare.findall(row)
                    verbose('article from wiki: ', self.article)

                if row.startswith('|~NO'):
                    Cols = gen_ntfcols('Cols', row)
                elif not row.startswith('|[['):
                    continue

                md = Cols(*(c.strip() for c in row.split('|')))

                try:
                    pid, url = p_linkpare.findall(md.NO)[0]
                except IndexError:
                    continue

                if not url.endswith('/'):
                    url += '/'

                if not md.TITLE:
                    # タイトルがない時は品番を利用
                    md = md._replace(TITLE='__' + pid)

                # 出演者の解析
                actress = []

                if md.ACTRESS and '別ページ' not in md.ACTRESS:
                    if rawpfmrs:
                        actress = [(a[0], a[1], '')
                                   for a in p_linkpare.finditer(md.ACTRESS)]
                    else:
                        # 「 ほか～」の切り離し
                        # TODO: もっと賢く
                        s = md.ACTRESS.rsplit(maxsplit=1)

                        number = ret_numofpfmrs(s[1]) if len(s) > 1 else 0

                        alist = p_delim.split(s[0])
                        actress = [self._parse_names(a) for a in alist if a]

                note = p_delim.split(md.NOTE)
                note = list(n for n in note if 'シリーズ' not in n)

                yield url, Summary(url=url,
                                   title=md.TITLE,
                                   pid=pid,
                                   actress=actress.copy(),
                                   number=number,
                                   note=note)

            if Cols is None:
                _emsg('E', '素人系総合Wikiの一覧ページのウィキテキストではないようです: ',
                      _fileinput.filename())


from_wiki = _FromWiki()


class _FromHtml:
    """素人総合WikiページをURLから(HTMLで)読み込んでインポート"""
    def _unquotename(self, el):
        """URLからページ名を取得"""
        url = el.get('href')
        if not url.startswith(BASEURL_SSW):
            return url
        return _clip_pname(el.get('href'))

    def _enclose(self, ph):
        """括弧でくくってなかったらくくる"""
        return ph if ph.startswith('(') else '({})'.format(ph)

    def _parse_performers(self, td):
        """出演者カラムの解析(FromHtml)"""

        # 内部リンクの前にある文字列チェック
        foretxt = (td.text or '').strip()

        if foretxt:
            # 先頭にリテラルあり
            if not len(td.xpath('a')):
                # リテラルのみでアンカー無し
                yield '', '', foretxt
                return
            else:
                # アンカーあり
                fores = p_delim.split(foretxt)
                for ph in filter(None, fores):
                    yield '', '', self._enclose(ph)

        if not len(td):
            # リテラルだけだったら終了
            return

        # 内部リンク処理
        for a in td.iterchildren('a'):

            shown = a.text.strip()
            if shown == '別ページ':
                return

            dest = self._unquotename(a)
            if dest == shown:
                dest = ''

            # 内部リンクの後にある文字列チェック
            tailtxt = (a.tail or '').strip()

            if not tailtxt:
                yield shown, dest, ''
            else:
                # 「~ ほか」チェック
                splitetc = tailtxt.rsplit(maxsplit=1)
                self._number = ret_numofpfmrs(splitetc[-1])
                if len(splitetc) > 1:
                    tailtxt = splitetc[0]
                elif self._number is not None:
                    tailtxt = ''

                tails = p_delim.split(tailtxt)

                # 内部リンクに付随する文字列がないかチェック
                yield shown, dest, tails.pop(0) if tails[0] else ''

                for ph in tails:
                    if ph:
                        yield '', '', self._enclose(ph)

    def _parse_notes(self, note):
        """NOTEの解析"""
        result = ''

        if note.text:
            result += note.text.strip()

        for el in note.iterchildren():
            if el.tag == 'br':
                result += '~~'

            elif el.tag == 'a':
                shown = el.text
                if 'シリーズ' in shown:
                    continue

                dest = self._unquotename(el)

                if shown == dest:
                    dest == ''

                result += '[[{}{}]]'.format(
                    shown, '>{}'.format(dest) if dest else '')

            if el.tail is not None:
                result += el.tail

        return [result.replace('~~', '', 1)] if result else []

    def __call__(self, wikiurls, service='dvd', cache=True):

        def _makeheader(iterth):
            """ヘッダの TITLE → SUBTITLE の置き換え"""
            for th in iterth:
                yield 'TITLE' if th.text == 'SUBTITLE' else th.text

        for wurl in wikiurls:

            if wurl.startswith('http://'):
                resp, he = open_url(wurl, cache=cache)
                if resp.status == 404:
                    _emsg('E', 'ページが見つかりません: ', wurl)
            else:
                with open(wurl, 'rb') as f:
                    he = _fromstring(f.read())

            try:
                self.article = he.find(
                    './/div[@id="page-header-inner"]//h2').text.strip()
            except AttributeError:
                _emsg('E', '素人系総合Wiki一覧ページのHTMLではないようです: ', wurl)

            userarea = he.find_class('user-area')[0]

            for tbl in userarea.iterfind('.//table'):

                Cols = gen_ntfcols(
                    'Cols', _makeheader(tbl.find('.//tr[th]').iterfind('th')))

                for tr in tbl.iterfind('.//tr[td]'):
                    self._number = 0

                    tds = tr.xpath('td')

                    try:
                        md = Cols(*tds)
                    except TypeError:
                        continue

                    anchor = md.NO.find('a')
                    if anchor is not None:
                        pid = anchor.text.strip()
                        url = anchor.get('href')
                        if not url.endswith('/'):
                            url += '/'
                    else:
                        pid = md.NO.text
                        if not pid:
                            continue
                        altera = md.PHOTO.find('a')
                        if altera is not None:
                            url = altera.get('href')
                            if url.endswith('jpg'):
                                continue
                        else:
                            cid = rm_hyphen(pid).lower()
                            url = build_produrl(service, cid)

                    # タイトルに改行があればスペースへ置き換え
                    if 'TITLE' in md._fields:
                        title = ' '.join(md.TITLE.xpath('text()')) or \
                                '__' + pid
                    else:
                        title = '__' + pid
                    actress = [a for a in self._parse_performers(md.ACTRESS)
                               if a is not None]
                    note = self._parse_notes(md.NOTE)
                    if 'ORIGINAL' in md._fields:
                        note.extend(self._parse_notes(md.ORIGINAL))

                    yield url, Summary(url=url,
                                       title=title,
                                       pid=pid,
                                       actress=actress.copy(),
                                       number=self._number,
                                       note=note)

from_html = _FromHtml()


def join_priurls(retrieval, *keywords, service='dvd'):
    """DMM基底URLの作成"""
    return tuple('{}/{}/-/list/=/article={}/id={}/sort=date/'.format(
        BASEURL, _SERVICEDIC[service][1], retrieval, k) for k in keywords)


def build_produrl(service, cid):
    """DMM作品ページのURL作成"""
    return '{}/{}/-/detail/=/cid={}/'.format(
        BASEURL, _SERVICEDIC[service][1], cid)


def getnext_text(elem, xpath=False):
    """.getnext()してtextしてstrip()"""
    if xpath:
        return [t.strip().strip('-')
                for t in elem.getnext().xpath('{}/text()'.format(xpath))]
    else:
        nexttext = elem.getnext().text
        return nexttext.strip().strip('-') if nexttext else None


def _rdrparser(page, he):
    """wikiリダイレクトページかどうかの検出"""
    verbose('is sswrdr/page: ', page)
    rdr_flg = False
    userarea = he.find_class('user-area')[0]

    if any(a.get('href').startswith(BASEURL)
           for a in userarea.iterfind('.//a[@class="outlink"]')):
        # DMMへのリンクが見つかったらリダイレクトページではないとみなし終了
        verbose('Not redirect page (dmm link found)')
        return page

    if userarea.text and userarea.text.strip() == '誘導ページ':
        rdr_flg = True
        verbose('guide page')

    for el in userarea:
        if el.tail and el.tail.strip() == 'リダイレクト：':
            rdr_flg = True
            dest = _clip_pname(el.getnext().get('href'))
            verbose('rdr dest: ', dest)

            if dest:
                return dest
                # if len(dest) > 1:
                #     _emsg('W',
                #          '"{}"のリダイレクト先を特定できません。もしかして…'.format(
                #              page))
                #     for cand in dest:
                #         _emsg('W', '⇒  ', cand)
                # else:
                #     return dest[0]

    if rdr_flg:
        _emsg('W', '"{}"のリダイレクト先が見つからないか特定できません。'.format(page))
        cands = userarea.xpath('.//a//text()')

        if len(cands) == 1:
            _emsg('W', 'とりあえず"{}"にしておきました。'.format(cands[0]))
            return cands[0]
        elif len(cands):
            _emsg('W', 'もしかして…')
            for cand in cands:
                _emsg('W', '⇒  ', cand)
        else:
            _emsg('W', 'リダイレクトページのようですがリダイレクト先が見つかりません。')

    return ''


def follow_redirect(page):
    """
    リダイレクト先の取得と記録

    辞書REDIRECTS内の値:
    __NON__ ⇒ 実際のページ (リダイレクト不要)
    __NOT_FOUND__ ⇒ page が存在しない
    (リダイレクト先)

    返り値:
    ・実際のページならそのままページ名、
    ・リダイレクト先があればリダイレクト先ページ名、
    ・ページが存在しなければ空文字
    """
    global _REDIRECTS

    verbose('check redirection: ', page)

    dest = _REDIRECTS.get(page, '')

    if dest:
        verbose('"{}" found on REDIRECTS: {}'.format(page, dest))
        if dest == '__NON__':
            # 実際のページなら空文字を返す
            return page
        elif dest != '__NOT_FOUND__':
            # リダイレクト先がわかっていればそれを返す
            return dest
        elif not RECHECK:
            # __NOT_FOUND__ でもRECHECKでなければ空文字を返す
            return ''

    # 未知のページのリダイレクト先チェックまたは再チェック
    url = _up.urljoin('http://sougouwiki.com/d/', quote(page))

    resp, he = open_url(url)

    if resp.status == 200:
        dest = _rdrparser(page, he)
        _REDIRECTS[page] = dest or '__NON__'
    elif resp.status == 404:
        _REDIRECTS[page] = '__NOT_FOUND__'

    verbose('rdr dest: ', dest)
    return dest


def _search_listpage(url, listname, listtype, pid):
    """実際の一覧ページをWiki内で探してみる"""
    # listname = set((listname,)) | set(
    #     _libssw.p_inbracket.split(listname.rstrip(')）')))
    verbose('Searching listpage: listname=', listname, ', pid=', pid)

    # DMM作品ページのURLで検索
    resp, he = open_url(
        'http://sougouwiki.com/search?keywords={}'.format(
            quote(url, safe='')),
        cache=False)

    searesult = he.find_class('result-box')[0].find('p[1]/strong').tail

    if searesult.strip() == 'に該当するページは見つかりませんでした。':
        verbose('url not found on ssw')
        return ()

    found = False
    while not found:
        keywords = he.xpath('//h3[@class="keyword"]/a/text()')
        verbose('list page keywords: ', keywords)

        for word in keywords:
            cand = word.strip().rstrip(' 0123456789')
            verbose('list cand key: ', cand)

            if cand.startswith(listname) or listname.startswith(cand):
                # Wikiページ名にレーベル/シリーズ名が含まれるか、その逆のとき採用
                yield word
                found = True

            if not found and listtype == 'レーベル':
                # レーベル一覧であれば、品番のプレフィクスが含まれるとき採用
                prefix = _libssw.split_pid(pid)[0]
                verbose('prefix: ', prefix)
                if prefix in word and not word.startswith('作品一覧'):
                    verbose('prefix in pid: ', prefix)
                    yield word
                    found = True

        if not found:
            # 次のページがあったらそちらで再度探す
            he = ssw_searchnext(he)
            if he is None:
                break


def check_actuallpage(url, lpage, ltype, pid):
    """
    実際の一覧ページのチェック

    見つかったら_REDIRECTSにキャッシュしておく
    """
    global _REDIRECTS

    verbose('check actual list page on ssw...')

    if not RECHECK \
       and url in _REDIRECTS \
       and _REDIRECTS[url] != '__NOT_FOUND__':
        # キャッシュされてたらそれを返す
        verbose('list page found on REDIRECTS: ', _REDIRECTS[url])
        return lpage if _REDIRECTS[url] == '__NON__' else _REDIRECTS[url]

    pages = tuple(_search_listpage(url, lpage, ltype, pid))
    verbose('list page found: ', pages)

    result = None
    numcand = len(pages)
    if not numcand:
        verbose('list page search result is zero')
        # 見つからなかったらシリーズ/レーベル名で開いてあればそれを返す
        dest = follow_redirect(lpage)
        verbose('dest: ', dest)
        if dest:
            result = dest
    elif numcand == 1:
        # 候補が1個ならそれを返す
        result = pages[0]
    else:
        _emsg('I', '一覧ベージ候補が複数見つかりました:')
        for cand in pages:
            _emsg('I', '⇒ ', cand)

    if result:
        _REDIRECTS[url] = result
        save_cache(_REDIRECTS, _RDRDFILE)

    return result


def stringize_performers(pfmrs, number, follow):
    """出演者文字列の作成"""
    def _build_performerslink(pfmrs, follow):
        """女優リンクの作成"""
        for shown, dest, parened in pfmrs:
            if shown in HIDE_NAMES_V:
                shown, dest, parened = '', '', '(削除依頼対応)'
            elif follow and shown and not dest:
                # 名前が無かったり既にリダイレクト先があったらスルー
                dest = follow_redirect(shown)

            ilink = '{}>{}'.format(shown, dest) if dest and shown != dest \
                    else shown
            yield '[[{}]]{}'.format(ilink, parened) if shown else parened

    pfmrsstr = '／'.join(_build_performerslink(pfmrs, follow))

    if follow:
        save_cache(_REDIRECTS, _RDRDFILE)

    # 「～ほかn名」
    if number == -1:
        pfmrsstr += '　ほか'
        pnum = -1
    elif number == -2:
        pfmrsstr += '　ほか数名'
        pnum = -1
    else:
        pnum = len(pfmrs)
        if number > pnum:
            pfmrsstr += '　ほか計{0}名'.format(number)
            pnum = number

    return pfmrsstr, pnum


_p_base_url = _re.compile(r'(.*/)-/')


def resolve_service(url):
    """サービスの決定"""
    verbose('Resolving service...')
    base = _p_base_url.findall(url)[0]

    if not base or base not in SVC_URL:
        _emsg('E', '未サポートのURLです。')
    else:
        return SVC_URL[base]


_p_cid = _re.compile(r'/cid=([a-z0-9_]+)/?')
_p_id = _re.compile(r'/id=([\d,]+?)/')


def get_id(url, cid=False, ignore=False):
    """URLからIDを取得"""
    try:
        return _p_cid.findall(url) if cid else _p_id.findall(url)[0].split(',')
    except IndexError:
        if ignore:
            return ()
        _emsg('E', 'IDを取得できません: ', url)


# 品番変換個別対応
_sp_pid_indv = (
    (_re.compile(r'^125ud(\d+).*'), r'ud\1r'),           # LEOのレンタル
    (_re.compile(r'^h_093r18(\d+)'), r'r18-\1'),         # チェリーズの一部レーベル
    (_re.compile(r'^h_066fad(\d+).*'), r'fad\1'),        # FAプロのレンタルの一部
    (_re.compile(r'^h_066rhtr(\d+).*'), r'rhtr\1'),      # FAプロのレンタルの一部
    (_re.compile(r'^55t28(\d+)'), r't28-\1'),            # TMAの一部
    (_re.compile(r'^\d{2}id(\d{2})(\d+)'), r'\1id-\2'),  # TMAの一部
    (_re.compile(r'^117?((?:tk)?arm[a-z]?)0?(\d{3}).*'), r'\1-\2'),  # アロマ企画の一部
    (_re.compile(r'^d1(\d+)'), r'd1-\1'),                # ドグマのD1 CLIMAXレーベル
    (_re.compile(r'^ad1(\d+)'), r'ad1-\1'),              # ドグマのAD1 CLIMAXレーベル
    (_re.compile(r'^h_308aoz(\d+z?)'), r'aoz-\1'),       # 青空ソフト
    (_re.compile(r'^(?:h_102)?bnsps(\d+).*'), r'nsps-\1'),  # ながえスタイルのセル版の一部
    (_re.compile(r'^21psd(\d+)'), r'psd+\1'),             # アウダースの一部
    (_re.compile(r'^\d*d1clymax00(\d+)'), r'd1clymax-\1'),  # D1グランプリ
)


def gen_pid(cid, pattern=None):
    """DMMの品番(cid)から正規の品番を生成"""
    if cid.startswith('http://'):
        cid = get_id(cid, True)[0]

    if pattern:
        pid, m = sub(pattern, cid, True)
    else:
        # 個別対応パターン
        for sp in _sp_pid_indv:
            pid, m = sub(sp, cid, True)
            if m:
                break
        else:
            pid, m = sub(sp_pid, cid, True)

    if m:
        pid = pid.upper()

    return pid, cid


class _InvalidPage(Exception):
    pass


class _GetActName:
    """名前の取得"""
    _p_actname1 = _re.compile(r'[)）][(（]')
    _p_actname2 = _re.compile(r'[（(、]')

    def __call__(self, elems):
        try:
            data = elems.find('.//h1').text.strip()
        except AttributeError:
            raise _InvalidPage

        # 複数の女優名チェク ('）（' で分割を試みる)
        named = self._p_actname1.split(data)

        if len(named) == 1:
            # 分割されなかったら名前は1つのみなのでそのまま名前とよみに分割
            named = p_inbracket.split(data)

        # 名前を分割
        name = self._p_actname2.split(named[0])
        # よみを分割
        yomi = self._p_actname2.split(named[1].rstrip('）)'))

        # 現在の名前の格納
        self.current = name[0]

        # # 名前と読みの数が一致しないのときの数合わせ
        # namelen = len(name)
        # yomilen = len(yomi)
        # if namelen > 1 and yomilen == 1:
        #     yomi = yomi * namelen
        # elif namelen == 1 and yomilen > 1:
        #     name = name * yomilen

        verbose('name: {}, yomi: {}'.format(name, yomi))
        return name, yomi

get_actname = _GetActName()


def fmt_name(director: str):
    return ','.join(director.split('：')[-1].split('＋'))


def ret_apacheinfo(elems):
    """Apache公式から作品情報を取得"""

    pid = actress = director = ''

    for t in elems.find_class("detail-main-meta")[0].xpath('li/text()'):

        t = t.strip()

        if t.startswith('品番：'):
            pid = t.split('：')[-1].strip()
            verbose('pid: ', pid)
        elif t.startswith('出演女優：'):
            actress = fmt_name(t)
            verbose('actress: ', actress)
        elif t.startswith('監督：'):
            director = fmt_name(t)
            verbose('director: ', director)

        if pid and director:
            break
    else:
        missings = []

        if not pid:
            missings.append('品番')

        if not director:
            missings.append('監督')

        _emsg('E', 'Apacheサイトから「{}」を取得できませんでした。'.format(
            'と'.join(missings)))

    return pid, actress, director


def get_cookie():
    """
    FirefoxからSMMのCookieを取得

    取得に必要な条件が満たされなければ黙ってFalseを返す
    """
    if _sys.platform == 'win32':
        fx_dir = _Path(_os.environ['APPDATA']).joinpath(
            'Mozilla/Firefox/Profiles')
    elif _sys.platform == 'darwin':
        fx_dir = _Path(_os.environ['HOME']).joinpath(
            'Library/Application Support/Firefox/Profiles')
    elif _sys.platform in {'os2', 'os2emx'}:
        return False
    else:
        fx_dir = _Path(_os.environ['HOME']).joinpath('.mozilla/firefox')
    verbose('fx_dir: ', fx_dir)

    if not fx_dir.exists():
        verbose('Firefox profile dir not found')
        return False

    for d in fx_dir.glob('*'):
        if d.suffix == '.default':
            prof_dir = d
            verbose('firefox profile: ', prof_dir)
            break
    else:
        verbose('firefox default profile not found')
        return False

    conn = _sqlite3.connect(str(fx_dir / prof_dir / 'cookies.sqlite'))
    cur = conn.cursor()
    cur.execute('select value from moz_cookies where '
                'host="supermm.jp" and name="cok_detail_history"')
    batta = cur.fetchone()

    if not batta:
        verbose('smm cookies not found')
        return False
    else:
        batta = batta[0]

    cur.execute('select value from moz_cookies where '
                'baseDomain="supermm.jp" and name="afsmm"')
    afsmm = cur.fetchone()[0]
    cur.close()

    return 'TONOSAMA_BATTA={}; afsmm={}; ses_age=18;'.format(batta, afsmm)


def ssw_searchnext(el):
    """Wiki検索ページの次ページがあれば取得"""
    pagin = el.xpath('.//div[@class="paging-top"]/a[text()="次の20件"]')
    if pagin:
        nextp = pagin[0].get('href')
        resp, he = open_url(_up.urljoin(BASEURL_SSW, nextp), cache=False)
        return he


def open_ssw(*pages):
    """wikiページをウェブブラウザで開く"""
    for p in filter(None, pages):
        _webbrowser.open_new_tab(
            'http://seesaawiki.jp/w/sougouwiki/e/add?pagename={}'.format(
                quote(p)))


_sp_diff = ((_re.compile(r'ISO-8859-1'), 'utf-8'),
            (_re.compile(r'Courier'), 'Sans'),
            (_re.compile(r'nowrap="nowrap"'), ''))


def show_diff(flines, tlines, fdesc, tdesc, context=True):
    """
    差分をとってブラウザで開く

    open_new_tab() のパラメータは実在するuriでなければならないので
    ファイルライクオブジェクトはNG
    """
    diff = _HtmlDiff().make_file(flines,
                                 tlines,
                                 fdesc,
                                 tdesc,
                                 context=context)
    for p in _sp_diff:
        diff = sub(p, diff)
    dummy, tmpf = _mkstemp(suffix='.html', dir=str(_CACHEDIR))
    with open(tmpf, 'w') as f:
        f.writelines(diff)
    _webbrowser.open_new_tab(tmpf)


def save_cache(target, stem):
    """キャッシュ情報の保存"""
    verbose('Saving cache...')

    lockfile = _CACHEDIR / (stem + '.lock')
    pkfile = _CACHEDIR / (stem + '.pickle')
    verbose('cache file: ', pkfile)

    if lockfile.exists():
        now = _time.time()
        mtime = lockfile.stat().st_mtime
        if now - mtime > 180:
            lockfile.unlink()

    for i in range(10):
        try:
            lockfile.touch(exist_ok=False)
        except FileExistsError:
            _time.sleep(1)
        else:
            break
    else:
        _emsg('E', 'キャッシュファイルが10秒以上ロック状態にあります: ', lockfile)

    ctrlc = False

    while True:
        try:
            with pkfile.open('wb') as f:
                _pickle.dump(target, f)
            verbose('cache saved: ({})'.format(stem))
        except KeyboardInterrupt:
            ctrlc = True
        else:
            break

    lockfile.unlink()

    if ctrlc:
        raise SystemExit


def load_cache(stem, default=None, expire=7200):
    """保存されたキャッシュ情報の読み込み"""
    verbose('Loading cache...')

    pkfile = _CACHEDIR / (stem + '.pickle')
    verbose('cache file path: ', pkfile)

    now = _time.time()

    try:
        mtime = pkfile.stat().st_mtime
    except FileNotFoundError:
        verbose('cache file not found')
        return default

    if (now - mtime) > expire:
        # 最終更新から expire 秒以上経ってたら使わない。
        verbose('saved cache too old')
        return default
    else:
        with pkfile.open('rb') as f:
            cache = _pickle.load(f)
        return cache

_REDIRECTS = load_cache(_RDRDFILE, default=_REDIRECTS)


def clear_cache():
    """キャッシュのクリア"""
    _rmtree(str(_CACHEDIR), ignore_errors=True)
    verbose('cache cleared')


def cache_info():
    """キャッシュ情報の出力"""
    size = sum(f.stat().st_size for f in _CACHEDIR.glob('*')) / 1048576
    _emsg('I', 'キャッシュパス: ', _CACHEDIR)
    _emsg('I', 'サイズ: {:.2f}MB'.format(size))
    raise SystemExit
