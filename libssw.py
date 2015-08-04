#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
素人Wiki用スクリプト用ライブラリ
'''
import os as _os
import sys as _sys
import re as _re
import time as _time
import sqlite3 as _sqlite3
import urllib.parse as _up
import fileinput as _fileinput
import pickle as _pickle
import webbrowser as _webbrowser
# import tkinter
from operator import itemgetter as _itemgetter
from multiprocessing import Process as _Process
from collections import namedtuple as _namedtuple, OrderedDict as _OrderedDict
from tempfile import gettempdir as _gettempdir, mkstemp as _mkstemp
from shutil import rmtree as _rmtree
from difflib import HtmlDiff as _HtmlDiff
from http.client import HTTPException as _HTTPException
from pathlib import Path as _Path

try:
    import httplib2 as _httplib2
except ImportError:
    raise SystemExit('httplib2(python3用)をインストールしてください。')

try:
    from lxml.html import fromstring as _fromstring
except ImportError:
    raise SystemExit('lxml(python3用)をインストールしてください。')

__version__ = 20150512

VERBOSE = 0

CACHEDIR = _Path(_gettempdir()) / 'dmm2ssw_cache'
RDRDFILE = 'redirects'

RECHECK = False

BASEURL = 'http://www.dmm.co.jp'
BASEURL_SMM = 'http://supermm.jp'
BASEURL_SSW = 'http://sougouwiki.com'
BASEURL_ACT = 'http://actress.dmm.co.jp'

SVC_URL = {'http://www.dmm.co.jp/mono/dvd/':       'dvd',
           'http://www.dmm.co.jp/rental/':         'rental',
           'http://www.dmm.co.jp/digital/videoa/': 'video',
           'http://www.dmm.co.jp/digital/videoc/': 'ama'}

SERVICEDIC = {
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
OMITWORDS = {'総集編':      '総集編',
             'BEST':       '総集編',
             'Best':       '総集編',
             'ベスト':      '総集編',
             'COMPLETE':   '総集編',
             'コンプリート': '総集編',
             '総編版':      '総集編',

             'DMM初回限定':  '限定盤',
             'DMM限定':     '限定盤',
             '数量限定':     '限定盤',
             '枚限定':       '限定盤',
             '初回限定版':    '限定盤',

             'アウトレット': 'アウトレット',
             '廉価版':      'アウトレット'}
# 【混ぜるな危険】
#  'コレクション'
#  '保存版'
#  '大全集'
#  '全集'

OMITTYPE = ('イメージビデオ', '総集編', 'アウトレット', '限定盤', 'UMD')

# 総集編・再収録専門そうなやつ
# 品番プレフィクス(URL上のもの)
OMNI_PREFIX = (
    '118bst',        # プレステージの総集編
    '118dcm',        # プレステージの総集編
    '118dcx',        # プレステージの総集編
    '118ful',        # プレステージの総集編
    '118kmx',        # プレステージの総集編
    '118mzq',        # プレステージの総集編
    '118pet',        # プレステージの総集編
    '118ppb',        # プレステージの総集編
    '118ppt',        # プレステージの総集編
    '118pre',        # プレステージの総集編
    '118spa',        # プレステージの総集編
    '118spp',        # プレステージの総集編
    '118tgbe',       # プレステージの総集編
    '118tre',        # プレステージの総集編
    '118zesp',       # プレステージの総集編
    '13box',         # グローリークエストの総集編
    '13gqe',         # グローリークエストの総集編
    '13qq',          # グローリークエストの総集編
    '13rvg',         # グローリークエストの総集編
    '13sqv',         # グローリークエストの総集編
    '13ysr',         # グローリークエストの総集編
    '143umd',        # グローバルメディアエンタテインメントの総集編
    '15ald',         # 桃太郎映像出版の総集編
    '15mofd',        # 桃太郎映像出版の総集編
    '164sbdd',       # サイドビーの総集編レーベル クスコ
    '164sbhe',       # サイドビーの総集編レーベル HEROINE
    '17dbr',         # ルビーの総集編シリーズ
    '17hrd',         # ルビーの総集編
    '17kmk',         # ルビーの総集編シリーズ
    '187jame',       # スタイルアートjam/妄想族の総集編
    '187slba',       # スタイルアートLOVE BETES/妄想族の総集編
    '18alsp',        # タカラ映像の総集編
    '18mbox',        # タカラ映像の総集編
    '18mght',        # タカラ映像の総集編
    '1svomn',        # サディスティックビレッジの総集編
    '21issd',        # アウダースジャパンの総集編
    '21pssd',        # アウダースジャパンの総集編
    '23aukb',        # U＆Kの総集編
    '23uksp',        # U＆Kの総集編
    '24hfd',         # ドリームチケットの総集編
    '28drn',         # DRAGON（ハヤブサ） 総集編専門レーベル
    '28gen',         # GIGA TON 総集編専門レーベル
    '28wed',         # EIGHT MAN 総集編専門レーベル
    '29cxaz',        # ジャネス/ladiesの総集編
    '29cwaz',        # ジャネス/ladiesの総集編
    '29djsh',        # ジャネスの総集編
    '29djsj',        # ジャネスの総集編
    '29hwaz',        # ジャネスの総集編
    '2bdclb',        # ワープエンタテインメントの総集編
    '2box',          # ワープエンタテインメントの総集編
    '2clb',          # ワープエンタテインメントの総集編
    '2spbox',        # ワープエンタテインメントの総集編
    '2wpw',          # ワープエンタテインメントの総集編
    '2wsp',          # ワープエンタテインメントの総集編
    '2ycc',          # ワープエンタテインメントの総集編
    '30dmbk',        # MAZO BOYS CLUB (未来フューチャー) の総集編
    '33awtb',        # AVS collector’sの総集編
    '33avsb',        # AVS collector’sの総集編
    '33avsw',        # AVS collector’sの総集編
    '33nopc',        # AVS collector’sの総集編
    '33acec',        # AVS collector’sの総集編
    '33dphb',        # AVS collector’sの総集編
    '33dphc',        # AVS collector’sの総集編
    '33dpnw',        # AVS collector’sの総集編
    '33dsfb',        # AVS collector’sの総集編
    '33exbs',        # AVS collector’sの総集編
    '33igub',        # AVS collector’sの総集編
    '33ncgb',        # AVS collector’sの総集編
    '33plzb',        # AVS collector’sの総集編
    '33zosb',        # AVS collector’sの総集編
    '3bmw',          # ワンズファクトリーの総集編
    '3naw',          # ワンズファクトリーの総集編
    '3swf',          # ワンズファクトリーの総集編
    '434dfda',       # デジタルアークの総集編
    '434dgtl',       # デジタルアークの総集編
    '434gkdfda',     # デジタルアークの総集編
    '434kcda',       # デジタルアークの総集編
    '49cadv',        # クリスタル映像の総集編
    '51cma',         # シネマジックの総集編
    '55hsrm',        # SCREAM 総集編専門レーベル
    '55id',          # TMAの総集編
    '83sbb',         # マルクス兄弟の総集編
    '83scf',         # マルクス兄弟の総集編
    '84bdhyaku',     # 100人 KMPの総集編レーベル
    '84hyaku',       # 100人 KMPの総集編レーベル
    '84hyas',        # 100人 KMPの総集編レーベル
    '9onsd',         # S1の総集編(BD)
    'abcb',          # ABC/妄想族の総集編
    'anhd',          # アンナと花子の総集編
    'atkd',          # Attackers BEST 総集編専門レーベル
    'apao',          # オーロラプロジェクト・アネックスの総集編
    'avsw',          # AVS collector’s の総集編
    'bcdp',          # 総集編メーカー BACK DROP
    'bijc',          # 美人魔女の総集編
    'bomn',          # BoinBB/ABCの総集編
    'bmw',           # ワンズファクトリーの総集編
    'cnz',           # キャンディの総集編
    'corb',          # たぶんCOREの総集編
    'crad',          # クロスの総集編
    'crmn',          # 痴ロモン/妄想族 総集編レーベル
    'daid',          # ダイナマイトエンタープライズの総集編
    'dazd',          # ダスッ！の総集編
    'dgtl',          # デジタルアークの総中編
    'emac',          # DX（エマニエル）の総集編
    'fabs',          # FAプロの総集編
    'h_066fabs',     # FAプロの総集編
    'h_066rabs',     # FAプロ 竜二ベスト
    'h_067nass',     # なでしこの総集編
    'h_068mxsps',    # マキシングの総集編
    'h_086abba',     # センタービレッジの総集編
    'h_086cbox',     # センタービレッジの総集編
    'h_086cvdx',     # センタービレッジの総集編
    'h_086euudx',    # センタービレッジの総集編
    'h_086ferax',    # センタービレッジの総集編
    'h_086gomu',     # センタービレッジの総集編
    'h_086hhedx',    # センタービレッジの総集編
    'h_086hthdx',    # センタービレッジの総集編
    'h_086honex',    # センタービレッジの総集編
    'h_086iannx',    # センタービレッジの総集編
    'h_086jrzdx',    # センタービレッジの総集編
    'h_086oita',     # センタービレッジの総集編
    'h_086qizzx',    # センタービレッジの総集編
    'h_108mobsp',    # モブスターズの総集編
    'h_127ytr',      # NONの総集編
    'h_175dbeb',     # BabyEntertainmentの総集編
    'h_175dxdb',     # BabyEntertainmentの総集編
    'h_179dmdv',     # ゲインコーポレーションの総集編
    'h_237swat',     # シリーズ ○○三昧 プラネットプラスの総集編シリーズ
    'h_254kanz',     # 完全盤 STAR PARADISEの総集編レーベル
    'h_254mgdn',     # MEGADON STAR PARADISEの総集編レーベル
    'h_254wnxg',     # VOLUME STAR PARADISEの総集編レーベル
    'h_443hpr',      # 催眠研究所の総集編シリーズ
    'h_479gah',      # GO AHEAD 総集編レーベル (GALLOP)
    'h_479gfs',      # SPECIAL GIFT 総集編レーベル (GALLOP)
    'h_479gft',      # GIFT 総集編レーベル (GALLOP)
    'h_479gfx',      # GIFT DX 総集編レーベル (GALLOP)
    'h_479gne',      # NEO GIFT 総集編レーベル (GALLOP)
    'h_537odfg',     # ワンダフルの総集編
    'h_540exta',     # エクストラ 総集編専門レーベル
    'h_543rlod',     # 乱熟 総集編メーカー
    'h_543rloh',     # 乱熟 総集編メーカー
    'h_543rloj',     # 乱熟 総集編メーカー
    'h_543rlok',     # 乱熟 総集編メーカー
    'h_543rloi',     # 乱熟 総集編メーカー
    'h_544yuyg',     # ケンシロウプロジェクトの総集編
    'h_797impa',     # impact（サンワソフト）の総集編
    'h_838chao',     # CHAOS（Pandora）総集編レーベル (Pandra)
    'h_865jkn',      # 総集編シリーズ 完熟肉汁つゆだく交尾集
    'hjbb',          # はじめ企画の総集編
    'hndb',          # 本中の総集編
    'hoob',          # AVS collector’sの総集編
    'idbd',          # アイポケの総集編
    'jfb',           # Fitchの総集編
    'jomn',          # ABC/妄想族の総集編
    'jusd',          # マドンナ/Madonnaの総集編
    'kibd',          # kira☆kiraの総集編
    'koze',          # ローグ・プラネット（フェチ）/妄想族の総集編
    'krbv',          # カルマ/BEST 総集編専門レーベル
    'kwbd',          # kawaiiの総集編
    'mbyd',          # 溜池ゴローの総集編
    'mibd',          # ムーディーズの総集編
    'mitb',          # 蜜月の総集編
    'mkck',          # E-BODYの総集編
    'mmb',           # 桃太郎ベスト
    'mvbd',          # エムズビデオグループの総集編
    'n_1155dslb',    # グラッソの復刻版(?)
    'obe',           # マドンナ/Obasanの総集編
    'onsd',          # S1の総集編
    'oomn',          # お母さん.com/ABCの総集編
    'rbb',           # ROOKIEの総集編
    'pbd',           # プレミアムの総集編
    'ppbd',          # OPPAIの総集編
    'ptko',          # パツキン/ABCの総集編
    'rabs',          # FAプロ 竜二ベスト
    'slba',          # スタイルアート/妄想族の総集編
    'stol',          # 変態紳士倶楽部の総集編
    'swac',          # 湘南/妄想族の総集編
    'tmbt',          # teamZEROの総集編
    'tomn',          # TEPPANの総集編
    'tywd',          # 乱丸の総集編
    'veq',           # VENUSの総集編
    'vero',          # VENUSの総集編
    'veve',          # VENUSの総集編
    'vvvd',          # ヴィの総集編

    '15awad12',      # 桃太郎映像出版の総集編作品
    '15send167',     # 桃太郎映像出版の総集編作品
    'bf249',         # BeFreeの総集編作品
    'bf315',         # BeFreeの総集編作品
    'bf392',         # BeFreeの総集編作品
    'h_746ssr051',   # SOSORUの総集編作品
)
# 品番正規表現
OMNI_PATTERN = (
    _re.compile(r'^(?:[hn]_)?\d*aaj'),  # AV30
    _re.compile(r'^(?:837?)?sbb'),      # コレクターズエディション (マルクス兄弟)
)

# イメージビデオ専門レーベル
IV_PREFIX = (
    'h_803pnch',    # Panchu
    )

ROOKIE = ('rki', '9rki')

# 既定のリンク先は同名別女優がいるためリダイレクトにできない女優をあらかじめ登録
REDIRECTS = {'黒木麻衣':  '花野真衣',
             '若菜あゆみ': '若菜あゆみ(人妻)',
             '藤原ひとみ': '藤原ひとみ(kawaii*)',
             '佐々木玲奈': '佐々木玲奈(2013)',
             'すみれ':    '東尾真子',
             'EMIRI':    '丘咲エミリ',
             '松嶋葵':    '松嶋葵（2014）',
             '和久井ナナ': 'ふわりゆうき'}

# 事務所から送信防止措置依頼されている女優
HIDE_NAMES = {'1023995': '立花恭子',
              '1024279': '藤崎かすみ',
              '1026305': '北野ひな'}


p_number = _re.compile(r'\d+')
p_delim = _re.compile(r'[/／,、]')
p_inbracket = _re.compile(r'[(（]')
p_linkpare = _re.compile(r'\[\[(.+?)(?:>(.+?))?\]\]')
p_list_article = _re.compile(r'/article=(.+?)/')
p_hiragana = _re.compile(r'[ぁ-ゞー]')
p_neghirag = _re.compile(r'[^ぁ-ゞー]')

sp_pid = (_re.compile(r'^(?:[hn]_)?\d*([a-z]+)(\d+).*', _re.I), r'\1-\2')

# 品番変換個別対応
sp_pid_indv = (
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


t_wikisyntax = str.maketrans('[]~', '［］～')
t_filename = str.maketrans(r'/:<>?"\*|;', '_' * 10)
t_nl = str.maketrans('', '', '\r\n')
t_pidsep = str.maketrans('', '', '+-')


DummyResp = _namedtuple('DummyResp', 'status,fromcache')


def ownname(path):
    return _Path(path).stem

OWNNAME = ownname(__file__)


class Verbose:
    '''デバッグ用情報の出力'''
    def __init__(self, ownname, verbose):
        self._ownname = ownname
        self.verbose = verbose

    def __call__(self, *msg):
        if self.verbose:
            msg = ''.join(str(m) for m in msg)
            print('({0}): >>> {1}'.format(self._ownname, msg),
                  file=_sys.stderr, flush=True)

verbose = Verbose(OWNNAME, VERBOSE)


class Emsg:
    '''標準エラー出力へメッセージ出力'''
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

emsg = Emsg(OWNNAME)


class OrderedDict2(_OrderedDict):
    '''
    先頭のアイテムの値だけを返すメソッドhead()と
    最後のアイテムの値だけを返すメソッドlast()付きの
    OrderedDict
    '''
    def head(self):
        '''先頭のアイテムの値を返す'''
        if not len(self):
            raise KeyError('データが0件です。')
        return self[self._OrderedDict__root.next.key]

    def last(self):
        '''最後のアイテムの値を返す'''
        if not len(self):
            raise KeyError('データが0件です。')
        return self[self._OrderedDict__root.prev.key]


# def copy2clipboard(string):
#     '''クリップボードへコピー'''
#     verbose('copy string: {}'.format(repr(string)))
#     root = tkinter.Tk(screenName=':0.0')
#     root.withdraw()
#     root.clipboard_clear()
#     root.clipboard_append(string)
#     root.destroy()


class Summary:
    '''作品情報格納用'''
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

    def tsv(self, *args):
        attrs = args or self.__slots__
        return '\t'.join(self.stringize(*attrs))

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


# class ProductProps:
#     '''一覧情報保管用(後方互換性重視)'''
#     __slots__ = ('url',
#                  'release',
#                  'title',
#                  'subtitle',
#                  'pid',
#                  'cid',
#                  'actress',
#                  'number',
#                  'director',
#                  'note')

#     def __init__(self,
#                  url='',
#                  release='',
#                  title='',
#                  subtitle='',
#                  pid='',
#                  cid='',
#                  actress=[],
#                  number=0,
#                  director=[],
#                  note=[]):
#         for key in self.__slots__:
#             value = eval(key)
#             if isinstance(value, list):
#                 setattr(self, key, value[:])
#             else:
#                 setattr(self, key, value)

#     def __contains__(self, key):
#         return hasattr(self, key)

#     def __getitem__(self, key):
#         return getattr(self, key)

#     def __setitem__(self, key, value):
#         setattr(self, key, value)

#     def __call__(self, *keys):
#         return self.values(*keys)

#     def __iter__(self):
#         return iter(self.__slots__)

#     def keys(self):
#         return self.__slots__

#     def values(self, *keys):
#         attrs = keys or self.__slots__
#         return list(getattr(self, k) for k in attrs)

#     def items(self, *args):
#         attrs = args or self.__slots__
#         return list((a, getattr(self, a)) for a in attrs)

#     def tsv(self, *args):
#         attrs = args or self.__slots__
#         return '\t'.join(self.stringize(*attrs))

#     def stringize(self, *args):
#         attrs = args or self.__slots__
#         for a in attrs:
#             v = getattr(self, a)
#             if a == 'note' and not v:
#                 break
#             if isinstance(v, int):
#                 v = str(v) if v else ''
#             elif isinstance(v, list):
#                 v = ','.join(v)
#             yield v

#     def __set(self, attr, other, overwrite):
#         this = getattr(self, attr)
#         if isinstance(other, list):
#             other = other.copy()
#         if not this or overwrite:
#             setattr(self, attr, other)

#     def merge(self, otherobj, overwrite=False):
#         if hasattr(otherobj, 'keys'):
#             for key in otherobj:
#                 val = otherobj[key]
#                 if val:
#                     self.__set(key, val, overwrite)
#         else:
#             for key, val in otherobj:
#                 if val:
#                     self.__set(key, val, overwrite)

#     def update(self, otherobj):
#         self.merge(otherobj, overwrite=True)


def sub(p_list, string, n=False):
    '''re.sub()、re.subn()ラッパー'''
    return p_list[0].subn(p_list[1], string) if n \
        else p_list[0].sub(p_list[1], string)


def quote(string, safe='/', encoding='euc_jisx0213', errors=None):
    return _up.quote(string, safe=safe, encoding=encoding,
                     errors=errors).replace('-', '%2d')


def unquote(string, encoding='euc_jisx0213', errors='replace'):
    return _up.unquote(string, encoding=encoding, errors=errors)


def clip_pname(url):
    return unquote(url.rsplit('/', 1)[-1])


def rm_nlcode(string):
    return string.translate(t_nl)


def rm_hyphen(string):
    return string.translate(t_pidsep)


def files_exists(mode, *files):
    '''同名のファイルが存在するかどうかチェック'''
    for f in files:
        if f in (_sys.stdin, _sys.stdout):
            continue
        verbose('file: ', f)
        isexist = _os.path.exists(f)
        if mode == 'r' and not isexist:
            emsg('E', 'ファイルが見つかりません: ', f)
        elif mode == 'w' and isexist:
            emsg('E', '同名のファイルが存在します (-r で上書きします): ', f)


def inprogress(msg):
    '''「{}中...」メッセージ'''
    if not VERBOSE:
        print('{}  '.format(msg), end='\r', file=_sys.stderr, flush=True)


def gen_no_omits(no_omit):
    return OMITTYPE[:no_omit]


def le80bytes(string, encoding='euc_jisx0213'):
    '''Wikiページ名最大長(80バイト)チェック'''
    return len(bytes(string, encoding)) <= 80


def gen_ntfcols(tname, fsource):
    '''表形式ヘッダから名前付きタプルを作成'''
    if isinstance(fsource, str):
        fsource = ('TITLE' if c == 'SUBTITLE' else c
                   for c in fsource.replace('~', '').split('|'))
    return _namedtuple(tname, fsource, rename=True)


class __OpenUrl:
    '''URLを開いて読み込む'''
    _p_charset = _re.compile(r'charset=([a-zA-Z0-9_-]+);?')

    def __init__(self):
        if VERBOSE > 1:
            _httplib2.debuglevel = 1
        self.__http = _httplib2.Http(str(CACHEDIR))
        self.__wait = dict()

    def __sleep(self):
        _time.sleep(5)

    def _url_openerror(self, name, info, url):
        '''URLオープン時のエラーメッセージ'''
        emsg('E',
             'URLを開く時にエラーが発生しました ({})。詳細: {}, url={}'.format(
                 name, info, url))

    def _resolve_charset(self, resp, html):
        '''文字エンコーディングの解決'''
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
            emsg('E', '不正なURL?: ', url)

        if cache:
            maxage = '7200' if site == 'sougouwiki.com' else '86400'
            headers = {'cache-control': 'private, max-age={}'.format(maxage)}
        else:
            headers = dict()

        if set_cookie:
            headers['cookie'] = set_cookie
        verbose('http headers: ', headers)

        for i in range(5):

            if site in self.__wait and self.__wait[site].is_alive():
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
                        emsg('E', '(おそらくサーバー側に問題のある)HTTP例外です。')
                    else:
                        url = url.replace('/limit=120/', '/limit=60/')
                resp = DummyResp(status=0, fromcache=False)
            verbose('http resp: ', resp)
            verbose('fromcache: ', resp.fromcache)

            if not resp.fromcache:
                verbose('start wait_', site)
                self.__wait[site] = _Process(target=self.__sleep, daemon=True)
                self.__wait[site].start()

            # HTTPステータスがサーバ/ゲートウェイの一時的な問題でなければ終了
            if resp.status and not 500 <= resp.status <= 504:
                if resp.status not in (200, 404):
                    emsg('W', 'HTTP status: ', resp.status)
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
                emsg('E', 'HTMLの読み込みに失敗しました: resp=', resp)

        return resp, _fromstring(html) if to_elems else html

open_url = __OpenUrl()


def check_omitword(title):
    '''タイトル内の除外キーワードチェック'''
    for key in OMITWORDS:
        if key in title:
            verbose('omit key, word: {}, {}'.format(key, OMITWORDS[key]))
            yield OMITWORDS[key], key


def check_omitprfx(cid, prefix=OMNI_PREFIX, patn=OMNI_PATTERN):
    '''隠れ総集編チェック(プレフィクス版)'''
    return any(cid.startswith(p) for p in prefix) or \
        any(p.search(cid) for p in patn)


p_omnivals = (_re.compile(r'(?:[2-9]\d|\d{3,})[人名]'),
              _re.compile(r'(?:[5-9]\d|\d{3,})連?発'),
              _re.compile(r'(?:[4-9]|\d{2,})時間'),
              _re.compile(r'(?:2[4-9]\d|[4-9]\d{2}|\d{4,})分'))

def check_omnivals(title):
    '''隠れ総集編チェック(関連数値編)'''
    def pick():
        for p in p_omnivals:
            m = p.findall(title)
            if m:
                yield m[0]
    hit = tuple(pick())
    if len(hit) > 1:
        return hit


p_ge4h = _re.compile(r'(?:[4-9]|\d{2,})時間')
p_ge200m = _re.compile(r'(?:[2-9]\d{2}|\d{4,})分')

def is_omnirookie(cid, title):
    '''ROOKIE隠れ総集編チェック'''
    if check_omitprfx(cid, ROOKIE):
        # ROOKIEチェック
        hh = p_ge4h.findall(title)
        mmm = p_ge200m.findall(title)
        return hh, mmm
    else:
        return None, None


class DMMTitleListParser:
    '''一覧ページの解析'''
    _sp_tsuffix = (_re.compile(r' - \S*( - DMM.R18)?$'), '')

    def __init__(self, no_omits=OMITTYPE, patn_pid=None, show_info=True):
        self._no_omits = no_omits
        self._patn_pid = patn_pid
        self._show_info = show_info
        self.omitted = 0
        self.priurl = ''
        self.article = []

    def _get_article(self, he):
        '''アーティクル名の取得'''
        try:
            article = he.find('head/title').text.strip()
        except AttributeError:
            article = ''

        # wiki構文と衝突する文字列の置き換え
        article = article.translate(t_wikisyntax)
        article = sub(self._sp_tsuffix, article)

        return article

    def _ret_titles(self, ttl):
        '''作品タイトルとURLの取得'''
        def omit(key, word):
            if self._show_info or VERBOSE:
                emsg('I', 'ページを除外しました: cid={}, {:<20}'.format(
                    cid, 'reason=("{}", "{}")'.format(key, word)))
            self.omitted += 1

        t_el = ttl.find('a')
        title = t_el.text
        path = t_el.get('href')
        url = _up.urljoin(BASEURL, path)

        pid, cid = gen_pid(url, self._patn_pid)
        cid = cid.lstrip('79')

        # 除外作品チェック (タイトルから)
        for key, word in check_omitword(title):
            if key not in self._no_omits:
                omit(key, word)
                return False, False

        if '総集編' not in self._no_omits:
            # 隠れ総集編チェック
            if check_omitprfx(cid, OMNI_PREFIX):
                omit('総集編', cid)
                return False, False

            omnival = check_omnivals(title)
            if omnival:
                omit('総集編', omnival)
                return False, False

            hh, mmm = is_omnirookie(cid, title)
            if hh or mmm:
                omit('ROOKIE', hh or mmm)
                return False, False

        if 'イメージビデオ' not in self._no_omits:
            # 隠れIVチェック
            if check_omitprfx(cid, IV_PREFIX):
                omit('イメージビデオ', cid)
                return False, False

        return url, Summary(url=url, title=title, pid=pid, cid=cid)

    def _ret_nextpage(self, he):
        '''ページネーション処理'''
        try:
            pagins = he.find_class('list-boxpagenation')[0].find('ul')
        except IndexError:
            return False

        for a in reversed(pagins.xpath('li/a')):
            if a.text == '次へ':
                nextpath = a.get('href')
                break
        else:
            nextpath = False

        return nextpath and _up.urljoin(BASEURL, nextpath)

    def __call__(self, he):
        '''解析実行'''
        verbose('Parsing TitleList')

        self.article.append((self._get_article(he), self.priurl))

        self.nexturl = self._ret_nextpage(he)

        return (self._ret_titles(ttl) for ttl in he.find_class('ttl'))


class IsGeaterEqualId:
    '''品番の比較'''
    def _is_ge_cid(self, cid):
        return cid >= self.key_id

    def _is_ge_pid(self, pid):
        prefix, number = split_pid(pid)
        return prefix == self.key_id[0] and number >= self.key_id[1]

    def __init__(self, key_id, attr):
        if not key_id:
            self._is_ge = lambda x: False
        else:
            self.key_id = split_pid(key_id) if attr == 'pid' else key_id
            self._is_ge = self._is_ge_pid if attr == 'pid' else self._is_ge_cid

    def __call__(self, cand):
        return self._is_ge(cand)


sp_wikis = (_re.compile(r' "target="_blank"'), r'" target="_blank"')

def from_dmm(listparser, priurls, pages_last=0, key_id=None, idattr='',
             ignore=False, show_info=True):
    '''DMMから作品一覧を取得'''
    verbose('Start parsing DMM list pages')

    is_ge_id = IsGeaterEqualId(key_id, idattr)

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
                emsg('E',
                     '指定した条件でページは見つかりませんでした: url=',
                     searchurl)
            elif resp.status != 200:
                emsg('E',
                     'URLを開く際にエラーが発生しました: staus=',
                     resp.status)

            # 構文ミスの修正
            # html = sub(sp_wikis, html)

            # HTMLの解析
            for url, prop in listparser(he):
                if url:

                    yield url, prop

                    if is_ge_id(getattr(prop, idattr, False)):
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


p_name = _re.compile(
    r'(?P<fore>[\w>]*)?(?P<paren>[(（][\w>]*[）)])?(?P<back>[\w>]*)?')

def parse_names(name):
    '''
    出演者情報の解析(rawテキスト)
    dmm2ssw.py -a オプション渡しとTSVからインポート用
    '''
    verbose('Parsing name...')

    # カッコ括りの付記の分割
    m = p_name.search(name)
    verbose('m.groups(): ', m.groups())

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


p_etc = _re.compile(r'ほか\w*?計(\d+)名')

def ret_numofpfmrs(etc):
    number = None

    m = p_etc.findall(etc)

    if m:
        number = int(m[0])
    elif etc == 'ほか':
        number = -1
    elif etc == 'ほか数名':
        number = -2

    return number


def cvt2int(item):
    return int(item) if item else 0


def from_tsv(files):
    '''タイトル一覧をファイルからインポートするジェネレータ(TSV)'''
    files_exists('r', *files)
    verbose('from tsv file: {}'.format(files))

    with _fileinput.input(files=files) as f:
        for row in f:
            # タブ区切りなので改行を明示して除去してタブを明示して分割
            row = tuple(c.strip() for c in row.rstrip('\n').split('\t'))
            verbose('row: ', row)

            # 女優名がある場合分割
            actress = p_delim.split(row[3]) if row[3] else []
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
    '''タイトル一覧をウィキテキスト(表形式)からインポート'''
    _p_interlink = _re.compile(r'(\[\[.+?\]\])')

    def __init__(self):
        self.article = ''

    def _parse_names(self, name):
        '''出演者情報の解析(ウィキテキスト)'''
        shown = dest = parened = ''

        for e in self._p_interlink.split(name):

            if not e:
                continue

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

                verbose('md: {}, {}, {}, {}, {}'.format(md.TITLE, pid, url,
                                                        actress, md.NOTE))
                yield url, Summary(url=url,
                                   title=md.TITLE,
                                   pid=pid,
                                   actress=actress.copy(),
                                   number=number,
                                   note=note)

            if Cols is None:
                emsg('E', '素人系総合Wikiの一覧ページのウィキテキストではないようです: ',
                     _fileinput.filename())


from_wiki = _FromWiki()


class _FromHtml:
    '''
    素人総合WikiページをURL(HTML)で読み込んでインポート
    '''
    def _unquotename(self, el):
        '''URLからページ名を取得'''
        url = el.get('href')
        if not url.startswith(BASEURL_SSW):
            return url
        return clip_pname(el.get('href'))

    def _enclose(self, ph):
        return ph if ph.startswith('(') else '({})'.format(ph)

    def _parse_performers(self, td):
        '''出演者カラムの解析(FromHtml)'''

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
                for ph in fores:
                    if ph:
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
                self.number = ret_numofpfmrs(splitetc[-1])
                if len(splitetc) > 1:
                    tailtxt = splitetc[0]
                elif self.number is not None:
                    tailtxt = ''

                tails = p_delim.split(tailtxt)

                # 内部リンクに付随する文字列がないかチェック
                yield shown, dest, tails.pop(0) if tails[0] else ''

                for ph in tails:
                    if ph:
                        yield '', '', self._enclose(ph)

    def _parse_notes(self, note):
        '''NOTEの解析'''
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
            for th in iterth:
                yield 'TITLE' if th.text == 'SUBTITLE' else th.text

        for wurl in wikiurls:

            if wurl.startswith('http://'):
                resp, he = open_url(wurl, cache=cache)
                if resp.status == 404:
                    emsg('E', 'ページが見つかりません: ', wurl)
            else:
                with open(wurl, 'rb') as f:
                    he = _fromstring(f.read())

            try:
                self.article = he.find(
                    './/div[@id="page-header-inner"]//h2').text.strip()
            except AttributeError:
                emsg('E', '素人系総合Wiki一覧ページのHTMLではないようです: ', wurl)

            userarea = he.find_class('user-area')[0]

            for tbl in userarea.iterfind('.//table'):

                Cols = gen_ntfcols(
                    'Cols', _makeheader(tbl.find('.//tr[th]').iterfind('th')))

                for tr in tbl.iterfind('.//tr[td]'):
                    self.number = 0

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

                    verbose('md: {}, {}, {}, {}, {}'.format(title, pid, url,
                                                            actress, note))
                    yield url, Summary(url=url,
                                       title=title,
                                       pid=pid,
                                       actress=actress.copy(),
                                       number=self.number,
                                       note=note)

from_html = _FromHtml()


def join_priurls(retrieval, *keywords, service='dvd'):
    '''基底URLの作成'''
    return tuple('{}/{}/-/list/=/article={}/id={}/sort=date/'.format(
        BASEURL, SERVICEDIC[service][1], retrieval, k) for k in keywords)


def build_produrl(service, cid):
    return '{}/{}/-/detail/=/cid={}/'.format(
        BASEURL, SERVICEDIC[service][1], cid)


def getnext_text(elem, xpath=False):
    '''.getnext()してtextしてstrip()'''
    if xpath:
        return [t.strip().strip('-')
                for t in elem.getnext().xpath('{}/text()'.format(xpath))]
    else:
        nexttext = elem.getnext().text
        return nexttext.strip().strip('-') if nexttext else None


def _rdrparser(page, he):
    '''
    wikiリダイレクトページかどうかの検出
    '''
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
            dest = clip_pname(el.getnext().get('href'))
            verbose('rdr dest: ', dest)

            if dest:
                return dest
                # if len(dest) > 1:
                #     emsg('W',
                #          '"{}"のリダイレクト先を特定できません。もしかして…'.format(
                #              page))
                #     for cand in dest:
                #         emsg('W', '⇒  ', cand)
                # else:
                #     return dest[0]

    if rdr_flg:
        emsg('W', '"{}"のリダイレクト先が見つからないか特定できません。'.format(page))
        cands = userarea.xpath('.//a//text()')

        if len(cands) == 1:
            emsg('W', 'とりあえず"{}"にしておきました。'.format(cands[0]))
            return cands[0]
        elif len(cands):
            emsg('W', 'もしかして…')
            for cand in cands:
                emsg('W', '⇒  ', cand)
        else:
            emsg('W', 'リダイレクトページのようですがリダイレクト先が見つかりません。')

    return ''


def follow_redirect(page):
    '''
    リダイレクト先の取得と記録
    辞書REDIRECTS内の値:
    __NON__ ⇒ 実際のページ (リダイレクト不要)
    __NOT_FOUND__ ⇒ page が存在しない
    (リダイレクト先)

    返り値:
    ・実際のページならそのままページ名、
    ・リダイレクト先があればリダイレクト先ページ名、
    ・ページが存在しなければ空文字
    '''
    global REDIRECTS

    verbose('check redirection: ', page)

    dest = REDIRECTS.get(page, '')

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
        REDIRECTS[page] = dest or '__NON__'
    elif resp.status == 404:
        REDIRECTS[page] = '__NOT_FOUND__'

    verbose('rdr dest: ', dest)
    return dest


def stringize_performers(pfmrs, number, follow):
    '''
    出演者文字列の作成
    '''
    def _build_performerslink(pfmrs, follow):
        '''女優リンクの作成'''
        verbose('pfmrs: ', pfmrs)
        for shown, dest, parened in pfmrs:
            if shown in HIDE_NAMES.values():
                shown, dest, parened = '', '', '(削除依頼対応)'
            elif follow and shown and not dest:
                # 名前が無かったり既にリダイレクト先があったらスルー
                dest = follow_redirect(shown)

            ilink = '{}>{}'.format(shown, dest) if dest and shown != dest \
                    else shown
            yield '[[{}]]{}'.format(ilink, parened) if shown else parened

    pfmrsstr = '／'.join(_build_performerslink(pfmrs, follow))

    if follow:
        save_cache(REDIRECTS, RDRDFILE)

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


p_base_url = _re.compile(r'(.*/)-/')

def resolve_service(url):
    '''サービスの決定'''
    verbose('Resolving service...')
    base = p_base_url.findall(url)[0]
    verbose('base url: ', base)
    if not base or base not in SVC_URL:
        emsg('E', '未サポートのURLです。')
    else:
        return SVC_URL[base]


p_cid = _re.compile(r'/cid=([a-z0-9_]+)/?')
p_id = _re.compile(r'/id=([\d,]+?)/')

def get_id(url, cid=False, ignore=False):
    '''URLからIDを取得'''
    try:
        return p_cid.findall(url) if cid else p_id.findall(url)[0].split(',')
    except IndexError:
        if ignore:
            return ()
        emsg('E', 'IDを取得できません: ', url)


def gen_pid(cid, pattern=None):
    '''URLから品番を生成'''
    if cid.startswith('http://'):
        cid = get_id(cid, True)[0]

    if pattern:
        pid, m = sub(pattern, cid, True)
    else:
        # 個別対応パターン
        for sp in sp_pid_indv:
            pid, m = sub(sp, cid, True)
            if m:
                break
        else:
            pid, m = sub(sp_pid, cid, True)

    if m:
        pid = pid.upper()

    return pid, cid


p_splitid = _re.compile(r'([a-z]+)[+-]?(\d+)', _re.I)

def split_pid(pid):
    return p_splitid.findall(pid)[0]


def sort_by_id(products, reverse=False):
    '''
    桁数が揃ってない品番もソート
    '''
    def _make_items(products, maxdigit):
        '''URL(キー)と桁を揃えた品番'''
        for url in products:
            prefix, number = split_pid(products[url].pid)
            yield url, '{0}{1:0>{2}}'.format(prefix, number, maxdigit)

    maxdigit = max(
        p_number.findall(products[p].pid)[0] for p in products)

    return (url for url, pid in sorted(_make_items(products, maxdigit),
                                       key=_itemgetter(1),
                                       reverse=reverse))


class InvalidPage(Exception):
    pass


class _GetActName:
    '''名前の取得'''
    _p_actname1 = _re.compile(r'[)）][(（]')
    _p_actname2 = _re.compile(r'[（(、]')

    def __call__(self, elems):
        try:
            data = elems.find('.//h1').text.strip()
        except AttributeError:
            raise InvalidPage

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


def fmt_name(director):
    return ','.join(director.split('：')[-1].split('＋'))


def ret_apacheinfo(elems):
    '''Apache公式から作品情報を取得'''

    pid = actress = director = ''

    for t in elems.find_class("detail-main-meta")[0].xpath('li/text()'):
        verbose('t: ', t)

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

        emsg('E', 'Apacheサイトから「{}」を取得できませんでした。'.format(
            'と'.join(missings)))

    return pid, actress, director


def get_cookie():
    '''
    FirefoxからSMMのCookieを取得
    取得に必要な条件が満たされなければ黙ってFalseを返す
    '''
    if _sys.platform == 'win32':
        fx_dir = _Path(_os.environ['APPDATA']).joinpath(
            'Mozilla/Firefox/Profiles')
    elif _sys.platform == 'darwin':
        fx_dir = _Path(_os.environ['HOME']).joinpath(
            'Library/Application Support/Firefox/Profiles')
    elif _sys.platform in ('os2', 'os2emx'):
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


def open_ssw(page):
    '''wikiページをウェブブラウザで開く'''
    if page:
        _webbrowser.open_new_tab(
            'http://seesaawiki.jp/w/sougouwiki/e/add?pagename={}'.format(
                quote(page)))


sp_diff = ((_re.compile(r'ISO-8859-1'), 'utf-8'),
           (_re.compile(r'Courier'), 'Sans'),
           (_re.compile(r'nowrap="nowrap"'), ''))

def show_diff(flines, tlines, fdesc, tdesc, context=True):
    '''差分をとってブラウザで開く'''
    diff = _HtmlDiff().make_file(flines,
                                 tlines,
                                 fdesc,
                                 tdesc,
                                 context=context)
    for p in sp_diff:
        diff = sub(p, diff)
    dummy, tmpf = _mkstemp(suffix='.html', dir=str(CACHEDIR))
    with open(tmpf, 'w') as f:
        f.writelines(diff)
    _webbrowser.open_new_tab(tmpf)


def save_cache(target, stem):
    '''キャッシュ情報の保存'''

    verbose('Saving cache...')

    lockfile = CACHEDIR / (stem + '.lock')
    pkfile = CACHEDIR / (stem + '.pickle')
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
        emsg('E', 'キャッシュファイルが10秒以上ロック状態にあります: ', lockfile)

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
    '''保存されたキャッシュ情報の読み込み'''
    verbose('Loading cache...')

    pkfile = CACHEDIR / (stem + '.pickle')
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

REDIRECTS = load_cache(RDRDFILE, default=REDIRECTS)


def clear_cache():
    '''キャッシュのクリア'''
    _rmtree(str(CACHEDIR), ignore_errors=True)
    verbose('cache cleared')
