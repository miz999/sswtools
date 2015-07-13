#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
DMMのURLからページを取得し素人系総合wiki用ウィキテキストを作成する

書式:
dmm2ssw.py [DMM作品ページのURL] [オプション...]


説明:
    オプションで与えられない情報は可能な限りDMMのページから取得してウィキテキスト
    を作成し標準出力へ出力する。

    女優ページ、レーベル/シリーズ一覧ページのウィキテキスト(-t オプション)、および
    その両方(-tt オプション)を作成できる。

    DVD通販、DVDレンタル、動画-ビデオ/-素人のページに対応しているはず。

    ■タイトルの自動編集
    タイトルに「（ハート）」と「◆」があった場合は「♥」に置き換える。
    その他wiki構文上問題のある文字列があれば全角に置き換える([]や~)。
    置き換えた場合、元のDMM上のタイトルはコメントとして残す(検索用)。
    --disable-modify-title オプションが与えられるとこれらの置き換えは
    行わない。

    ■無駄に長すぎるタイトルの一部対応
    アパッチとSCOOPの作品に関してはタイトルをメーカー公式サイトから取得する。
    HunterおよびATOMについては対応不可(hunterpp.pyにて対応)。

    ■女優名の自動編集
    女優名に過去の芸名が付記されている場合(「現在の芸名 (旧芸名...)」)は旧芸名を
    除去する。
    --disable-strip-oldname オプションが与えられると除去しない。
    削除依頼が出ている女優名は強制的に「(削除依頼対応)」に置き換えられる。

    ■SMM(supermm.jp)からの出演者情報の補完
    DMM上から出演者情報が得られなかった場合、以下の条件においてSMMの作品ページから
    出演者情報の取得を試みる。
    ・DVD/Blu-rayセル版であること
    ・Firefoxがインストールされていること
    ・Firefox上でSMMのCookieを受け入れる状態になっていること
    ・一度FirefoxからデフォルトプロファイルでSMMのアダルトページにアクセスして
      年齢認証を行っていること(Cookieの期限が24時間のようなので、1日に1回行えばよいはず)
    SMM上でも仮の名前のときがあるため、SMM上ですべてひらがなの名前のときはその名前の
    女優名が存在しなければ内部リンクにしない。
    --disable-check-smm オプションが与えられると出演者情報がなくてもSMMを見に
    行かない。

    ■ジュエル系の出演者名は無視
    ジュエル系の出演者名は本人の女優名ではないことがほとんどなので出演者情報があっても
    無視する。登録してあるジュエル系メーカーは以下の通り:
'''
IGNORE_PERFORMERS = {'45067': 'KIプランニング',
                     '45339': '豊彦',
                     '45352': 'リアルエレメント'}

''' ■リダイレクトページの検出とリダイレクト先の自動取得
    Wikiの出演者名や一覧ページがリダイレクトページかどうかチェックし、リダイレクト
    ページならリダイレクト先を取得してリンク先にする。
    -f オプションが与えられるとリダイレクトかどうかチェックしない。

    ■実際の一覧ページ名の自動取得
    一覧ページ名を実際のWiki上の記事名から探して適切なリンク先の取得を試みる。
    (「DANDY」→「DANDY 2」など)
    作品のDMMのURLで検索するため、一覧ページにその作品のエントリがないか、あっても
    他のサイトへのリンクになっていると失敗する。
    そうでなくても失敗するかもしれない(一覧ページに追加して間もなく、検索でまだ
    ヒットしないなど)。
    検索してヒットしなかったらDMM上のものをそのまま設定する。

    ■レンタル先行レーベルでの自動切り替え
    レンタル版が先行する作品もあるレーベルなのにレンタル以外のサービスのURLが
    与えられた場合、レンタル版をチェックし、リリースが早ければレンタル版の情報で
    ウィキテキストを作成、備考としてセル版へのリンクを追加する。
    --disable-check-rental オプションが与えられるとレンタル版をチェックしない。
    登録してあるレンタル先行レーベルは以下の通り:
'''
RENTAL_PRECEDES = {
    '51':    'God',
    '419':   'MANIAC（クリスタル）',
    '664':   'LEO',
    '3548':  'ATHENA',
    '6172':  'アートビデオSM/妄想族',
    '4285':  'FAプロ',
    '21383': 'FAプロ 熟女',
    '21405': 'FAプロ 赤羽',
    '22815': 'Fプロジェクト',
    '5940':  'ながえSTYLE',
    '23360': 'ナックル（ながえスタイル）',
    '23474': 'ナックル（サイドビー）',
    '23768': 'CINEMA（シネマ）',
}

''' ■取得した情報のキャッシュ
    採取したページ内容やリダイレクト情報などは、OSのテンポラリディレクトリ
    (C:\TEMPや/tmpなど)にディレクトリ 'dmm2ssw_cache' を作成し、そこに
    キャッシュする。
    一度キャッシュしたページはWikiなら2時間、それ以外のサイトなら24時間それを
    利用する(キャッシュされないページもある)。
    キャッシュを消したい場合はディレクトリごと直接削除するか -c オプションを
    指定する。
    --recheck オプションを指定すると「ページがない」およびリダイレクトページと
    キャッシュされているページを再チェックする。
    キャッシュディレクトリがどこにあるかは --cache-info オプションで確認できる。


動作条件:
    [必須] python3.4以降, httplib2(python3用), lxml(python3用)
    [必須] libssw.py  このスクリプトと同じ場所、またはPYTHONPATHが通っている
    ところへおいておく。


注意:
    このスクリプトを連続実行させて短時間に大量の情報を取得した場合、
    その間隔が短いと(D)DoS攻撃とみなされて通報されるかもしれないので注意。


引数:
DMM作品ページのURL
    省略時は標準入力から読み込む。


オプション:

-a, --actress 出演者 [出演者 ...]
    クレジットされてない出演者を追加する場合用。
    出演者(のwikiページ名)を指定する。
    女優名がリダイレクトページならwiki同様 "表示名>ページ名" と指定する。
    DMMページ上にすでに出演者情報が存在する場合はそれに含まれなかったものが末尾に
    追加される。
    ここに"("または"（"で始まる文字列(例: (1人目)、(M・Sさん) など)を指定すると
    内部リンクにしない。
    "女優A,女優B／(3人目)" というようにスラッシュやカンマなどで区切って渡すのも可
    (ただし出力では区切り文字はすべて"／"になる)。
    女優名ページ用ウィキテキストの場合、-n 指定も含め2名に満たない場合は出力
    されない。
    出演者文字列の先頭に @@ をつけるとウィキテキストの構文で直接指定したとみなす
    (@@を取り除いてそのままウィキテキストに出力する)。
    ウィキテキストで直接指定時は引数は先頭の1個だけ取られ、2個目以降は無視される。

-n, --number 出演者数
    未知の出演者がいる場合用。
    出演者の総数を指定する。
    指定されると出演者の最後に「… ほか計n名」を追加する。
    正数を与えても既知の出演者数以下の場合は無視される。
    -1 を指定すると「… ほか」と人数を明記しない曖昧表示になる。
    -a をウィキテキストで直接指定したときは無視される。

-s, --series [シリーズ一覧ページ名]
    シリーズ一覧ページへのリンクを追加する場合用。
    DMM上でのシリーズとwikiでのシリーズの扱いが異なる時にwikiページ名を指定する
    一覧ページ名を指定しないとDMMページから取得する。
    指定されるとDMMページ上のものを置き換える。

-l, --label [レーベル一覧ページ名]
    -s 同様だが、シリーズ一覧ではなくレーベル一覧へのリンクとして追加する。

--linklabel 一覧ページへのリンクのラベル名
    作品一覧ページへのリンクに表示するラベル(「レーベル一覧」「シリーズ一覧」など)を
    ここで指定した文字列に置き換える。

--hide-list
     一覧ページへのリンクを追加しない。

-t, --table
    シリーズ/レーベル一覧ページ用の表形式のウィキテキストを出力する。
    2個以上指定すると女優ページ用と両方出力する。

--pid 品番
    作品の品番を直接指定する。
    -t/-tt オプションが与えられた時用。

    ※指定しない場合
    DMM上の品番情報(cid=)から自動生成を試みる。
    正規表現にマッチした場合置き換えられ、すべて大文字化される。
    正しい品番にならない場合があるので注意。
    マッチしなかったら変更せずそのまま出力する。

    自動生成パターン(python正規表現)と置換文字列:

    '^(?:[hn]_)?\d*([a-z]+)(\d+).*', '\1-\2'

    1hunt569     ⇒ HUNT-569
    41hrdv01212r ⇒ HRDV-01212
    h_093crc035  ⇒ CRC-035

    ※以下の場合は個別に対応して正しく生成する:
    ・チェリーズの一部レーベル
        h_093r18243 ⇒ R18-243
    ・LEOのレンタル版
        125ud537ra  ⇒ UD537R
    ・FAプロのレンタル版の一部
        h_066fad1976r ⇒ FAD1976
        h_066rhtr013r ⇒ RHTR013
    ・TMAの一部
        55t28349 ⇒ T28-349
        55id22036 ⇒ 22ID-036
    ・AROMAの一部作品(過去の同一品番との衝突回避)
        11arm0374 ⇒ ARM-374
    ・ドグマの D1 CLIMAX レーベル
        d1001 ⇒ D1-001
    ・ドグマの AD1 CLIMAX レーベル
        ad1001 ⇒ AD1-001
    ・青空ソフト
        h_308aoz200z ⇒ AOZ-200Z
    ・ながえスタイルのセル版の一部
        h_102bnsps001 ⇒ NSPS-001
    ・アウダースの一部
        21psd001 ⇒ PSD+001
    ・D1グランプリ
        36d1clymax00004 ⇒ D1CLYMAX-004

--subtitle 副題
    -t/-tt オプションが与えられた時用。
    作品名の副題(SUBTITLEカラムに出力される)に指定された副題を出力する。

--as-series
    -t/-tt オプションが与えられた時用。
    シリーズ一覧用にタイトルではなく副題を出力する。

--note 備考 [備考 ...]
    女優ページ形式ではウィキテキストの最後、一覧ページ形式では右端の「NOTE」
    カラムに指定された文字列を出力する。
    データは固定の文字列と以下の変数を指定できる。
    これら変数はウィキテキスト作成時に対応する文字列に展開される。
    @{media}  メディアの種類
    @{time}   収録時間
    @{series} シリーズ名
    @{maker}  メーカー名
    @{label}  レーベル名
    @{cid}    品番

-d, --add-dir-col
    DIRECTORカラムを出力する。
    -t/-tt オプションが与えられた時用。

--add-column [カラム名[:データ] [カラム名[:データ] ...]]
    表形式に任意のカラムを追加する。
    -t/-tt を指定しない場合は無視される。
    書式はカラム名のあとに :とともに各カラム内に出力するデータを指定できる。
    データの書式は --note オプションと同じ。

--join-tsv ファイル [ファイル ...] (TSV)
    DMMから得た作品と(URLが)同じ作品がファイル内にあった場合、DMMからは取得できなかった
    情報がファイル側にあればそれで補完する(NOTEも含む)。
    ファイル形式については「インポートファイル形式」参照。

--join-wiki ウィキテキスト [ウィキテキスト ...] (一覧ページの表形式)
    DMMから得た作品と(URLが)同じ作品がウィキテキスト内にあった場合、DMMからは取得
    できなかった情報がウィキテキスト側にあればそれで補完する(NOTEも含む)。
    セルが結合されている表には未対応。

--join-html Wiki一覧ページのURL/HTML [Wiki一覧ページのURL/HTML ...] (一覧ページのHTML)
    DMMから得た作品と(URLが)同じ作品が、Wikiの一覧ページにあった場合、DMMからは取得
    できなかった情報がWiki側にあればそれで補完する(NOTEも含む)。
    一覧ページを保存したHTMLのファイルでも可。
    セルが結合されている表には未対応。

-f, --disable-follow-redirect
    指定・取得した出演者名のwikiページがリダイレクトページかどうかチェック
    しない。

--disable-check-smm
    DMMの作品ページ上に出演者名がない場合にSMMの作品ページに無いかチェック
    しない。

--disable-check-rental
    レンタル先行レーベルなのにレンタル以外のサービスの作品URLだった場合に
    レンタル版の方をチェックしない。

--disable-check-bluray
    入力されたURLがBlu-ray版だったときにDVD版の有無をチェックしない。

--disable-check-listpage
    Wiki上の実際の一覧ページをチェックせず、オプションで与えられたものか
    DMMのものをそのまま採用する。

--recheck
    「ページが見つからない」とキャッシュされているページを再チェックする。

--disable-modify-title
    タイトルの自動修正を無効にする(「説明」参照)。

--disable-strip-oldname
    出演者の旧名の自動除去を無効にする(「説明」参照)。

--fastest
    処理時間に影響する(ウェブページにアクセスする)あらゆる補助処理を行わない。

-b, --browser
    ウィキテキスト作成後、Wikiの女優、シリーズ一覧、あるいはレーベル一覧の
    ページをウェブブラウザで開く。

-c, --clear-cache
    キャッシュを終了時に削除する(「説明」参照)。

--cache-info
    キャッシュのパスとファイルサイズの合計を出力して終了する。

-v, --verbose
    デバッグ用情報を出力する。

-V, --version
    バージョン情報を表示して終了する。

-h, --help
    ヘルプメッセージを表示して終了する。


使用例:
 作品 http://www.dmm.co.jp/mono/dvd/-/detail/=/cid=h_635sw251/ のウィキテキストを作成する場合:

 1) 女優ページ用ウィキテキストを作成する場合。

    dmm2ssw.py "http://www.dmm.co.jp/mono/dvd/-/detail/=/cid=84scop225/"

 2) レーベル一覧ページ用(表形式)ウィキテキストを作成する場合。

    dmm2ssw.py "http://www.dmm.co.jp/mono/dvd/-/detail/=/cid=84scop225/" -t

 3) 出演者が「波多野結衣」だけ確認でき、出演者数は計3名だとわかった場合。

    dmm2ssw.py "http://www.dmm.co.jp/mono/dvd/-/detail/=/cid=84scop225/" -a "波多野結衣" -n 3

 4) 出演者全員が確認でき、女優ページ用とレーベル一覧ページ用両方のウィキテキストを作成し、作成したら各Wikiページをウェブブラウザで開く場合。

    dmm2ssw.py "http://www.dmm.co.jp/mono/dvd/-/detail/=/cid=84scop225/" -ttb -a "波多野結衣" "羽川るな" "椿かなり"

'''
import sys as _sys
import re as _re
import argparse as _argparse
import urllib.parse as _up
import unicodedata as _unicodedata
from itertools import chain as _chain
from copy import deepcopy as _deepcopy
from collections import namedtuple as _namedtuple
import libssw as _libssw

__version__ = 20150512

VERBOSE = 0

AUTOMODIFY = True
AUTOSTRIP = True

OWNNAME = _libssw.ownname(__file__)
verbose = _libssw.Verbose(OWNNAME, VERBOSE)
emsg = _libssw.Emsg(OWNNAME)

BASEURL = _libssw.BASEURL
BASEURL_SMM = _libssw.BASEURL_SMM
BASEURL_SSW = _libssw.BASEURL_SSW

REDIRECTS = _libssw.REDIRECTS

ReturnVal = _namedtuple('ReturnVal',
                        ('release', 'pid', 'title', 'title_dmm', 'url',
                         'maker', 'label', 'series', 'wktxt_a', 'wktxt_t'))

p_more = _re.compile(r"url: '(.*?)'")
p_related = _re.compile(r'var url = "(.*)"')
p_genre = _re.compile(r'/article=keyword/id=(\d+)/')
# p_genre = _re.compile(r'/article=keyword/id=(6003|6147|6561)/')
p_age = _re.compile(r'(\(\d+?\))$')

sp_heart = (_re.compile(r'（ハート）|◆'), r'♥')
sp_ltbracket_h = (_re.compile(r'^(?:【.+?】)+?'), '')
sp_ltbracket_t = (_re.compile(r'(?:【.+?】)+?$'), '')
# sp_href = (_re.compile(r'href=(/.*/)>'), r'href="\1">')
sp_nowrdchr = (_re.compile(r'\W'), '')
sp_pid = None  # dmmsar.py 側から更新

sp_expansion = ((_re.compile('@{media}'), 'media'),
                (_re.compile('@{time}'), 'time'),
                (_re.compile('@{series}'), 'series'),
                (_re.compile('@{maker}'), 'maker'),
                (_re.compile('@{label}'), 'label'),
                (_re.compile('@{cid}'), 'cid'))


IMG_URL = {'dvd':    'http://pics.dmm.co.jp/mono/movie/adult/',
           'rental': 'http://pics.dmm.co.jp/mono/movie/',
           'video':  'http://pics.dmm.co.jp/digital/video/',
           'ama':    'http://pics.dmm.co.jp/digital/amateur/'}

# 除外対象ジャンル
OMITGENRE = {'6014': 'イメージビデオ',
             '6003': '総集編',       # ベスト・総集編
             '6608': '総集編',       # 女優ベスト・総集編
             '7407': '総集編',       # ベスト・総集編
             '6147': 'アウトレット',
             '6175': 'アウトレット',  # '激安アウトレット'
             '4104': 'UMD',
             }
#  '6561': '限定盤'} # 特典対象

# 総集編・再収録専門なのに作品にそうジャンル付けされないやつ
# メーカー
OMIT_MAKER = {'6500': 'BACK DROP', }
#             '45810': 'エクストラ'}
OMIT_MAKER_SUSS = {'5665': 'ROOKIE', }

# レーベル
OMIT_LABEL = {'6010':  'ALL IN☆ ONE',
              '9164':  'オーロラプロジェクト・EX',
              '21231': 'DRAGON（ハヤブサ）',
              '24230': '美少女（プレステージ）'}
# シリーズ
OMIT_SERIES = {
    '2935':   'BEST（作品集）',
    '9939':   'プレミアムベスト',
    '9696':   'ism',
    '77766':  '人妻の情事（なでしこ）',
    '202979': '『無垢』特選 無垢ナ女子校生限定ソープランド 大好評記念感謝祭',
    '204625': 'いいなりな人妻たち',
    '205518': 'いやらしくてムッチリお尻で巨乳の人妻とHがしたい',
    '205779': 'フェラチオSP',
    '207233': '寸止め焦らしで大暴発スペシャル',
    '208033': '湯あがりぺちゃぱいバスタイム',
    '208077': '美熟女プレイ集',
    '208374': '催眠研究',
    '209310': 'ONEDAFULL1年の軌跡全60作品',
    '209360': '○○ism',
    '209413': 'アウトレットDVD5枚組 1980',
    '209887': '奥さんの体がエロいから犯されるんです！！！',
    '210208': 'ママ友！増刊号 ヤリ友の輪',
    '210925': '淫乱すぎる若妻48人の連続ドスケベSEX',
    '210926': 'どすけべ妻のいやらしいフェラチオ',
    '211184': 'The○○ 美熟女スペシャル',
    '211414': '母乳厳選集',
    '213087': 'おませなJKの制服でオクチえっち！',
    '213420': 'キレイなお姉さんのパンモロ○○コレクション',
    '213840': '癒しのじゅるじゅぽフェラCOLLECTION',
}

# シリーズとして扱うとめんどくさいシリーズ
IGNORE_SERIES = {'8369': 'E-BODY',
                 '205878': 'S級素人'}

# レンタル版のページの出演者が欠けていることがあるメーカー
FORCE_CHK_SALE_MK = {'40121': 'LEO'}
# レンタル版のページの出演者が欠けていることがあるシリーズ
FORCE_CHK_SALE_SR = {'79592': '熟ズボッ！',
                     '3820':  'おはズボッ！'}

GENRE_BD = '6104'  # Blu-rayのジャンルID


class OmitTitleException(Exception):
    '''総集編など除外タイトル例外'''
    def __init__(self, key, word=''):
        self.key = key
        self.word = word

    def __str__(self):
        return repr(self.word)


def _get_args(argv, p_args):
    '''
    コマンドライン引数の解釈
    '''
    global VERBOSE
    global AUTOMODIFY
    global AUTOSTRIP

    argparser = _argparse.ArgumentParser(
        description='DMMのURLから素人系総合wiki用ウィキテキストを作成する')
    argparser.add_argument('url',
                           help='DMMの作品ページのURL',
                           nargs='?',
                           metavar='URL')

    argparser.add_argument('-a', '--actress',
                           help='出演者 (DMMページ内のものに追加する)',
                           nargs='+',
                           default=[])
    argparser.add_argument('-n', '--number',
                           help='未知の出演者がいる場合の総出演者数 (… ほか計NUMBER名)',
                           type=int,
                           default=0)

    list_page = argparser.add_mutually_exclusive_group()
    list_page.add_argument('-s', '--series',
                           help='シリーズ一覧へのリンクを追加(DMM上のものを置き換え)',
                           default=getattr(p_args, 'series', None))
    list_page.add_argument('-l', '--label',
                           help='レーベル一覧へのリンクを追加(DMM上のものを置き換え)',
                           default=getattr(p_args, 'label', None))
    list_page.add_argument('--hide-list',
                           help='一覧ページへのリンクを追加しない',
                           action='store_true',
                           default=getattr(p_args, 'hide_list', False))

    argparser.add_argument('--linklabel',
                           help='一覧ページへのリンクの表示名を置き換える',
                           default=getattr(p_args, 'linklabel', None))

    argparser.add_argument('-t', '--table',
                           help='一覧ページ用の表形式ウィキテキストを作成する, 2個以上指定すると両方作成する',
                           action='count',
                           default=getattr(p_args, 'table', 0))

    argparser.add_argument('--pid',
                           help='作品の品番を直接指定(-t/-tt 指定時用)')

    argparser.add_argument('--subtitle',
                           help='タイトルの副題を直接指定(-t/-tt 指定時用)')
    argparser.add_argument('--as-series',
                           help='タイトルではなく副題で作成(-t/-tt 指定時用)',
                           action='store_true')

    argparser.add_argument('--note',
                           help='備考(表形式ではNOTEカラム)として出力する文字列',
                           nargs='+',
                           metavar='DATA',
                           default=getattr(p_args, 'note', []))
    argparser.add_argument('-d', '--add-dir-col',
                           help='DIRECTORカラムを出力する (-t/-tt 指定時用)',
                           dest='dir_col',
                           action='store_true',
                           default=getattr(p_args, 'dir_col', False))
    argparser.add_argument('--add-column',
                           help='表形式ヘッダに任意のカラムを追加する (-t/-tt 指定時のみ)',
                           nargs='+',
                           metavar='COLUMN:DATA',
                           default=getattr(p_args, 'add_column', []))

    # 外部からデータ補完
    argparser.add_argument('--join-tsv',
                           help='テキストファイル(TSV)でデータを補完する',
                           nargs='+',
                           metavar='FILE')
    argparser.add_argument('--join-wiki',
                           help='素人系総合Wikiのウィキテキスト(表形式)でデータを補完する',
                           nargs='+',
                           metavar='FILE')
    argparser.add_argument('--join-html',
                           help='素人系総合Wikiの一覧ページを読み込んで補完する',
                           nargs='+',
                           metavar='URL/HTML')

    argparser.add_argument('-f', '--disable-follow-redirect',
                           help='ページのリダイレクト先をチェックしない',
                           dest='follow_rdr',
                           action='store_false',
                           default=getattr(p_args, 'follow_rdr', True))
    argparser.add_argument('--disable-check-smm',
                           help='出演者情報がなかったときにSMMを検索しない',
                           dest='smm',
                           action='store_false',
                           default=getattr(p_args, 'smm', True))
    argparser.add_argument('--disable-check-rental',
                           help='レンタル先行レーベルでもレンタル版のリリースをチェックしない',
                           dest='check_rental',
                           action='store_false',
                           default=getattr(p_args, 'check_rental', True))
    argparser.add_argument('--disable-check-related',
                           help='レンタル版のときの他メディアの情報収集を行わない',
                           dest='check_rltd',
                           action='store_false',
                           default=getattr(p_args, 'check_rltd', True))
    argparser.add_argument('--disable-check-listpage',
                           help='Wiki上の実際の一覧ページを探さない',
                           dest='check_listpage',
                           action='store_false',
                           default=getattr(p_args, 'check_listpage', True))
    argparser.add_argument('--disable-longtitle',
                           help='アパッチ、SCOOPの長いタイトルを補足しない',
                           dest='longtitle',
                           action='store_false',
                           default=getattr(p_args, 'longtitle', True))
    argparser.add_argument('--fastest',
                           help='ウェブにアクセスするあらゆる補助処理を行わない',
                           action='store_true',
                           default=getattr(p_args, 'fastest', False))

    argparser.add_argument('--recheck',
                           help='キャッシュしているリダイレクト先を強制再チェック',
                           action='store_true',
                           default=getattr(p_args, 'recheck', False))

    argparser.add_argument('--disable-modify-title',
                           help='タイトルの自動調整を無効にする',
                           action='store_false',
                           default=True)
    argparser.add_argument('--disable-strip-oldname',
                           help='出演者の旧芸名の自動除去を無効にする',
                           action='store_false',
                           default=True)

    argparser.add_argument('-b', '--browser',
                           help='生成後、wikiのページをウェブブラウザで開く',
                           action='store_true')

    argparser.add_argument('-c', '--clear-cache',
                           help='プログラム終了時にキャッシュをクリアする',
                           action='store_true',
                           default=False)
    argparser.add_argument('--cache-info',
                           help='キャッシュのパスとファイルサイズの合計を出力して終了する',
                           action='store_true')
    argparser.add_argument('-v', '--verbose',
                           help='デバッグ用情報を出力する',
                           action='count',
                           default=0)
    argparser.add_argument('-V', '--version',
                           help='バージョン情報を表示して終了する',
                           action='version',
                           version='%(prog)s {}'.format(__version__))

    args = argparser.parse_args(argv)

    # dmmsar.py 側からVERBOSEが変更される場合があるため
    verbose.verbose = VERBOSE = VERBOSE or args.verbose
    if args.verbose > 1:
        _libssw.VERBOSE = _libssw.verbose.verbose = args.verbose - 1
    verbose('verbose mode on')

    if args.cache_info:
        size = sum(
            f.stat().st_size for f in _libssw.CACHEDIR.glob('*')) / 1048576
        emsg('I', 'キャッシュパス: ', _libssw.CACHEDIR)
        emsg('I', 'サイズ: {:.2f}MB'.format(size))
        raise SystemExit

    if args.fastest:
        for a in ('follow_rdr', 'smm', 'check_rental', 'check_listpage',
                  'check_rltd', 'longtitle'):
            setattr(args, a, False)

    AUTOMODIFY = args.disable_modify_title
    AUTOSTRIP = args.disable_strip_oldname
    _libssw.RECHECK = args.recheck

    verbose('args: ', args)
    return args


def _build_image_url(service, cid):
    '''
    画像URL作成
    '''
    verbose('force building image url')
    suffix = ('js', 'jp') if service == 'ama' else ('ps', 'pl')
    return tuple(_up.urljoin(IMG_URL[service], '{0}/{0}{1}.jpg'.format(cid, s))
                 for s in suffix)


def _normalize(string):
    '''
    タイトルから【.+?】と非unicode単語文字を除いて正規化
    '''
    string = _unicodedata.normalize('NFKC', string).replace(' ', '')
    string = _libssw.sub(sp_ltbracket_h, string)
    string = _libssw.sub(sp_ltbracket_t, string)
    string = _libssw.sub(sp_nowrdchr, string)
    return string


class LongTitleException(Exception):
    pass


def _ret_apache(cid, pid):
    '''Apacheのタイトルの長いやつ'''
    verbose('Checking Apache title...')

    number = cid.replace('h_701ap', '')
    url = 'http://www.apa-av.jp/list_detail/detail_{}.html'.format(number)

    resp, he = _libssw.open_url(url)

    if resp.status != 200:
        emsg('W', 'ページを開けませんでした: url={}, status={}'.format(
            url, resp.status))
        raise LongTitleException

    opid, actress, director = _libssw.ret_apacheinfo(he)

    if pid != opid:
        verbose('check_apache: PID on Apache official is different fro DMM')
        raise LongTitleException(pid, opid)

    return he.head.find('title').text.strip().replace('\n', ' ')


class _RetrieveTitleSCOOP:
    '''SCOOPのタイトルの長いやつ'''
    def __init__(self):
        self.cookie = _libssw.load_cache('kmp_cookie', expire=86400)

    def __call__(self, cid, pid):
        verbose('Checking SCOOP title...')

        prefix = cid[2:6]
        number = cid[6:]
        url = 'http://www.km-produce.com/works/{}-{}'.format(prefix, number)

        while True:
            verbose('cookie: ', self.cookie)
            resp, he = _libssw.open_url(url, set_cookie=self.cookie)
            if 'set-cookie' in resp:
                self.cookie = resp['set-cookie']
                verbose('set cookie')
                _libssw.save_cache(self.cookie, 'kmp_cookie')
            else:
                break

        if resp.status != 200:
            emsg('W', 'ページを開けませんでした: url={}, status={}'.format(
                url, resp.status))
            raise LongTitleException

        return he.find_class('title')[0].text.strip()

_ret_scoop = _RetrieveTitleSCOOP()


class _RetrieveTitlePlum:
    '''プラムのタイトル'''
    def __init__(self, prefix):
        self.prefix = prefix
        self.ssid = None
        self.cart = None

    def _parse_cookie(self, cookie):
        verbose('parse cookie: ', cookie)
        for c in (i.split(';')[0].strip() for i in cookie.split(',')):
            if '=' not in c:
                continue
            lhs, rhs = c.split('=')
            if rhs == 'deleted':
                self.ssid = lhs
            elif lhs == 'cart_pDq7k':
                self.cart = rhs

        if self.ssid and self.cart:
            return 'AJCSSESSID={}; cart_pDq7k={}; enter=enter'.format(
                self.ssid, self.cart)

    def __call__(self, cid, pid):
        verbose('Checking Plum title...')

        number = cid.replace(self.prefix, '')
        if len(number) < 3:
            number = '{:0>3}'.format(number)
        url = 'http://www.plum-web.com/?view=detail&ItemCD=SE{}&label=SE'.format(number)

        cookie = ''
        for i in range(5):
            cookie = self._parse_cookie(cookie)
            verbose('plum cookie: ', cookie)

            resp, he = _libssw.open_url(url, set_cookie=cookie, cache=False)

            cookie = self._parse_cookie(resp.get('set-cookie', cookie))

            if resp.status != 200:
                emsg('W', 'ページを開けませんでした: url={}, status={}'.format(
                    url, resp.status))
                raise LongTitleException

            if not len(he.get_element_by_id('nav', '')):
                break

        else:
            emsg('E', 'プラム公式サイトをうまく開けませんでした。')

        title = he.find('.//h2[@id="itemtitle"]').text.strip()
        title = _libssw.sub(sp_ltbracket_h, title)

        return title

# _ret_plum_se = _RetrieveTitlePlum('h_113se')


TITLE_FROM_OFFICIAL = {'h_701ap': _ret_apache,    # アパッチ
                       '84scop': _ret_scoop,      # SCOOP
                       '84scpx': _ret_scoop,      # SCOOP
                       # 'h_113se': _ret_plum_se, # 素人援交生中出し(プラム)
                       }


def _compare_title(cand, title):
    '''
    同じタイトルかどうか比較
    title はあらかじめ _normalize() に通しておくこと
    '''
    cand = _normalize(cand.strip())
    verbose('cand norm: ', cand)
    return cand.startswith(title) or title.startswith(cand)


class __TrySMM:
    '''
    SMMから出演者情報を得てみる

    SMM通販新品から「品番 + タイトルの先頭50文字」で検索、ヒットした作品のページの
    「この作品に出演している女優」を見る

    返り値:
    女優情報があった場合はその人名のリスト、なければ空のタプル
    '''
    # 1年以内にリリース実績のある実在するひらがなのみ(4文字以下)の名前 (2015-07-05現在)
    _allhiraganas = ('あいり', 'あづみ', 'あゆか', 'ありさ', 'くるみ',
                     'ここあ', 'さな', 'さやか', 'しずく', 'すみれ', 'つくし',
                     'つばさ', 'つぼみ', 'なおみ', 'なごみ', 'なつみ',
                     'ののか', 'ひかる', 'まりか', 'みはる', 'めぐり',
                     'もえり', 'ももか', 'ゆいの', 'ゆう', 'ゆうゆう', 'りん',
                     'りんか', 'れんか')

    def __init__(self):
        self.title_smm = ''
        # self._cookie = _libssw.get_cookie()
        self._cookie = 'afsmm=10163915; TONOSAMA_BATTA=0bf596e86b6853db3b7cc52cdd4ff239; ses_age=18'

    def _is_existent(self, name):
        '''その名前の女優が実際にいるかどうかDMM上でチェック'''
        verbose('is existent: ', name)
        url = '{}/-/search/=/searchstr={}/'.format(_libssw.BASEURL_ACT,
                                                   _up.quote(name))
        while True:
            resp, he = _libssw.open_url(url)
            for a in he.iterfind('.//tr[@class="list"]'):
                cand = a.find('td[2]/a').text.strip()
                if name == cand:
                    return True

            pagin = he.find('.//td[@class="line"]/a[last()]')
            if pagin is not None and pagin.text == '次へ':
                url = _libssw.BASEURL_ACT + pagin.get('href')
            else:
                break

    def _chk_anonym(self, pfmr):
        '''SMM出演者情報でひらがなのみの名前の場合代用名かどうかチェック
        名前がひらがなのみで5文字未満で既知のひらがな女優名でなければ仮名とみなす'''
        # if _libssw.p_neghirag.search(pfmr) or self._is_existent(pfmr):
        if _libssw.p_neghirag.search(pfmr) or \
           len(pfmr) > 4 or \
           pfmr in self._allhiraganas:
            return (pfmr, '', '')
        else:
            return ('', '', '({})'.format(pfmr))

    def __call__(self, pid, title):
        verbose('Trying SMM...')
        # SMMで検索(品番+タイトル)
        if not self._cookie:
            verbose('could not retrieve cookie')
            return ()

        search_url = '{}/search/image/-_-/cate/20/word/{}'.format(
            BASEURL_SMM, _up.quote('{} {}'.format(pid, title[:50])))

        resp, he_search = _libssw.open_url(search_url, set_cookie=self._cookie)

        if resp.status != 200:
            verbose('smm search failed: url={}, status={}'.format(
                search_url, resp.status))
            return ()

        # SMM上で年齢認証済みかどうかの確認
        confirm = he_search.get_element_by_id('confirm', None)

        if confirm is not None:
            emsg('W', 'SMMの年齢認証が完了していません。')
            self._cookie = False
            return ()

        # 検索結果のタイトルは <img alt= から取得
        items = he_search.find_class('imgbox')

        if not len(items):
            verbose('smm: No search result')
            return ()

        # DMM、SMM各タイトルを正規化して比較、一致したらそのページを読み込んで
        # 出演者情報を取得
        title = _normalize(title)
        verbose('title norm: ', title)

        for item in items:
            path = item.find('a').get('href')
            self.title_smm = item.find('a/img').get('alt')

            # タイトルが一致しなければ次へ
            if not _compare_title(self.title_smm, title):
                verbose('title unmatched')
                continue

            # 作品ページを読み込んで出演者を取得
            prod_url = _up.urljoin(BASEURL_SMM, path)
            verbose('smm: prod_url: ', prod_url)

            resp, he_prod = _libssw.open_url(
                prod_url, set_cookie=self._cookie)

            pid_smm = he_prod.find(
                './/div[@class="detailline"]/dl/dd[7]').text.strip()
            if pid != pid_smm:
                verbose('pid unmatched')
                continue

            smmpfmrs = he_prod.xpath('//li[@id="all_cast_li"]/a/text()')
            verbose('smmpfmrs: ', smmpfmrs)

            smmpfmrs = [self._chk_anonym(p) for p in smmpfmrs]
            verbose('chk anonym: ', smmpfmrs)

            return smmpfmrs[:]

            break

        else:
            verbose('all titles are mismatched')
            return ()

_try_smm = __TrySMM()


class DMMParser:
    '''
    DMM作品ページの解析
    '''
    def __init__(self, no_omits=_libssw.OMITTYPE,
                 start_date=None, start_pid_s=None, filter_pid_s=None,
                 pass_bd=False, n_i_s=False, deeper=True, quiet=False):
        self._sm = _libssw.Summary()
        self.deeper = deeper
        self.quiet = quiet
        self.no_omits = no_omits
        self.start_date = start_date
        self.start_pid_s = start_pid_s and _libssw.split_pid(start_pid_s)
        self.filter_pid_s = filter_pid_s
        self.pass_bd = pass_bd
        self.n_i_s = n_i_s

    def _mark_omitted(self, key, hue):
        '''除外タイトルの扱い'''
        if key in self.no_omits:
            # 除外対称外なら備考に記録
            if not any(key in s for s in self._sm['note']):
                self._sm['note'].append(key)
        else:
            # 除外対象なら処理中止
            verbose('Omit exception ({}, {})'.format(key, hue))
            raise OmitTitleException(key, hue)

    def _ret_title(self, chk_longtitle):
        '''タイトルの採取'''
        def _det_longtitle_maker():
            for key in TITLE_FROM_OFFICIAL:
                if self._sm['cid'].startswith(key):
                    verbose('title from maker: ', key)
                    return TITLE_FROM_OFFICIAL[key]

        tdmm = self._he.find('.//img[@class="tdmm"]').get('alt')
        verbose('title dmm: ', tdmm)

        tmkr = ''
        if chk_longtitle:
            titleparser = _det_longtitle_maker()
            if titleparser:
                # Apacheの作品タイトルはメーカー公式から
                try:
                    tmkr = titleparser(self._sm['cid'], self._sm['pid'])
                except LongTitleException as e:
                    emsg('W',
                         'メーカー公式サイトから正しい作品ページを取得できませんでした: ',
                         e.args)
        verbose('title maker: ', tmkr)

        title = tmkr or tdmm
        title_dmm = tdmm if not _normalize(title).startswith(_normalize(tdmm)) \
                    else ''

        if __name__ == '__main__' and self.deeper:
            # 除外チェック
            for key, word in _libssw.check_omitword(title):
                self._mark_omitted(key, word)

        return title, title_dmm

    def _ret_props(self, prop):
        '''各種情報'''

        tag = prop.text.strip()

        if tag == '種類：':

            self._sm['media'] = _libssw.rm_nlcode(_libssw.getnext_text(prop))

            verbose('media: ', self._sm['media'])

        elif tag in ('発売日：', '貸出開始日：', '配信開始日：'):

            if self.start_date and data.replace('/', '') < self.start_date:
                raise OmitTitleException('release', 'date')

            self._sm['release'] = _libssw.rm_nlcode(_libssw.getnext_text(prop))

            verbose('release: ', self._sm['release'])

        elif tag == '収録時間：':

            self._sm['time'] = _libssw.rm_nlcode(_libssw.getnext_text(prop))

            verbose('time: ', self._sm['time'])

        elif tag == 'メーカー：':

            mk = prop.getnext().find('a')

            try:
                self._sm['maker_id'] = mkid = _libssw.get_id(mk.get('href'))[0]
            except AttributeError:
                return

            if not self._sm['maker']:
                self._sm['maker'] = _libssw.getnext_text(prop, 'a')[0]

            # ジュエル系なら出演者情報は無視
            if mkid in IGNORE_PERFORMERS:
                self.ignore_pfmrs = True
                verbose('Jewel family found')

            # 総集編メーカーチェック
            if mkid in OMIT_MAKER:
                self._mark_omitted('総集編', OMIT_MAKER[mkid])

            # 総集編容疑メーカー
            if mkid in OMIT_MAKER_SUSS:
                self.omit_suss = OMIT_MAKER_SUSS[mkid]

            # 他のサービスを強制チェック
            if mkid in FORCE_CHK_SALE_MK:
                verbose('series forece chk other: ', FORCE_CHK_SALE_MK[mkid])
                self.force_chk_sale = True

            verbose('maker: ', self._sm['maker'])

        elif tag == 'レーベル：':

            lb = prop.getnext().find('a')

            try:
                lbid = _libssw.get_id(lb.get('href'))[0]
            except AttributeError:
                return

            self._sm['label'] = lb.text

            # 隠れ総集編レーベルチェック
            if lbid in OMIT_LABEL:
                self._mark_omitted('総集編', OMIT_LABEL[lbid])

            # レンタル先行レーベルチェック
            if lbid in RENTAL_PRECEDES:
                self.rental_pcdr = True

            self._sm['label_id'] = lbid

            verbose('label: ', self._sm['label'])

        elif tag == 'シリーズ：':

            sr = prop.getnext().find('a')

            if sr is None:
                return

            srid = _libssw.get_id(sr.get('href'))[0]

            if self.n_i_s:
                verbose('not in series')
                raise OmitTitleException('series', (srid, sr.text))

            # 隠れ総集編シリーズチェック
            if srid in OMIT_SERIES:
                self._mark_omitted('総集編', OMIT_SERIES[srid])

            if srid in IGNORE_SERIES:
                # シリーズとして扱わない処理
                verbose('series hid: ', IGNORE_SERIES[srid])
                self._sm['series'] = '__HIDE__'
            else:
                self._sm['series'] = _libssw.getnext_text(prop, 'a')[0]

            # 独自ページ個別対応
            # ・SOD女子社員
            if self._sm['series'] == 'SOD女子社員':
                self._sm['series'] += 'シリーズ' + self._sm['release'].split('/', 1)[0]

            self._sm['series_id'] = srid

            # 他のサービスを強制チェック
            if srid in FORCE_CHK_SALE_SR:
                verbose('series forece chk other: ',
                        FORCE_CHK_SALE_SR[srid])
                self.force_chk_sale = True

            verbose('series: ', self._sm['series'])

        elif tag == '監督：':
            data = _libssw.getnext_text(prop, 'a')
            if data and not self._sm['director']:
                self._sm['director'] = data

            verbose('director: ', self._sm['director'])

        elif tag == 'ジャンル：':
            for g in prop.getnext():
                verbose('genre: ', g.text)
                try:
                    gid = p_genre.findall(g.get('href'))[0]
                except IndexError:
                    continue

                # 除外対象ジャンルであれば記録または中止
                if OMITGENRE.get(gid, False):
                    self._mark_omitted(OMITGENRE[gid], 'genre')

                if gid == GENRE_BD:
                    self.bluray = True
                    verbose('media: Blu-ray')

                self._sm['genre'].append(g.text)

        elif tag == '品番：':
            data = _libssw.getnext_text(prop)

            # URL上とページ内の品番の相違チェック
            if not self.quiet and \
               self._sm['cid'] and \
               self._sm['cid'] != data.rsplit('so', 1)[0]:
                emsg('I', '品番がURLと異なっています: url={}, page={}'.format(
                    self._sm['cid'], data))

            self._sm['pid'], self._sm['cid'] = _libssw.gen_pid(data, sp_pid)
            verbose('cid: ', self._sm['cid'], ', pid: ', self._sm['pid'])

            # 作成開始品番チェック(厳密)
            if self.start_pid_s:
                prefix, number = _libssw.split_pid(self._sm['pid'])
                if self.start_pid_s[0] == prefix and \
                   self.start_pid_s[1] > number:
                    raise OmitTitleException('pid', self._sm['pid'])

            # filter-pid-sチェック
            if self.filter_pid_s and not self.filter_pid_s.search(
                    self._sm['pid']):
                raise OmitTitleException('pid filtered', self._sm['pid'])

            # 隠れ総集編チェック
            if _libssw.check_omitprfx(data, _libssw.OMNI_PREFIX):
                self._mark_omitted('総集編', data)

            # ROOKIE総集編チェック
            if self.omit_suss:
                hh, mmm = _libssw.is_omnirookie(data, self._sm['title'])
                if hh or mmm:
                    self._mark_omitted('総集編', self.omit_suss)

            # 隠れIVチェック
            if _libssw.check_omitprfx(data, _libssw.IV_PREFIX):
                self._mark_omitted('イメージビデオ', data)

        # 動画用
        elif tag == '名前：':
            # 素人動画のタイトルは後でページタイトルと年齢をくっつける
            try:
                age = p_age.findall(_libssw.getnext_text(prop))[0]
            except IndexError:
                age = ''
            self._sm['subtitle'] = age
            verbose('ama subtitle(age): ', self._sm['subtitle'])

        elif tag == 'サイズ：':
            self._sm['size'] = _libssw.getnext_text(prop)
            verbose('ama size: ', self._sm['size'])

    def _ret_images(self, service):
        '''パッケージ画像のURLの取得'''
        if service == 'ama':
            img_lg = self._he.find(
                './/div[@id="sample-video"]/img').get('src')
            img_sm = img_lg.replace('jp.jpg', 'js.jpg')
        else:
            img_a = self._he.find('.//a[@name="package-image"]')
            try:
                img_lg = img_a.get('href')
            except AttributeError:
                img_lg = None
            try:
                img_sm = img_a.find('img').get('src')
            except AttributeError:
                img_sm = None

        return img_lg, img_sm

    def _ret_performers(self, gvnpfmrs, smm):
        '''
        出演者の取得
        (女優名, リダイレクト先, おまけ文字列) のタプルを返すジェネレータ
        '''
        def _trim_name(name):
            '''女優名の調整'''
            name = name.strip()
            if AUTOSTRIP:
                name = _libssw.p_inbracket.split(name)[0]
            return name

        def _list_pfmrs(plist):
            return [(_trim_name(p.strip()), '', '') for p in plist]

        verbose('gvnpfmrs: ', gvnpfmrs)
        verbose('smm: ', smm)

        el = self._he.get_element_by_id('performer', ())

        if len(el):
            if self.omit_suss and len(el) > 3:
                self._mark_omitted('総集編', self.omit_suss)

            if el[-1].get('href') == '#':
                # 「▼すべて表示する」があったときのその先の解析
                verbose('more performers found')
                more_js = el.getparent().find('script')

                if more_js is not None:
                    more_path = p_more.findall(more_js.text)[0]
                else:
                    # 処理スクリプトがHEAD内にある場合(動画ページ)用
                    for scr in self._he.xpath('head/script/text()'):
                        more_path = p_more.findall(scr)
                        if more_path:
                            more_path = more_path[0]
                            break
                    else:
                        emsg('E', '「▼すべて表示する」先が取得できませんでした。')

                more_url = _up.urljoin(BASEURL, more_path)
                resp, he_more = _libssw.open_url(more_url, 'utf-8')
                verbose('more_url opened')

                p_list = _list_pfmrs(he_more.xpath('//a/text()'))

            else:
                p_list = _list_pfmrs(el.xpath('a/text()'))

        elif smm:
            # 出演者情報がなければSMMを見てみる(セル版のときのみ)
            p_list = _try_smm(self._sm['pid'], self._sm['title'])

            if p_list:
                emsg('I', '出演者情報をSMMより補完しました: ', self._sm['pid'])
                emsg('I', 'DMM: ', self._sm['title'])
                emsg('I', 'SMM: ', _try_smm.title_smm)
                emsg('I', '出演者: ', ','.join(p[0] or p[2] for p in p_list))
        else:
            p_list = ()

        pfilter = ''.join(_chain.from_iterable(p_list))

        # DMM/SMMから取得した出演者をyield
        for name in p_list:
            yield name

        # 与えられた出演者情報でDMMに欠けているものをyield
        for gvn in gvnpfmrs:
            verbose('gvn: ', gvn)
            if all(g not in pfilter for g in gvn[:2] if g):
                yield gvn

    def _get_otherslink(self, service, firmly=True):
        '''他のサービスの作品リンクの取得'''
        def _chooselink(others, service):
            for o in others:
                link = o.get('href')
                if service == 'rental' and '/rental/' in link:
                    return link.replace('/ppr', '')
                elif service == 'videoa' and '/digital/videoa/' in link:
                    return link
                elif service == 'dvd' and '/mono/dvd/' in link:
                    return link
            return False

        others = self._he.iterfind('.//ul[@class="others"]/li/a')
        opath = _chooselink(others, service)

        if not opath and firmly:
            # 「他のサービスでこの作品を見る」欄がないときに「他の関連商品を見る」で探してみる
            verbose('link to others not found. checking related item...')
            searstr = self._sm['title'] + '|' + (
                self._sm['series'] if self._sm['series'] else '')

            searlurl = '{}/search/=/searchstr={}/cid={}/{}'.format(
                BASEURL,
                _up.quote(searstr),
                self._sm['cid'],
                'related=1/sort=rankprofile/view=text/')

            resp, he_rel = _libssw.open_url(searlurl)

            title_nr = _normalize(self._sm['title'])
            verbose('title norm: ', title_nr)

            ttl_el = he_rel.iterfind('.//p[@class="ttl"]/a')
            others = (t for t in ttl_el if _compare_title(t.text, title_nr))
            opath = _chooselink(others, service)

        return _up.urljoin(BASEURL, opath) if opath else False

    def _link2other(self, url, tag, release):
        return '※[[{}版>{}]]のリリースは{}。'.format(tag, url, release)

    def _get_otherscontent(self, *service):
        '''他サービス版の情報取得'''
        for s in service:
            others_url = self._get_otherslink(s)
            if others_url:
                break
        else:
            verbose('missing others links')
            return False

        resp, he_others = _libssw.open_url(others_url)

        others_data = _libssw.Summary(self._sm.values())
        others_data['url'] = others_url
        others_data['pid'], others_data['cid'] = _libssw.gen_pid(others_url,
                                                                 sp_pid)

        others_data.update(_othersparser(he_others, service, others_data))
        verbose('others data: ', others_data.items())

        if service == ('rental',):
            # レンタル版のリリースが早ければそれを返す
            if others_data['release'] >= self._sm['release']:
                verbose("rental isn't released earlier")
                return False
            else:
                others_data['others'].append(
                    self._link2other(self._sm['url'],
                                     'セル',
                                     self._sm['release']))
                verbose('rental precedes: ', others_data['note'])

        return _deepcopy(others_data)

    def _check_rltditem(self, media):
        '''
        他メディア(「ご注文前にこちらの商品もチェック！」の欄)があればそれへのリンクを返す
        '''
        verbose('checking {}...'.format(media))
        iterrltd = self._he.iterfind(
            './/div[@id="rltditem"]/ul/li/a/img[@alt="{}"]'.format(media))

        for rlitem in iterrltd:
            rlttl = rlitem.getparent().text_content().strip()
            verbose('rltd ttl: ', rlttl)
            for key, word in _libssw.check_omitword(rlttl):
                # 限定品の除外チェック
                if key not in self.no_omits:
                    break
            else:
                verbose('rltditem: ', rlitem.getparent().get('href'))
                return _up.urljoin(BASEURL, rlitem.getparent().get('href'))

    def __call__(self, he, service, sm=_libssw.Summary(),
                 args=_argparse.Namespace, ignore_pfmrs=False):
        '''作品ページの解析'''
        self._he = he
        self._sm = sm
        self.ignore_pfmrs = ignore_pfmrs
        self.data_replaced = False
        self.bluray = False
        self.omit_suss = False
        self.rental_pcdr = False
        self.force_chk_sale = False

        verbose('self._sm: ', self._sm.items())

        # 作品情報の取得
        for prop in self._he.iterfind('.//td[@class="nw"]'):
            self._ret_props(prop)

        # タイトルの取得
        if not self._sm['title'] or self._sm['title'].startswith('__'):
            self._sm['title'], self._sm['title_dmm'] = self._ret_title(args.longtitle)

        if service == 'ama':
            # 素人動画の時のタイトル/副題の再作成
            self._sm['title'] = self._sm['subtitle'] = \
                                self._sm['title'] + self._sm['subtitle']

        sale_data = None
        # if self.deeper and service != 'ama' and __name__ != '__main__':
        if self.deeper and service != 'ama':
            if self.rental_pcdr and args.check_rental:
                # レンタル先行メーカーチェック
                if service != 'rental':
                    # レンタル先行メーカーなのにレンタル版のURLじゃなかったらレンタル版を
                    # 調べてリリースの早い方を採用
                    verbose('checking rental...')
                    rental_data = self._get_otherscontent('rental')
                    if rental_data:
                        emsg('W',
                             'レンタル版のリリースが早いためレンタル版に'
                             '変更します。')
                        if __name__ != '__main__':
                            emsg('W', self._sm['title'])
                        self.data_replaced = 'rental'
                        # レンタル版データで置き換え
                        # sale_rel = self._sm['release']
                        self._sm.update(rental_data)

                elif args.check_rltd:
                    # レンタル版URLだったときのセル版へのリンクチェック
                    # セル版があればそれへのリンクとリリース日を、なければレンタル版と付記
                    verbose('checking sale...')
                    sale_data = self._get_otherscontent('dvd')
                    if sale_data:
                        self._sm['others'].append(
                            self._link2other(sale_data['url'],
                                             'セル',
                                             sale_data['release']))
                    else:
                        self._sm['others'].append('※レンタル版')

            # if service == 'video':
            #     # 動画配信のみかどうかチェック → できない
            #     for o in ('dvd', 'rental'):
            #         if self._get_otherslink(o, firmly=False):
            #             break
            #     else:
            #         self._sm['note'].append('動画配信のみ')

            # Blu-ray版のときのDVD版の、またはその逆のチェック
            related = 'DVD' if self.bluray else 'Blu-ray'
            rltd_url = self._check_rltditem(related)
            if rltd_url:
                if self.bluray and self.pass_bd:
                    # Blu-ray版だったときDVD版があればパス
                    verbose('raise Blu-ray exception')
                    raise OmitTitleException('Blu-ray', 'DVD exists')
                else:
                    self._sm['note'].append('[[{}版あり>{}]]'.format(
                        related, rltd_url))

        # パッケージ画像の取得
        self._sm['image_lg'], self._sm['image_sm'] = self._ret_images(service)

        if not self.ignore_pfmrs:
            # 出演者の取得
            self._sm['actress'] = list(
                self._ret_performers(
                    self._sm['actress'],
                    getattr(args, 'smm', False) and service == 'dvd'))

            # レンタル版で出演者情報がなかったとき他のサービスで調べてみる
            if (service == 'rental' or self.data_replaced == 'rental') \
               and (not self._sm['actress'] or self.force_chk_sale) \
               and args.check_rltd:

                verbose('possibility missing performers, checking others...')
                other_data = self._get_otherscontent('videoa', 'dvd')

                if other_data and other_data['actress']:
                    self._sm['actress'].extend(a for a in other_data['actress']
                                               if a not in self._sm['actress'])

        return ((key, self._sm[key]) for key in self._sm if self._sm[key])

_othersparser = DMMParser(deeper=False)


def search_listpage(url, listname, listtype, pid):
    '''実際の一覧ページをWiki内で探してみる'''
    # listname = set((listname,)) | set(
    #     _libssw.p_inbracket.split(listname.rstrip(')）')))
    verbose('Searching listpage: listname=', listname, ', pid=', pid)

    # DMM作品ページのURLで検索
    resp, he = _libssw.open_url(
        'http://sougouwiki.com/search?keywords={}'.format(
            _libssw.quote(url, safe='')),
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
            pagin = he.find('.//div[@class="paging-top"]/a[last()]')
            if pagin is not None and pagin.text.strip() == '次の20件':
                nextp = pagin.get('href')
                resp, he = _libssw.open_url(_up.urljoin(BASEURL_SSW, nextp),
                                            cache=False)
            else:
                break


def check_actuallpage(url, lpage, ltype, pid):
    '''
    実際の一覧ページのチェック
    見つかったらREDIRECTSにキャッシュしておく
    '''
    global REDIRECTS

    if not _libssw.RECHECK \
       and url in REDIRECTS \
       and REDIRECTS[url] != '__NOT_FOUND__':
        # キャッシュされてたらそれを返す
        verbose('list page found on REDIRECTS: ', REDIRECTS[url])
        return lpage if REDIRECTS[url] == '__NON__' else REDIRECTS[url]

    verbose('check actual list page on ssw...')
    pages = tuple(search_listpage(url, lpage, ltype, pid))
    verbose('list page found: ', pages)

    result = None
    numcand = len(pages)
    if not numcand:
        verbose('list page search result is zero')
        # 見つからなかったらシリーズ/レーベル名で開いてあればそれを返す
        dest = _libssw.follow_redirect(lpage)
        verbose('dest: ', dest)
        if dest:
            result = dest
    elif numcand == 1:
        # 候補が1個ならそれを返す
        result = pages[0]
    else:
        emsg('I', '一覧ベージ候補が複数見つかりました:')
        for cand in pages:
            emsg('I', '⇒ ', cand)

    if result:
        REDIRECTS[url] = result
        _libssw.save_cache(REDIRECTS, _libssw.RDRDFILE)

    return result


def det_listpage(summ, args):
    '''一覧ページへのリンク情報の決定'''
    verbose('List link processed')

    list_type = ''

    for attr, typ in (('series', 'シリーズ'),
                      ('label', 'レーベル'),
                      ('maker', 'メーカー')):

        list_page = summ[attr]

        if list_page:
            if list_page == '__HIDE__':
                continue
            elif _libssw.le80bytes(list_page):
                list_type = typ
                break
            else:
                emsg('W',
                     typ,
                     '名が80バイトを超えているのでそのページは無いものとします: ',
                     list_page)
    else:
        return '', ''

    verbose('List type: {}, List page: {}'.format(list_type, list_page))

    # SCOOP個別対応
    if list_page == 'SCOOP（スクープ）':
        list_page = 'スクープ'

    # wiki構文と衝突する文字列の置き換え
    list_page = list_page.translate(_libssw.t_wikisyntax)

    if not args.check_listpage:
        return list_type, list_page

    # Wiki上の実際の一覧ページを探し、見つかったらそれにする。
    actuall = check_actuallpage(summ['url'],
                                list_page,
                                list_type,
                                summ['pid'])
    if actuall:
        list_page = actuall
    else:
        emsg('W', list_type,
             '一覧ページが見つからなかったのでDMMのものを採用します。')
        emsg('W', list_type, ': ', list_page)
        if __name__ != '__main__':
            emsg('W', 'タイトル: ', summ['title'])

    return list_type, list_page


def expansion(phrases, summ):
    '''予約変数の展開'''
    for ph in phrases:
        for p, r in sp_expansion:
            ph = p.sub(getattr(summ, r), ph)
        yield ph


def check_missings(summ):
    '''未取得情報のチェック'''
    missings = [m for m in ('release', 'title', 'maker', 'label', 'image_sm')
                if not summ[m]]
    verbose('missings: ', missings)
    missings and emsg(
        'W', '取得できない情報がありました: ', ",".join(missings))


def format_wikitext_a(summ, anum, astr):
    '''ウィキテキストの作成 女優ページ用'''
    wtext = ''

    # 発売日
    date = summ['release'].replace('/', '.')
    wtext += '//{0} {1[pid]}\n'.format(date, summ)
    # 自動修正があった場合のDMM上のタイトル (コメント)
    if summ['title_dmm']:
        wtext += '//{0[title_dmm]} #検索用\n'.format(summ)
    # タイトルおよびメーカー
    titleline = '[[{0[title]} {0[size]}（{1}）>{0[url]}]]'.format(
        summ, summ['maker'] or summ['label']
    ) if summ['size'] else '[[{0[title]}（{1}）>{0[url]}]]'.format(
        summ, summ['maker'] or summ['label'])
    # シリーズ
    if summ['list_type']:
        titleline += '　[[({0[list_type]}一覧)>{0[list_page]}]]'.format(summ)
    wtext += titleline + '\n'
    # 画像
    wtext += '[[{0[image_sm]}>{0[image_lg]}]]\n'.format(summ)
    # 出演者
    if anum not in (0, 1):
        wtext += '出演者：{0}\n'.format(astr)
    # 備考
    notes = summ['note'] + summ['others'] if summ['others'] else summ['note']
    if notes:
        wtext += '、'.join(notes) + '\n'

    return wtext


def format_wikitext_t(summ, astr, dstr, dir_col, diff_page, add_column):
    '''ウィキテキストの作成 table形式'''
    wtext = ''

    # 品番
    wtext += '|[[{0[pid]}>{0[url]}]]'.format(summ) if summ['url'] \
             else '|{0[pid]}'.format(summ)

    # 画像
    wtext += '|[[{0[image_sm]}>{0[image_lg]}]]'.format(summ) if summ['url'] \
             else '|'

    # サブタイトル
    wtext += '|{0[subtitle]}~~{0[size]}'.format(summ) if summ['size'] \
             else '|{0[subtitle]}'.format(summ)

    # 出演者
    wtext += '|[[別ページ>{}]]'.format(summ['list_page']) if diff_page \
             else '|{0}'.format(astr)

    # 監督
    if dir_col:
        wtext += '|{0}'.format(dstr)

    # 追加カラム
    if add_column:
        wtext += '|' + '|'.join(add_column)

    # 発売日
    wtext += '|{0[release]}'.format(summ).replace('/', '-')

    # 備考
    wtext += '|{}|'.format('、'.join(summ['note']))

    return wtext


def main(props=_libssw.Summary(), p_args=_argparse.Namespace,
         dmmparser=DMMParser()):

    # モジュール呼び出しの場合継承したコマンドライン引数は無視
    argv = [props.url] if __name__ != '__main__' else _sys.argv[1:]
    args = _get_args(argv, p_args)

    # 作品情報
    summ = _libssw.Summary()

    if __name__ == '__main__':
        verbose('args: ', args)
        if not args.url:
            # URLが渡されなかったときは標準入力から
            verbose('Input from stdin...')

            data = _sys.stdin.readline().rstrip('\n')

            if not data:
                emsg('E', 'URLを指定してください。')

            verbose('data from stdin: ', data.split('\t'))
            for key, data in zip(('url', 'title', 'pid', 'actress', 'number',
                                  'director', 'director', 'note'),
                                 data.split('\t')):
                if key == 'url':
                    summ[key] = data.split('?')[0]
                elif key == 'actess':
                    summ[key] = list(_libssw.parse_names(a) for a in data)
                elif key == 'number':
                    summ[key] = int(data) if data else 0
                elif key == 'director':
                    summ[key] = _libssw.p_delim.split(data)
                elif key == 'note':
                    summ[key].append(data)
                else:
                    summ[key] = data

            verbose('summ from stdin: ', summ.items())

        for attr in ('url', 'number', 'pid', 'subtitle'):
            if not summ[attr]:
                summ[attr] = getattr(args, attr)

        if not summ['actress'] and args.actress:
            actiter = _chain.from_iterable(
                _libssw.p_delim.split(a) for a in args.actress)
            summ['actress'] = list(_libssw.parse_names(a) for a in actiter)

    else:
        verbose('props: ', props.items())
        verbose('p_args: ', vars(p_args))

        summ.update(props)

    for attr, typ in (('series', 'シリーズ'), ('label', 'レーベル')):
        if getattr(args, attr):
            summ['list_type'] = typ
            summ['list_page'] = getattr(args, attr)

    # 品番
    if not summ['pid']:
        summ['pid'], summ['cid'] = _libssw.gen_pid(summ['url'], sp_pid)

    retrieval = getattr(p_args, 'retrieval',
                        'series' if args.as_series else 'find')
    service = getattr(p_args, 'service', None)
    series_guide = getattr(p_args, 'series_guide', True)

    if args.actress and args.actress[0].startswith('@@'):
        # ウィキテキストで直接指定
        rawpfmrs = args.actress[0].lstrip('@@')
    else:
        rawpfmrs = ''

    # サービス未指定時の自動決定
    if not service:
        service = _libssw.resolve_service(summ['url'])
    verbose('service resolved: ', service)

    if service == 'ama':
        # 動画(素人)の場合監督欄は出力しない。
        args.dir_col = False

    join_d = dict()

    if args.join_tsv:
        # join データ作成(tsv)
        verbose('join tsv')
        for k, p in _libssw.from_tsv(args.join_tsv):
            join_d[k] = p

    if args.join_wiki:
        # join データ作成(wiki)
        verbose('join wiki')
        for k, p in _libssw.from_wiki(args.join_wiki):
            if k in join_d:
                join_d[k].merge(p)
            else:
                join_d[k] = p

    if args.join_html:
        # jon データ作成(url)
        verbose('join url')
        for k, p in _libssw.from_html(args.join_html):
            if k in join_d:
                join_d[k].merge(p)
            else:
                join_d[k] = p

    if (args.join_tsv or args.join_wiki or args.join_html) and not len(join_d):
        emsg('E', '--join-* オプションで読み込んだデータが0件でした。')

    # URLを開いて読み込む
    resp, he = _libssw.open_url(summ['url'])

    if resp.status == 404:
        # 404の時、空のエントリを作成(表形式のみ)して返す
        emsg('I', 'ページが見つかりませんでした: ', summ['url'])
        if p_args.cid_l:
            summ['url'] = ''
        else:
            if not summ['subtitle']:
                summ['subtitle'] = summ['title']
            summ['image_sm'], summ['image_lg'] = _build_image_url(service,
                                                                  summ['cid'])
        wktxt_t = format_wikitext_t(summ,
                                    '',
                                    '／'.join(summ['director']),
                                    args.dir_col,
                                    False,
                                    add_column)
        verbose('wktxt_t: ', wktxt_t)
        return False, resp.status, ReturnVal(summ['release'],
                                             summ['pid'],
                                             summ['title'],
                                             summ['title_dmm'],
                                             summ['url'],
                                             summ.values('maker', 'maker_id'),
                                             summ.values('label', 'label_id'),
                                             summ.values('series', 'series_id'),
                                             wktxt_a=(),
                                             wktxt_t=wktxt_t)
    elif resp.status != 200:
        return False, resp.status, ('HTTP status', resp.status)

    # 構文ミスの修正
    # html = _libssw.sub(sp_href, html)

    # HTMLの解析
    try:
        summ.update(dmmparser(he, service, summ, args, ignore_pfmrs=rawpfmrs))
    except OmitTitleException as e:
        # 除外対象なので中止
        return False, 'Omitted', (e.key, e.word)

    verbose('summ: ', summ.items())

    if dmmparser.data_replaced:
        service = dmmparser.data_replaced

    # joinデータがあったら補完
    if summ['url'] in join_d:
        summ.merge(join_d[summ['url']])

    # 画像がまだないときのリンク自動生成
    if not summ['image_lg']:
        summ['image_sm'], summ['image_lg'] = _build_image_url(service,
                                                              summ['cid'])
        verbose('image_sm: ', summ['image_sm'])
        verbose('image_lg: ', summ['image_lg'])

    #
    # タイトルの調整
    #
    # 削除依頼対応
    for dl in _libssw.HIDE_NAMES.values():
        summ['title'] = summ['title'].replace(dl, '').strip()

    on_dmm = summ['title']
    # wiki構文と衝突する文字列の置き換え
    modified = on_dmm.translate(_libssw.t_wikisyntax)
    if AUTOMODIFY:
        # ♥の代替文字列の置き換え
        modified = _libssw.sub(sp_heart, modified)

    summ['title'] = modified
    if not summ['title_dmm'] and modified != on_dmm:
        summ['title_dmm'] = on_dmm
    verbose('summ[title]: ', summ['title'])
    verbose('summ[title_dmm]: ', summ['title_dmm'])

    # シリーズ/レーベル一覧へのリンク情報の設定
    # 一覧ページの直接指定があればそれを、なければ シリーズ > レーベル で決定
    if not (args.hide_list or summ['list_type']):
        summ['list_type'], summ['list_page'] = det_listpage(summ, args)
    if args.linklabel:
        summ['list_type'] = args.linklabel
    verbose('summ[list_page]: ', summ['list_page'])

    if args.note:
        summ['note'] = list(expansion(args.note, summ)) + summ['note']
    verbose('note: ', summ['note'])

    add_column = tuple(expansion(args.add_column, summ)) if args.add_column else ()
    verbose('add column: ', add_column)

    # 出演者文字列の作成
    pfmrslk = ()
    if rawpfmrs:
        # ウィキテキスト
        pfmrslk = _libssw.p_linkpare.findall(rawpfmrs)
        pfmrsstr, pnum = rawpfmrs, len(pfmrslk)
    elif len(summ['actress']) < 2 and not summ['number'] and args.table == 0:
        # 女優ページ用のみ作成で出演者数が1人ならやらない
        pfmrsstr, pnum = '', 0
    else:
        pfmrsstr, pnum = _libssw.stringize_performers(summ['actress'],
                                                      summ['number'],
                                                      args.follow_rdr)

    # 監督文字列の作成
    dirstr = '／'.join(summ['director'])

    # table形式用副題の生成
    if retrieval == 'series':
        # シリーズ名が list_page にあってタイトルの先頭からシリーズ名と
        # 同じ文字列があれば落とす。
        # list_page に値がなければタイトルをそのまま入れる。
        if not summ['subtitle']:
            summ['subtitle'] = _re.sub(
                r'^{}[、。！？・…♥]* '.format(summ['series']),
                '',
                summ['title'],
                flags=_re.I).strip()

    elif not summ['subtitle']:
        # タイトルをそのまま副題に(表形式用)
        summ['subtitle'] = summ['title']
    verbose('subtitle: ', summ['subtitle'])

    # 未取得情報のチェック
    if VERBOSE:
        check_missings(summ)

    # レーベル一覧での [[別ページ>]] への置き換えチェック
    # Wikiの制限で80バイトを超える場合は置き換えない
    diff_page = (series_guide and
                 retrieval in ('label', 'maker') and
                 _libssw.le80bytes(summ['series']) and
                 summ['series'] and
                 summ['series'] != '__HIDE__')
    verbose('diff_page: ', diff_page)

    # ウィキテキストの作成
    wikitext_a = format_wikitext_a(
        summ, pnum, pfmrsstr) if args.table != 1 else ()
    wikitext_t = format_wikitext_t(summ,
                                   pfmrsstr,
                                   dirstr,
                                   args.dir_col,
                                   diff_page,
                                   add_column) if args.table else ''

    if __name__ != '__main__':
        # モジュール呼び出しならタプルで返す。
        return True, summ['url'], ReturnVal(summ['release'],
                                            summ['pid'],
                                            summ['title'],
                                            summ['title_dmm'],
                                            summ['url'],
                                            summ.values('maker', 'maker_id'),
                                            summ.values('label', 'label_id'),
                                            summ.values('series', 'series_id'),
                                            wikitext_a,
                                            wikitext_t)
    else:
        # 書き出す
        print()
        if wikitext_a:
            print(wikitext_a)

        if wikitext_t:
            print(wikitext_t)

        print()

        # if args.copy:
        #     verbose('copy 2 clipboard')
        #     _libssw.copy2clipboard(output)

        if args.browser:
            # wikiのページを開く
            if args.table != 1:
                pages = pfmrslk or summ['actress']
                for a in pages:
                    _libssw.open_ssw(a[1] or a[0])
            if args.table:
                _libssw.open_ssw(summ['list_page'])

    # キャッシュディレクトリの削除
    if args.clear_cache:
        _libssw.clear_cache()


if __name__ == '__main__':
    main()
