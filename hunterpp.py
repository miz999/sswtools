#!/usr/bin/env python
'''
Hunterなど、一部メーカーの無駄に長いタイトルをメーカー公式サイトから取得して
dmmsar.pyやdmm2ssw.pyの入力となるTSVデータを作成する。

書式:
hunterpp.py 公式サイトの作品ページURL(開始) [公式サイトの作品ページURL(終了)] [オプション...]


説明:
    対応サイト) Hunter、Apache、ATOM、SWITCH

    メーカー公式サイトから作品ページを読み込み、タイトル、DMMサイトのURL、品番
    からなるTSVデータを作成する。
    URLを1個だけ指定するとその作品だけ、2個指定すると1個めを開始、2個めを終了のURLとみなし、
    その間の番号のURLのデータも作成する。
    このデータをdmmsar.pyやdmm2sww.pyに読み込ませて素人系総合Wikiのウィキテキストを
    作成できる。
    Apacheの作品についてはdmm2ssw.pyでも公式サイトを見に行くので、DMMで公開済みの作品で
    あればこれを使う必要はない。


引数:
メーカー公式サイトの作品ページのURLまたはサイト上の作品の番号(数値部のみ)


オプション:
-m, --maker
    作品のメーカー。引数をURLで指定していれば不要。

-o, --out
    出力ファイル名。未指定時は標準出力に出力。

-r, --replace
    出力ファイルと同名のファイルがあったとき上書きする。

-a, --append
    出力ファイルと同名のファイルがあったときそれに追加する。

--tee
    ファイルに出力するとともに標準出力にも出力する。

-v, --verbose
    デバッグ用情報を出力する。

-V, --version
    バージョン情報を表示して終了する。

-h, --help
    ヘルプメッセージを表示して終了する。


使用例:
  1) 作品1個だけのウィキテキストを作成する(dmm2sswを使用)。

    hunterpp.py "http://www.apa-av.jp/list_detail/detail_207.html" | dmm2ssw.py

  2) 複数まとめて作成する(dmmsar.pyを使用)。公式サイト上の番号で指定する場合。
      dmmsar.py では -Li (レーベル一覧、TSVファイルから入力) を指定する。

    hunterpp.py "0000100970" "0000100990" -m hunter | dmmsar.py -Lit

  3) 事前にTSVファイルに出力されたものを利用してウィキテキストを作成する

    hunterpp.py "http://www.hunter-pp.jp/detail.php?value=site0000100978" -ao hunter.tsv

    (Windows)
    findstr hunt982 hunter.tsv | dmm2ssw.py -a 羽月希 松島れん 椿かなり 辻本りょう 水城奈緒

    (MacOSX/Linux)
    grep hunt982 hunter.tsv | dmm2ssw.py -a ...

'''
import argparse
import sys
import urllib.parse as up
import re

import libssw

__version__ = 20150526

OWNNAME = libssw.ownname(__file__)
VERBOSE = 0

verbose = libssw.Verbose(OWNNAME, VERBOSE)
emsg = libssw.Emsg(OWNNAME)

DMMBASE = 'http://www.dmm.co.jp/mono/dvd/-/detail/=/cid={}/'

MAKER = {'www.hunter-pp.jp': 'hunter',
         'www.a-t-o-m.jp': 'atom',
         'www.apa-av.jp': 'apache',
         'switch1.jp': 'switch',
         }

BASEURL = {
    'hunter': 'http://www.hunter-pp.jp/detail.php?value=site{:0>{}}',
    'apache': 'http://www.apa-av.jp/list_detail/detail_{:0>{}}.html',
    'atom': 'http://www.a-t-o-m.jp/detail.php?value=site{:0>{}}',
    'switch': 'http://switch1.jp/web/{}',
}

p_id = {
    'hunter': re.compile(r'.*value=site(\d+)'),
    'atom': re.compile(r'.*value=site(\d+)'),
    'apache': re.compile(r'.*/detail_(\d+).html'),
    'switch': re.compile(r'(\d+?)$'),
}

p_cid = re.compile(r'([A-Z]+)-(\d+)')


def get_args():
    global VERBOSE
    global verbose

    argparser = argparse.ArgumentParser(
        description='Hunter、Apache、ATOMの無駄に長いタイトル用プリプロセッサ')

    argparser.add_argument('start',
                           help='開始ID')
    argparser.add_argument('end',
                           help='終了ID',
                           nargs='?',
                           default='')
    argparser.add_argument('-m', '--maker',
                           help='メーカー',
                           choices=('hunter', 'atom', 'apache'))

    argparser.add_argument('-o', '--out',
                           help='ファイルに出力',
                           metavar='FILE')

    writemode = argparser.add_mutually_exclusive_group()
    writemode.add_argument('-r', '--replace',
                           help='出力ファイルと同名のファイルがあったら上書きする',
                           action='store_true')
    writemode.add_argument('-a', '--append',
                           help='出力ファイルと同名のファイルがあったらそれに追加する',
                           action='store_true')

    argparser.add_argument('--tee',
                           help='ファイルとともに標準出力にも出力する',
                           action='store_true')

    argparser.add_argument('-v', '--verbose',
                           help='デバッグ用情報を出力する',
                           action='count',
                           default=0)
    argparser.add_argument('-V', '--version',
                           help='バージョン情報を表示して終了する',
                           action='version',
                           version='%(prog)s {}'.format(__version__))

    args = argparser.parse_args()

    verbose.verbose = VERBOSE = args.verbose

    if not VERBOSE:
        verbose = libssw.verbose = lambda *x: None
    elif VERBOSE > 1:
        libssw.VERBOSE = libssw.verbose.verbose = VERBOSE - 1
        verbose('Verbose mode on')

    return args


def gen_urls(site, args):
    '''
    メーカー公式ページのURLの作成
    '''
    def get_value(item):
        '''引数がURLだったときURLの数値部を取り出す'''
        return p_id[site].findall(item)[0] if item.startswith('http://') \
            else item

    start = get_value(args.start)
    end = get_value(args.end)
    verbose('start: ', start, ', end: ', end)

    digit = max(len(i) for i in (start, end))
    verbose('digit: ', digit)

    if not end:
        return (BASEURL[site].format(start, digit),)
    else:
        return tuple(BASEURL[site].format(i, digit)
                     for i in range(int(start), int(end) + 1))


def tsvize(url, title, pid, actress, director):
    verbose('url: ', url)
    verbose('title: ', title)
    verbose('pid: ', pid)
    verbose('actress: ', actress)
    verbose('director: ', director)
    return '\t'.join((url, title, pid, actress, '', director))


def cidelem(pid):
    return pid.replace('-', '').lower()


def hunterparser(he, site):
    '''Hunterパーサ'''
    title = he.xpath('.//h3')

    if not len(title):
        return

    title = title[0].text.strip().replace('\r\n', ' ')

    detail = he.find_class("detail-main-meta")[0]

    actress = libssw.fmt_name(detail.xpath('li')[0].text)
    pid = detail.xpath('li')[1].text.split('：')[-1].strip()
    cid = '1' + cidelem(pid)
    director = libssw.fmt_name(detail.xpath('li')[2].text)

    dmmurl = DMMBASE.format(cid)
    verbose('DMM: ', dmmurl)

    return tsvize(dmmurl, title, pid, actress, director)


def apacheparser(he, site):
    '''Apacheパーサ'''
    title = he.head.find('title')

    if title is None:
        return

    title = title.text.strip().replace('\n', ' ')

    pid, actress, director = libssw.ret_apacheinfo(he)
    cid = 'h_701' + cidelem(pid)

    dmmurl = DMMBASE.format(cid)

    return tsvize(dmmurl, title, pid, actress, director)


def atomparser(he, site):
    '''ATOMパーサ'''
    title = he.find_class('title_content_box2')

    if not len(title):
        return None

    title = title[0].find('h2').text.strip().replace('\r\n', ' ')
    pid = he.find_class("detail-text")[0].xpath('b')[1].tail.strip('：').strip()
    cid = '1' + cidelem(pid)

    dmmurl = DMMBASE.format(cid)

    return tsvize(dmmurl, title, pid, '', '')


def switchparser(he, site):
    '''SWITCHパーサ'''
    title = he.head.find('meta[@property="og:title"]').get('content')

    varlist = he.find('.//table[@class="extraVarsList"]')
    actress = ','.join(
        varlist.find('tr[3]/td').text.replace('---', '').strip().split())
    director = varlist.find('tr[4]/td').text.strip()
    pid = varlist.find('tr[5]/td').text.strip()
    cid = 'h_635' + cidelem(pid)

    dmmurl = DMMBASE.format(cid)

    return tsvize(dmmurl, title, pid, actress, director)


def gen_tsv(urls, site, parser):
    '''TSVデータジェネレータ'''
    total = rest = len(urls)

    for url in urls:
        verbose('url: ', url)

        resp, he = libssw.open_url(url)

        rest -= 1
        libssw.inprogress('(残り {} 件/全 {} 件)  '.format(rest, total))

        if resp.status == 404:
            continue

        title = he.xpath('.//title')[0].text

        if title.endswith('Error report') or title.startswith('未公開作品'):
            continue

        item = parser(he, site)
        if item:
            yield item

    print(file=sys.stderr, flush=True)


def main():

    args = get_args()
    verbose('args: ', args)

    site = MAKER.get(up.urlparse(args.start).netloc, False) or args.maker
    verbose('site: ', site)

    if not site:
        emsg('E', 'サイト名を解決できませんでした。')

    if args.out:
        if args.replace:
            writemode = 'w'
        elif args.append:
            writemode = 'a'
        else:
            libssw.files_exists('w', args.out)
            writemode = 'x'
        verbose('writemode: ', writemode)

    urls = gen_urls(site, args)
    verbose('urls: ', urls)

    if site == 'hunter':
        parser = hunterparser
    elif site == 'apache':
        parser = apacheparser
    elif site == 'atom':
        parser = atomparser
    elif site == 'switch':
        parser = switchparser

    title_list = tuple(gen_tsv(urls, site, parser))

    fds = []
    if args.out:
        fds.append(open(args.out, writemode))
    if not args.out or args.tee:
        fds.append(sys.stdout)

    for fd in fds:
        print(*title_list, sep='\n', file=fd)

    if args.out:
        fd.close()


if __name__ == '__main__':
    main()
