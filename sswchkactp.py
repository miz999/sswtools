#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
素人系Wikiのレーベル/シリーズ一覧ページにあって女優ページにない作品情報の洗い出し

書式:
sswchkactp.py [一覧ページのURL/HTML/ウィキテキスト ...] [オプション ...]


説明:
    Wikiのレーベル/シリーズ一覧ページを読み込み、そこにある作品と出演者から、それらが
    出演女優のページにあるかどうか、あったとき逆のリンクもちゃんとあるかどうかをチェック
    する。

注意:
    ・セルが結合されている表には未対応。
    ・入力がウィキテキストの場合、ページ名はウィキテキスト内の見出し(大)から取得するが、
      それが実際のページ名と異なる場合は -l オプションで明示的に指定する必要がある。
      例) ページ名は「DANDY 2」だが見出しには「DANDY」の場合など。


引数:
一覧ページのウィキテキストを格納したテキストファイル、一覧ページのURL、あるいはHTML
    未指定時は標準入力から読み込む。

オプション:
-w, --from-wikitext
    入力データ(ファイルまたは標準入力)がウィキテキスト形式の場合指定する。
    指定がないとHTML形式とみなす。

-l, --list-name ページ名
    ウィキテキスト内から正しいページ名が得られないときに直接指定する。

-s, --start-pid チェック開始品番
    このオプションを使用すると指定された開始品番より後の作品だけチェックする。

-g, --gen-wikitext
    女優ページにない作品の女優ページ用のウィキテキストを作成する。

-b, --browser
    ウィキテキストを作成後、wikiの女優ページをウェブブラウザで開く。
    このオプションが指定された場合、-g オプションの指定も自動的に指定される。

-v, --verbose
    デバッグ用情報を出力する。

-V, --version
    バージョン情報を表示して終了する。

-h, --help
    ヘルプメッセージを表示して終了する。
'''
import argparse
import re
import urllib.parse as up
from collections import OrderedDict

import libssw
import dmm2ssw

__version__ = 20150504

VERBOSE = 0

OWNNAME = libssw.ownname(__file__)
verbose = libssw.Verbose(OWNNAME, VERBOSE)
emsg = libssw.Emsg(OWNNAME)

BASEURL_SSW = libssw.BASEURL_SSW

p_ssw = re.compile(r'href="http://sougouwiki.com/d/([^/]+?)"')


def get_args():
    global VERBOSE

    argparser = argparse.ArgumentParser(
        description='素人系総合Wikiの一覧ページにあって女優ページにない作品の洗い出し')
    argparser.add_argument('target',
                           help='調査対象一覧ページのURL/ウィキテキスト(未指定で標準入力から読み込み)',
                           nargs='?',
                           default='-',
                           metavar='TARGET')

    argparser.add_argument('-w', '--from-wikitext',
                           help='入力ファイルがウィキテキストの場合指定する',
                           action='store_true')

    argparser.add_argument('-l', '--list-name',
                           help='一覧ページ名を直接指定')

    argparser.add_argument('-s', '--start-pid',
                           help='チェック開始品番',
                           default='')

    argparser.add_argument('-g', '--gen-wikitext',
                           help='女優ページに作品がない女優がいる作品のウィキテキストを作成する',
                           action='store_true')

    argparser.add_argument('-b', '--browser',
                           help='生成後、wikiのページをブラウザで開く',
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

    verbose.verbose = VERBOSE = VERBOSE or args.verbose
    if args.verbose > 1:
        libssw.VERBOSE = libssw.verbose.verbose = args.verbose - 1
    verbose('verbose mode on')

    args.start_pid = libssw.rm_hyphen(args.start_pid).upper()

    if args.browser:
        args.gen_wikitext = True

    return args


def searchwiki_by_url(url):
    '''検索結果から記事名を返すジェネレータ'''
    resp, he = libssw.open_url(
        'http://sougouwiki.com/search?keywords={}'.format(libssw.quote(url),
        cache=False))

    searesult = he.find_class('result-box')[0].xpath('p[1]/strong')[0].tail

    if searesult.strip() == 'に該当するページは見つかりませんでした。':
        verbose('url not found on ssw')
        return None

    while True:
        for a in he.iterfind('.//h3[@class="keyword"]/a'):
            yield a.get('href'), a.text

        # 次のページがあったらそちらで再度探す
        pagin = he.find_class('paging-top')[0].xpath('a[last()]')
        if len(pagin) and pagin[0].text.strip() == '次の20件':
            nextp = pagin[0].get('href')
            resp, he = libssw.open_url(up.urljoin(BASEURL_SSW, nextp),
                                       cache=False)
        else:
            break


def gen_sswurl(name):
    return up.urljoin(BASEURL_SSW, '/d/{}'.format(libssw.quote(name)))


def check_actrpage(actr_url, listp, prod_url):
    '''
    女優ページに作品情報があるか、一覧ページへのリンクがちゃんとあるかチェック
    '''
    # 女優ページの取得
    resp, html = libssw.open_url(actr_url, cache=False, to_elems=False)
    if resp.status == 404:
        return False, 404, False

    # 女優ページ内の各行をチェックしDMMの作品ページURLがあればその行を取得
    for line in html.split('\n'):

        if prod_url not in line:
            continue

        verbose('prod entry: ', line)

        link2list = p_ssw.findall(line)
        verbose('link to listpage: ', link2list)

        return (True,
                link2list,
                listp.lower() in tuple(L.lower() for L in link2list))

    # 作品情報が見つからなかったら
    verbose('prod info not found')
    return False, False, False


def main():
    args = get_args()

    # 一覧ページからチェックする作品情報を取得
    if args.from_wikitext:
        targets = OrderedDict(libssw.from_wiki((args.target,)))
        listname = libssw.from_wiki.article
    else:
        targets = OrderedDict(libssw.from_html((args.target,)))
        listname = libssw.from_html.article

    # 一覧ページ名の取得
    listname = args.list_name or listname

    if not listname:
        emsg('E', '一覧ページ名を取得できませんでした。-l オプションで指定してください。')

    # listp_url = gen_sswurl(listname)
    listp = libssw.quote(listname)
    verbose('quoted listp: ', listp)

    print('ページ名:', listname)

    before = True if args.start_pid else False
    shortfalls = set()

    for prod_url in targets:

        # 作品情報
        props = targets[prod_url]
        verbose('props: ', props.items())

        pid = libssw.rm_hyphen(libssw.gen_pid(prod_url)[0])
        verbose('pid: ', pid)

        if before and args.start_pid != pid:
            continue
        else:
            before = False

        if not props.actress:
            continue

        print('\nTITLE: {}'.format(props.title))
        print('URL:   {}'.format(prod_url))

        notfounds = []

        # 作品の出演者情報
        for actr in props.actress:

            if not any(actr[:2]):
                continue
            else:
                shown = actr[0]
                dest = actr[1] or actr[0]

            result = ''

            print('* {}({}):'.format(dest, shown) if shown != dest else
                  '* {}:'.format(shown),
                  '...\b\b\b',
                  end='')

            rdr = libssw.follow_redirect(dest)
            if rdr and rdr != dest:
                dest = rdr
                print('(リダイレクトページ) ⇒ {}: '.format(rdr), end='')

            actr_url = gen_sswurl(dest)

            # 女優名のページをチェック
            present, link2list, linked = check_actrpage(actr_url,
                                                        listp,
                                                        prod_url)
            verbose('present: {}, link2list: {}, linked: {}'.format(
                present, link2list, linked))

            if not present:

                if dest not in shortfalls:
                    notfounds.append(dest)
                    shortfalls.add(dest)

                if link2list == 404:
                    result += '✕ (女優ページなし)'.format(shown)
                else:
                    # 女優ページになかったら作品URLで検索してヒットしたWikiページでチェック
                    for purl, label in searchwiki_by_url(prod_url):
                        if label.startswith(dest):
                            present, link2list, linked = check_actrpage(
                                purl, listp, prod_url)
                            if present:
                                result += ' ⇒ {}'.format(label)
                                break
                    else:
                        result += '✕ (女優ページあり)'
            else:

                if linked:
                    result += '○'
                elif link2list:
                    result += '△ (他の一覧ページへのリンクあり: {})'.format(
                        ','.join(
                            '"{}"'.format(libssw.unquote(p))
                            for p in link2list))
                else:
                    result += '△ (一覧ページへのリンクなし)'

            print(result, actr_url)

        # ウィキテキストの作成
        if notfounds and args.gen_wikitext:
            props['title'] = '' # 副題の時もあるので一旦リセット
            b, status, data = dmm2ssw.main(props=props)
            verbose('Return from dmm2ssw: {}, {}, {}'.format(
                b, status, data))
            if b:
                print()
                print(data.wktxt_a)

                if args.browser:
                    for page in notfounds:
                        libssw.open_ssw(page)


if __name__ == '__main__':
    main()
