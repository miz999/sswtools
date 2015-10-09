#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
指定したメーカーのレーベルおよびシリーズの一覧情報をDMMから取得しウィキテキストを作成する

書式:
dmmlasl.py [-t {maker | label}] ID [オプション ...]

説明:
    DMMから、指定したメーカーに所属する全レーベルおよび全シリーズの情報(名称、作品数、
    品番のプレフィクス、最新リリース日)を取得しウィキテキスト形式で一覧を作成する。
    作成したウィキテキストは、デフォルトで
    {maker | label}.<ID>.{メーカー名 | レーベル名}.wiki
    というファイル名で保存する。

    「AVGP」や「AV OPEN」など、広くメーカーにまたがる仮レーベルのシリーズ情報は
    取得しない。

    限定商品とアウトレットは除外する(総集編は含む)。

    収集した情報は、
    {maker | label}.<ID>.{メーカー名 | レーベル名}.pickle
    というファイル名で保存する。
    次回実行時はこのファイルを読み込み再利用する(DMMの作品一覧からファイルに
    ないもののみ情報を取得する)。


注意:
    複数レーベルにまたがるシリーズはレーベルごとに繰り返し同じ(シリーズ全体の)
    情報で表示される。
    このため、このときレーベル内のシリーズごとの作品数の合計とレーベルの作品数とが、
    シリーズごとの品番のプレフィクスとレーベルのそれとが等しくならない。

    Blu-ray版とDVD版がある作品はまとめられずにそれぞれ個別にカウントされる。

    品番のプレフィクスをまとめているが、これらは作品ページのURLから取得して
    おり、実際の品番と異なる場合がある。


引数:
IDまたはURL
    DMM上でのメーカーかレーベルのIDもしくはDMMでのその一覧ページ(IDが含まれる)
    URLを指定する。

オプション:
-t, --target {maker | label}
    ID指定の場合にメーカーかレーベルかを指定する。
    URL渡しのときは指定する必要なし(指定しても無視される)。

--service {dvd,rental,video,ama,all}
    取得するサービスを指定する。
    引数をURLで渡していれば指定不要。

-o, --outfile ファイル名
    一覧ウィキテキストを出力するファイル名を指定する。
    オプション未指定時は自動設定される。

-r, --replace
    一覧ウィキテキストの出力ファイル名と同名のファイルが存在する場合それを
    上書きする。

-p, --pickle-path
    保存した .pickle ファイルが格納されているディレクトリを指定する。
    未指定時は現在のディレクトリからさがす。

-l, --only-label
    レーベルの一覧だけ出力し、シリーズ一覧は出力しない。
    (データの矛盾を避けるため、内部でシリーズ情報の取得自体は行う)

-s, --only-series
    シリーズの一覧だけ出力し、レーベル情報は出力しない。

-u, --unsuppress
    「AVGP」や「AV OPEN」など、メーカーにまたがるめんどくさい仮レーベルの
    シリーズ情報も取得する。

-d, --without-dmm
    DMMの一覧ページヘのリンクを出力しない。

-a, --without-latest
    各レーベル/シリーズの最新リリース日を出力しない。

-e, --without-prefixes
    品番のプレフィクスの統計を出力しない

--regen-pid
    一旦生成した品番を再生成する。

-C, --clear-cache
    プログラム終了時にHTTPキャッシュをクリアする。

-v, --verbose
    デバッグ情報を出力する。

-V, --version
    バージョン情報を表示して終了する。

-h, --help
    ヘルプメッセージを表示して終了する。
"""
import argparse
import pickle
import time
from collections import Counter, OrderedDict
from pathlib import Path
from operator import itemgetter

import libssw

# import pdb

__version__ = 20151009

VERBOSE = 0

OWNNAME = libssw.ownname(__file__)
BASEURL = libssw.BASEURL

emsg = libssw.Emsg(OWNNAME)

# 配下のシリーズを取得しないレーベル
IGNORE_LABELS = ('AVGP',
                 'AV OPEN',
                 'AV30',
                 'AVopen',
                 'Onafes',
                 'D1グランプリ')

# 配下のシリーズを取得しないメーカーとレーベルの組み合わせ
IGNORE_PARES = {'40004':      # アイエナジー
                ('125',),     #     SOFT ON DEMAND

                '45276':      # SODクリエイト
                ('815',       #     COBRA(WAAP)
                 '30',        #     DEEP'S
                 '212'),      #     みるきぃぷりん
}

ROOTID = None
PREFIXES = True


verbose = None


def get_args():
    global VERBOSE
    global verbose

    argparser = argparse.ArgumentParser(
        description='メーカー配下の全レーベルの一覧、レーベル配下の全シリーズの一覧をウィキテキストで作成する')
    argparser.add_argument('root',
                           help='メーカー/レーベルのIDまたはDMMでのその一覧ページのURL',
                           metavar='ID')

    argparser.add_argument('-t', '--target',
                           help='IDがメーカーかレーベルかを指定する',
                           choices=('maker', 'label'),
                           default='maker')

    argparser.add_argument('--service',
                           help='取得するサービスを指定する',
                           choices=('dvd', 'rental', 'video', 'ama', 'all'),
                           default='dvd')
    argparser.add_argument('-o', '--outfile',
                           help='出力ファイル名を指定する(デフォルト名を変更する)',
                           metavar='FILE')
    argparser.add_argument('-r', '--replace',
                           help='一覧の出力ファイルと同名のファイルがあった場合上書きする',
                           action='store_true')

    argparser.add_argument('-p', '--pickle-path',
                           help='保存ファイルのパスを指定する')

    only = argparser.add_mutually_exclusive_group()
    only.add_argument('-l', '--only-label',
                      help='レーベル一覧だけ出力する',
                      action='store_true')
    only.add_argument('-s', '--only-series',
                      help='シリーズ一覧だけ出力する',
                      action='store_true')

    argparser.add_argument('--sort-key',
                           help='ソートキー',
                           choices=('release', 'name', 'number'),
                           default='release')

    argparser.add_argument('-u', '--unsuppress',
                           help='シリーズ一覧を作成しないよう指定されているレーベルに'
                           'ついても作成する',
                           action='store_false',
                           dest='suppress',
                           default=True)

    argparser.add_argument('-d', '--without-dmm',
                           help='DMMへのリンクを追加しない',
                           action='store_false',
                           dest='dmm',
                           default=True)
    argparser.add_argument('-a', '--without-latest',
                           help='最新リリース日を追加しない',
                           action='store_false',
                           dest='latest',
                           default=True)
    argparser.add_argument('-e', '--without-prefixes',
                           help='品番のプレフィクスの統計を出力しない',
                           dest='prefixes',
                           action='store_false',
                           default=True)

    argparser.add_argument('--regen-pid',
                           help='品番を再作成する',
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

    VERBOSE = args.verbose
    verbose = libssw.def_verbose(VERBOSE, libssw.ownname(__file__))
    verbose('verbose mode on')

    verbose('args: {}'.format(args))
    return args


def get_elems(props):
    resp, he = libssw.open_url(props['url'])
    if resp.status != 200:
        emsg('W', 'ページを取得できませんでした: '
             'url="{0[url]}", title={0[title]}, status={1}'.format(
                 props, resp.status))
        return False

    return he.xpath('//td[@class="nw"]')


def ret_idname(el):
    """作品の所属するレーベル/シリーズのIDと名称を返す"""
    e = el.getnext().xpath('a')
    return (libssw.get_id(e[0].get('href'))[0], e[0].text.strip()) if e \
        else (None, '')


class RetrieveMembers:
    def __init__(self, listparser, service):
        self.listparser = listparser
        self.service = service
        self.ophans = []
        self.ophans_prods = OrderedDict()
        self.ophans_prefix = Counter()

    def __call__(self, tier, newcomers, existings, last_pid):
        """レーベル/シリーズ情報を返す"""

        if tier == 'label':
            rname = 'メーカー'
            nwidx = 7
        else:
            rname = 'レーベル'
            nwidx = 5

        self.ophans.clear()
        self.ophans_prods.clear()
        self.ophans_prefix.clear()
        self.ophans_latest = '0000/00/00'

        queue = list(newcomers.keys())
        while queue:
            url = queue[-1]

            if url in existings or url in self.ophans:
                queue.pop()
                continue

            props = newcomers[url]
            verbose('popped: {}'.format(props.items()))
            libssw.inprogress('この{}残り: {}'.format(rname, len(queue)))

            # 作品ページを開いて要素を取得
            el = get_elems(props)
            if not len(el):
                queue.pop()
                continue

            # レーベル/シリーズIDと名前
            mid, mname = ret_idname(el[nwidx])
            mreldate = libssw.getnext_text(el[1])
            if not mid:
                self.ophans.append(url)
                self.ophans_prods[url] = props
                mprefix = libssw.split_pid(props['pid'])[0]
                self.ophans_prefix[mprefix] += 1
                verbose('ophans: {}'.format(props['pid']))

                if mreldate > self.ophans_latest:
                    self.ophans_latest = mreldate
                    verbose('ophans latest: {}'.format(self.ophans_latest))
                queue.pop()
                continue

            # 複数メーカーにまたがっていて扱いが面倒なレーベルは整理
            if tier == 'label' and \
               ROOTID in IGNORE_PARES and \
               mid in IGNORE_PARES[ROOTID]:
                verbose('ignore label: {}'.format(mname))
                queue.pop()
                continue

            priurls = libssw.join_priurls(tier, mid, service=self.service)

            # レーベル/シリーズの全作品情報の取得
            mprods = OrderedDict()
            for murl, mprops in libssw.from_dmm(self.listparser,
                                                priurls,
                                                key_id=last_pid,
                                                key_type='last',
                                                idattr='pid',
                                                ignore=True,
                                                show_info=False):
                if murl not in existings:
                    mprods[murl] = dict(mprops)

            if not mprods:
                return

            yield int(mid), mname, priurls[0], mprods.copy()

            for key in mprods:
                try:
                    queue.remove(key)
                except ValueError:
                    pass


def count_prefixes(prods):
    """品番プレフィクスの集計"""
    return Counter(libssw.split_pid(prods[p]['pid'])[0] for p in prods)


def get_latest(prods):
    """最新リリース作品のリリース日を返す"""
    item = next(iter(prods.values()))
    mel = get_elems(item)
    return libssw.getnext_text(mel[1])


def summ_prefixes(prefixes, fd):
    """品番プレフィクスのまとめ"""
    if not PREFIXES:
        return

    pfxstr = ', '.join('{} ({}作品)'.format(p, n)
                       for p, n in prefixes.most_common())
    total = sum(prefixes.values())
    print('-{}作品: {}'.format(total, pfxstr), file=fd)


def print_serises(keys, name, prefix, prods, url, latest, withdmm, withlatest,
                  sort_key, fd):
    """シリーズ情報の出力"""
    if sort_key == 'release':
        kiter = tuple((k, latest[k]) for k in keys)
        rev = True
    elif sort_key == 'name':
        kiter = tuple((k, name[k]) for k in keys)
        rev = False
    elif sort_key == 'number':
        kiter = tuple((k, len(prods[k])) for k in keys)
        rev = True

    for n, item in enumerate(sorted(kiter, key=itemgetter(1), reverse=rev),
                             start=1):
        sid = item[0]
        print('***{}.[[{}]]'.format(n, name[sid]), file=fd)
        summ_prefixes(prefix[sid], fd)
        if withlatest:
            print('-最新リリース: {}'.format(latest[sid]), file=fd)
        if withdmm:
            print('-[[DMMの一覧>{}]]'.format(url[sid]), file=fd)


def main():
    global ROOTID
    global PREFIXES

    existings = OrderedDict()
    newcomers = OrderedDict()

    mk_prefix = Counter()

    mk_ophans = []
    mk_ophans_prods = dict()
    mk_ophans_prefix = Counter()
    mk_ophans_latest = ''

    lb_newcomers = dict()

    lb_name = dict()
    lb_url = dict()
    lb_prods = dict()
    lb_prefix = Counter()
    lb_latest = dict()
    lb_series = dict()

    lb_ophans = dict()
    lb_ophans_prods = dict()
    lb_ophans_prefix = Counter()
    lb_ophans_latest = dict()

    sr_name = dict()
    sr_url = dict()
    sr_prods = dict()
    sr_prefix = Counter()
    sr_latest = dict()

    args = get_args()
    PREFIXES = args.prefixes

    if args.root.startswith('http://'):
        # IDがURL渡しだったときの対処
        ROOTID = libssw.get_id(args.root)[0]
        target = libssw.get_article(args.root)
        service = libssw.resolve_service(args.root)
    else:
        ROOTID = args.root
        target = args.target
        service = args.service
    verbose('root id: {}'.format(ROOTID))
    verbose('target: {}'.format(target))
    verbose('service: {}'.format(service))

    listparser = libssw.DMMTitleListParser(
        no_omits=('イメージビデオ', '総集編'), show_info=False)
    ret_members = RetrieveMembers(listparser, service)

    flprefix = '{}.{}'.format(target, ROOTID)
    pkfile = tuple(
        Path(args.pickle_path or '.').glob('{}.*.pickle'.format(flprefix)))
    pkfile = pkfile[0] if pkfile else None
    if pkfile:
        with pkfile.open('rb') as f:
            (existings,
             lb_name,
             lb_url,
             lb_prods,
             lb_latest,
             sr_name,
             sr_url,
             sr_prods,
             sr_latest,
             lb_series,
             lb_ophans,
             lb_ophans_prods,
             lb_ophans_latest,
             mk_ophans,
             mk_ophans_prods,
             mk_ophans_latest) = pickle.load(f)

    exist_set = set(existings)

    # 新規追加分を取得
    priurls = libssw.join_priurls(target, ROOTID, service=service)

    try:
        last_pid = next(reversed(existings.values()))['pid']
    except StopIteration:
        last_pid = None

    # メーカーの新規作品情報の取得
    for nurl, nprops in libssw.from_dmm(listparser, priurls,
                                        key_id=last_pid,
                                        key_type='last',
                                        idattr='pid',
                                        ignore=True):
        if nurl not in exist_set:
            newcomers[nurl] = dict(nprops)

    nc_num = len(newcomers)
    total = nc_num + len(existings)
    if not total:
        emsg('E', '検索結果は0件でした。')

    article_name = listparser.article[0][0]

    # メーカー名がわかったところで出力ファイルのチェック
    outstem = '{}.{}'.format(flprefix,
                             libssw.trans_filename(article_name))

    outfile = args.outfile or '{}.wiki'.format(outstem)
    if args.replace:
        writemode = 'w'
    else:
        libssw.files_exists('w', outfile)
        writemode = 'x'

    emsg('I', '{} [id={}, 新規{}/全{}作品]'.format(
        article_name, ROOTID, nc_num, total))

    # まずレーベル別にまとめ
    lb_set = set(lb_name)
    lb_set_add = lb_set.add
    for lid, lname, lurl, lprods in ret_members('label',
                                                newcomers,
                                                exist_set,
                                                last_pid):
        if lid not in lb_set:
            # 新規レーベル
            lb_name[lid] = lname
            lb_url[lid] = lurl
            lb_prods[lid] = lprods
            lb_series[lid] = []
            lb_set_add(lid)
        else:
            # 既知レーベルの新規作品
            for u in reversed(lprods):
                lb_prods[lid][u] = lprods[u]

        lb_newcomers[lid] = lprods
        lb_latest[lid] = get_latest(lprods)

        emsg('I', 'レーベル: {} [id={}, 新規{}作品]'.format(
            lname, lid, len(lprods)))

    #
    # メーカーその他作品まとめ
    #
    ncmk_ophans = ret_members.ophans.copy()
    ncmk_ophans_prods = ret_members.ophans_prods.copy()
    emsg('I', '{}その他: {}作品'.format(
        article_name, len(ncmk_ophans_prods)))

    # メーカーその他作品の追加
    mk_ophans.extend(ncmk_ophans)
    for u in reversed(ncmk_ophans_prods):
        mk_ophans_prods[u] = ncmk_ophans_prods[u]
    verbose('mk_ophans_prods: {}'.format(len(mk_ophans_prods)))

    # メーカーその他作品の品番およびプレフィクス
    if args.regen_pid:
        for p in mk_ophans_prods:
            mk_ophans_prods[p]['pid'] = libssw.gen_pid(mk_ophans_prods[p]['url'])[0]
    mk_ophans_prefix = count_prefixes(mk_ophans_prods)

    # メーカーその他作品の最新リリース日
    ncmk_ophans_latest = ret_members.ophans_latest
    if ncmk_ophans_latest > mk_ophans_latest:
        mk_ophans_latest = ncmk_ophans_latest

    #
    # レーベル別まとめ
    #
    # 新作情報を追加してレーベル全体のプレフィクス情報の再作成
    for lid in lb_prods:
        if args.regen_pid:
            for p in lb_prods[lid]:
                lb_prods[lid][p]['pid'] = libssw.gen_pid(lb_prods[lid][p]['url'])[0]
        lb_prefix[lid] = count_prefixes(lb_prods[lid])

    # レーベルごとにシリーズまとめ
    for lid in lb_prods:
        lprods = lb_prods[lid]

        if lb_name[lid].startswith(IGNORE_LABELS) and args.suppress:
            lb_series[lid] = ()
            lb_ophans_prefix[lid] = ()
            continue

        emsg('I', '')
        emsg('I', 'レーベル「{}」のシリーズ'.format(lb_name[lid]))

        verbose('exising ophans: {}'.format(len(lb_ophans.get(lid, ()))))
        sr_set = set(sr_name)
        sr_set_add = sr_set.add
        for sid, sname, surl, sprods in ret_members('series',
                                                    lprods,
                                                    exist_set,
                                                    last_pid):
            if sid not in sr_set:
                sr_name[sid] = sname
                sr_url[sid] = surl
                sr_prods[sid] = sprods
                sr_set_add(sid)
            else:
                for u in reversed(sprods):
                    sr_prods[sid][u] = sprods[u]
            emsg('I', 'シリーズ: {} [id={}, 新規{}作品]'.format(
                sname, sid, len(sprods)))

            sr_latest[sid] = get_latest(sprods)
            try:
                lb_series[lid].append(sid)
            except KeyError:
                lb_series[lid] = [sid]

        # レーベルその他作品まとめ
        nclb_ophans = ret_members.ophans.copy()
        nclb_ophans_prods = ret_members.ophans_prods.copy()
        emsg('I', '{}その他: {}作品'.format(
            lb_name[lid],  len(nclb_ophans_prods)))
        nclb_ophans_latest = ret_members.ophans_latest

        if lid not in lb_ophans:
            lb_ophans[lid] = []
            lb_ophans_prods[lid] = OrderedDict()
            lb_ophans_latest[lid] = '0000/00/00'

        lb_ophans[lid].extend(nclb_ophans)
        for u in reversed(nclb_ophans_prods):
            lb_ophans_prods[lid][u] = nclb_ophans_prods[u]
        verbose('lb_ophans_prods[{}]: {}'.format(lid, len(lb_ophans_prods)))
        nclb_ophans_latest = ret_members.ophans_latest
        if nclb_ophans_latest > lb_ophans_latest[lid]:
            lb_ophans_latest[lid] = nclb_ophans_latest

    verbose('lb_ophans_prods: {}'.format(lid, len(lb_ophans_prods)))
    for lid in lb_ophans_prods:
        verbose('lb_ophans_prods[{}]: {}'.format(lid, len(lb_ophans_prods[lid])))
        if args.regen_pid:
            for p in lb_ophans_prods[lid]:
                lb_ophans_prods[lid][p]['pid'] = libssw.gen_pid(
                    lb_ophans_prods[lid][p]['url'])[0]
        lb_ophans_prefix[lid] = count_prefixes(lb_ophans_prods[lid])
        verbose('lb_ophans_prefix[{}]: {}'.format(lid, len(lb_ophans_prefix[lid])))

    for sid in sr_prods:
        if args.regen_pid:
            for p in sr_prods[sid]:
                sr_prods[sid][p]['pid'] = libssw.gen_pid(sr_prods[sid][p]['url'])[0]
        sr_prefix[sid] = count_prefixes(sr_prods[sid])

    for url in reversed(newcomers):
        existings[url] = newcomers[url]
    mk_prefix = count_prefixes(existings)

    print('\n')

    fd = open(outfile, writemode)

    if target == 'maker':
        print('*[[{}（メーカー）]]'.format(article_name), file=fd)
        # print('全{}作品'.format(total), file=fd)
        summ_prefixes(mk_prefix, fd)
    print(time.strftime('(%Y年%m月%d日現在)'), file=fd)

    if args.sort_key == 'release':
        keyiter = lb_latest.items()
        reverse = True
    elif args.sort_key == 'name':
        keyiter = lb_name.items()
        reverse = False
    elif args.sort_key == 'number':
        keyiter = tuple((lid, len(lb_prods[lid])) for lid in lb_prods)
        reverse = True

    if not args.only_series:
        for n, item in enumerate(
                sorted(keyiter, key=itemgetter(1), reverse=reverse),
                start=1):
            lid = item[0]
            print('**{}.[[{}]]'.format(n, lb_name[lid]), file=fd)
            summ_prefixes(lb_prefix[lid], fd)

            if args.latest:
                print('-最新リリース: {}'.format(lb_latest[lid]), file=fd)

            if args.dmm:
                print('-[[DMMの一覧>{}]]'.format(lb_url[lid]), file=fd)

            if not args.only_label:
                # シリーズ別出力
                numofseries = len(lb_series.get(lid, ()))
                numofoph = len(lb_ophans_prefix.get(lid, ()))
                is_exist = numofseries or numofoph
                if is_exist:
                    print('[+]', file=fd)
                    print('シリーズ数:', numofseries, file=fd)

                try:
                    print_serises(lb_series[lid],
                                  sr_name, sr_prefix, sr_prods, sr_url,
                                  sr_latest,
                                  args.dmm, args.latest, args.sort_key, fd)
                except KeyError:
                    pass

                if numofoph:
                    print('***{}その他'.format(lb_name[lid]), file=fd)
                    summ_prefixes(lb_ophans_prefix[lid], fd)
                    if args.latest:
                        print('-最新リリース: {}'.format(lb_ophans_latest[lid]),
                              file=fd)

                if is_exist:
                    print('[END]', file=fd)

            print(file=fd)

        if mk_ophans:
            print('**{}その他'.format(article_name), file=fd)
            summ_prefixes(mk_ophans_prefix, fd)

            if args.latest:
                print('-最新リリース: {}'.format(mk_ophans_latest), file=fd)

    elif not args.only_label:
        """only-series"""
        print_serises(sr_name, sr_name, sr_prefix, sr_prods, sr_url, sr_latest,
                      args.dmm, args.latest, args.sort_key, fd)

    fd.close()

    print('出力ファイル:', outfile)

    if newcomers or args.regen_pid:
        pkpath = Path(args.pickle_path or '.') / '{}.pickle'.format(outstem)
        try:
            pkpath.rename(pkpath.with_suffix(pkpath.suffix + '.bak'))
        except FileNotFoundError:
            pass

        verbose('save file: {}'.format(pkpath))
        with pkpath.open('wb') as f:
            pickle.dump((existings,
                         lb_name,
                         lb_url,
                         lb_prods,
                         lb_latest,
                         sr_name,
                         sr_url,
                         sr_prods,
                         sr_latest,
                         lb_series,
                         lb_ophans,
                         lb_ophans_prods,
                         lb_ophans_latest,
                         mk_ophans,
                         mk_ophans_prods,
                         mk_ophans_latest),
                        f)

    # キャッシュディレクトリの削除
    if args.clear_cache:
        libssw.clear_cache()


if __name__ == '__main__':
    main()
