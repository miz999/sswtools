#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
素人系Wikiの女優ページにない作品情報をDMMから取得して補完

書式:
sswactcomp.py [女優ページのファイル [ファイル ...]] [オプション ...]


説明:
    Wiki女優ページのウィキテキストとDMM上の女優の作品一覧とを比較し、Wiki側に
    足りない作品情報を補完する。
    総集編と書かれていない総集編が紛れ込んでしまうので注意。
    また、元のウィキテキストのレイアウトを必ず維持するとは限らないので、入力ファイルと
    出力ファイルの比較を忘れないこと。


引数:
Wiki女優ページのウィキテキストのファイル名
    ファイル名を指定しないと標準入力から読み込む。
    複数のウィキテキストを読み込むことができるが、出力ファイルではそれらは一つに
    まとめられる。


オプション:
-a, --actress 女優ID [女優ID ...]
    DMM上の女優IDを指定する。改名していて統合されていない場合はそれぞれのIDを
    指定できる。DMM上でのその女優の作品一覧のURLでも可。
    入力ファイル内に女優女優の作品一覧のURLがあればそこからの取得を試みる。

-o, --out ファイル名
    指定されたファイルに出力する。未指定時は標準出力に出力する。

-r, --replace
    出力ファイル名と同名のファイルが存在する場合それを上書きする。

-m, --disable-omit
    イメージビデオを除外しない。
    m を2個指定すると総集編作品も、
    3個指定するとアウトレットも、
    4個指定すると限定盤も除外しない。
    除外もれが発生する場合もある。

-f, --disable-follow-redirect
    取得した出演者名のwikiページがリダイレクトページかどうかチェックしない。
    指定しない場合チェックし、そうであればリダイレクト先へのリンクを取得して
    付加する。
    詳細はdmm2ssw.pyの説明参照。

--disable-check-rental
    レンタル先行メーカーなのにセル版の情報を指定されていた場合でもレンタル版の
    リリースをチェックしない。

--disable-check-listpage
    Wiki上の実際の一覧ページを探さない。

--disable-check-bd
    デフォルトでは、Blu-ray版製品だったとき、DVD版がないか確認し、DVD版があれば
    Blu-ray版の情報は作成しない(DVD版の方で備考としてBlu-ray版へのリンクを付記
    する)が、このオプションが与えられるとそれを行わず、DVD版と同様に作成する。

--fastest
    処理時間に影響する(ウェブページへアクセスする)あらゆる補助処理を行わない。

-d, --diff
    データ追加前と追加後の差分をウェブブラウザで表示する。
    厳密には元のウィキテキストそのものとの差分ではなく、テキストを解析した後の
    作品情報単位での差分。

-C, --clear-cache
    HTTPキャッシュを終了時に削除する。

-v, --verbose
    デバッグ用情報を出力する。

-V, --version
    バージョン情報を表示して終了する。

-h, --help
    ヘルプメッセージを表示して終了する。
"""
import sys
import argparse
import re
import fileinput
from collections import OrderedDict
from operator import itemgetter
from itertools import chain

import libssw
import dmm2ssw

__version__ = 20140805

VERBOSE = 0

OWNNAME = libssw.ownname(__file__)
BASEURL = libssw.BASEURL

SPLIT_DEFAULT = 200

verbose = libssw.Verbose(OWNNAME, VERBOSE)
emsg = libssw.Emsg(OWNNAME)

p_cstart = re.compile(r'^// *(\d+.?\d+.?\d+)')
p_product = re.compile(r'>(http://www.dmm.co.jp/.*/cid=.*?)]]')
p_actid = re.compile(r'/article=actress/id=([\d,]+?)/')
p_linkurl = re.compile(r'>(http://.+?)\]\]')

sp_datedelim = (re.compile(r'-/'), '.')


def get_args():
    global VERBOSE
    global verbose

    argparser = argparse.ArgumentParser(
        description='素人系総合wiki女優ページにない作品情報をDMMから補完する')
    argparser.add_argument('wikifiles',
                           help='Wiki女優ページ(ウィキテキスト)を格納したファイル(未指定で標準入力から入力)',
                           nargs='*',
                           metavar='WIKIFILES')
    argparser.add_argument('-a', '--actress-id',
                           help='DMM上での女優のID(または女優の作品一覧のURL)',
                           nargs='+',
                           default=[],
                           metavar='ID')

    # ファイル出力
    argparser.add_argument('-o', '--out',
                           help='ファイルに出力 (未指定時は標準出力へ出力)',
                           metavar='FILE')
    argparser.add_argument('-r', '--replace',
                           help='出力ファイルと同名のファイルがあった場合上書きする',
                           action='store_true')

    argparser.add_argument('--split',
                           help='指定作品数ごとに「// {0}」のようにコメント行を入れる (デフォルト {0})'.format(SPLIT_DEFAULT),
                           type=int,
                           default=SPLIT_DEFAULT)

    # 作品データの除外基準
    argparser.add_argument('-m', '--disable-omit',
                           help='IVを除外しない, 2個指定すると総集編作品も、'
                           '3個指定するとアウトレット版も、'
                           '4個指定すると限定盤も除外しない',
                           dest='no_omit',
                           action='count',
                           default=0)

    argparser.add_argument('-f', '--disable-follow-redirect',
                           help='ページのリダイレクト先をチェックしない',
                           dest='follow_rdr',
                           action='store_false',
                           default=True)
    argparser.add_argument('--disable-check-rental',
                           help='レンタル先行メーカーでセル版のときレンタル版の'
                           'リリースをチェックしない',
                           action='store_false',
                           dest='check_rental',
                           default=True)
    argparser.add_argument('--disable-check-bd',
                           help='Blu-ray版のときDVD版があってもパスしない',
                           action='store_false',
                           dest='pass_bd',
                           default=True)
    argparser.add_argument('--disable-check-listpage',
                           help='Wiki上の実際の一覧ページを探さない',
                           dest='check_listpage',
                           action='store_false',
                           default=True)
    argparser.add_argument('--fastest',
                           help='処理時間に影響するあらゆる補助処理を行わない',
                           action='store_true')

    argparser.add_argument('-d', '--diff',
                           help='データ追加前と後の差分をウェブブラウザで表示する',
                           action='store_true')

    argparser.add_argument('-C', '--clear-cache',
                           help='プログラム終了時にHTTPキャッシュをクリアする',
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

    # dmmsar.py 側からVERBOSEが変更される場合があるため
    verbose.verbose = VERBOSE = VERBOSE or args.verbose

    if not VERBOSE:
        verbose = libssw.verbose = lambda *x: None
    elif VERBOSE > 1:
        libssw.VERBOSE = libssw.verbose.verbose = \
            dmm2ssw.VERBOSE = dmm2ssw.verbose.verbose = VERBOSE - 1
        verbose('verbose mode on')

    if args.fastest:
        for a in ('follow_rdr', 'check_rental', 'pass_bd', 'check_listpage'):
            setattr(args, a, False)

    verbose('args: ', args)
    return args


def add_actid(g_actid, actids):

    def append_id(aid):
        if aid and aid not in g_actid:
            g_actid.append(aid)

    for ai in actids:
        if ai.startswith('http://'):
            for a in chain.from_iterable(i.split(',')
                                         for i in p_actid.findall(ai)):
                append_id(a)
        else:
            append_id(ai)


def get_existing(g_actid, files):
    """
    Wikiテキストをファイルから読み込んで作品ごとの情報を返すジェネレータ
    ついでに引数で女優IDが与えられていないときに自動取得を試みる。
    """
    item = []
    key = None
    url = None
    rdate = None
    i = 0

    fd = fileinput.input(files=files)

    for row in fd:
        row = row.strip()

        # //YYYY.MM.DD の行かどうか
        m_rd = p_cstart.findall(row)

        if not url:
            # urlがまだ見つかってないときにurlがあるか探す
            url = p_product.findall(row)

        if row.startswith('*[['):
            # 必要であれば女優IDを追加
            add_actid(g_actid, p_linkurl.findall(row))

        if m_rd or not row:
            # 空行かリリース日の行だったら作品情報1個分完了
            if url:
                key = url[0]

            if item:
                yield key or str(i), rdate, '\n'.join(item)

            # 次の作品のための初期化
            if m_rd:
                # リリース日発見
                item = [row]
                rdate = libssw.sub(sp_datedelim, m_rd[0])
            else:
                # 空行発見
                item = []

            key = url = None
            i += 1

        else:
            item.append(row)

    if item:
        yield key or str(i), rdate, '\n'.join(item)

    fd.close()


def main():

    args = get_args()

    libssw.files_exists('r', *args.wikifiles)
    if args.out:
        if args.replace:
            writemode = 'w'
        else:
            libssw.files_exists('w', args.out)
            writemode = 'x'
    else:
        writemode = None

    g_actid = []
    seq = []
    contents = dict()
    release = dict()

    # 女優IDがURL渡しだったときの対処
    add_actid(g_actid, args.actress_id)

    # 除外対象
    no_omits = libssw.gen_no_omits(args.no_omit)
    verbose('non omit target: ', no_omits)

    # ウィキテキストの読み込み
    # 女優IDも取得
    for key, rdate, item in get_existing(g_actid, args.wikifiles):
        seq.append(key)
        contents[key] = item
        release[key] = rdate
        verbose('key: ', key)
        verbose('rdate: ', rdate)
        verbose('item: ', item)

    # 複数のIDがあった時にカンマで区切る
    aidstr = ','.join(g_actid)
    emsg('I', '女優ID: ', aidstr)

    listparser = libssw.DMMTitleListParser(no_omits)
    priurls = libssw.join_priurls('actress', aidstr)

    # Wikiにない作品情報の取り込み
    emsg('I', '作品一覧を取得中...')
    products = OrderedDict(
        (u, p) for u, p in libssw.from_dmm(listparser, priurls)
        if u not in seq)
    emsg('I', '一覧取得完了')

    total = len(products)
    if not total:
        emsg('E', '検索結果は0件でした。')

    verbose('Start building product info')
    if not VERBOSE:
        print('作成中...', file=sys.stderr, flush=True)

    # 不足分のウィキテキストを作成
    current = seq[:]
    newitems = []
    rest = total
    omitted = 0

    dmmparser = libssw.DMMParser(no_omits)

    for url in products:
        props = products[url]
        verbose('props: ', props.items())

        props.pid, g_cid = libssw.gen_pid(props.url)

        libssw.inprogress('(残り {} 件/全 {} 件: 除外 {} 件)  '.format(
            rest, total, omitted))

        b, status, data = dmm2ssw.main(props=props,
                                       p_args=args,
                                       dmmparser=dmmparser)
        verbose('Return from dmm2ssw: {}, {}, {}'.format(
            b, status, data))

        if b:
            newitems.append(data)
        elif status == 404:
            emsg('I', 'ページが見つかりませんでした: url="{}"'.format(props.url))
            newitems.append(data)
        else:
            emsg('I', 'ページを除外しました: '
                 'cid={0}, reason=("{1[0]}", "{1[1]}")'.format(
                     props.cid, data))
            omitted += 1
        rest -= 1
        verbose('rest: {} / total: {} / omitted: {}'.format(rest, total,
                                                            omitted))

    # レンタル先行作品があった場合のためソート
    newitems.sort(key=itemgetter(0), reverse=True)

    # マージ
    i = -1
    for new in newitems:
        verbose('new: ', new)
        if new.url in seq:
            # レンタル版に変更にあったものの既存チェック
            continue

        for i, key in enumerate(seq[i + 1:], start=i + 1):
            # 時系列で途中のデータの挿入
            verbose('i, key: {}, {}'.format(i, key))
            if not key.isdecimal():
                verbose('new: {} > curr: {}'.format(
                    new.release.replace('/', '.'), release[key]))
                if new.release.replace('/', '.') > release[key]:
                    # 新規データの挿入
                    verbose('insert: {}, {}'.format(key, contents[key][1]))
                    seq.insert(i, new.url)
                    contents[new.url] = new.wktxt_a
                    release[new.url] = new.release
                    break
                elif '----' in contents[key]:
                    seq.append(new.url)
                    contents[new.url] = new.wktxt_a
                    release[new.url] = new.release
                    break
        else:
            # 残りのデータの追加
            seq.append(new.url)
            contents[new.url] = new.wktxt_a
            release[new.url] = new.release

    if args.diff:
        # 差分の出力
        libssw.show_diff(
            tuple(contents[k] for k in current),
            tuple(contents[k] for k in seq),
            '追加前',
            '追加後')

    # 出力
    header = False
    i = 0
    fd = open(args.out, writemode) if args.out else sys.stdout
    while seq:
        key = seq.pop(0)
        if key.startswith('http://'):
            i += 1
            if args.split and not i % args.split:
                print('// {}'.format(i), file=fd)
        content = contents[key]
        if content.startswith('*'):
            header = True
        print(content, file=fd)
        if (not header or len(content) > 2) and seq:
            print(file=fd)
        header = False
    print()
    if args.out:
        fd.close()

    # キャッシュディレクトリの削除
    if args.clear_cache:
        libssw.clear_cache()


if __name__ == '__main__':
    main()
