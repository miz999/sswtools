#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
素人総合Wikiウィキテキスト(表形式)の要素の置き換え
対象のウィキテキストにない情報を置き換えデータで補完するか、
置き換えデータが存在する行を行ごと置き換える。

書式:
sswsubs.py [補完対象ファイル] -i 補完データファイル [ファイル ...]

説明:
    補完対象ファイルを指定しないと標準入力から読み込む。
    セルが結合されている表には未対応。
"""
import sys
import re
import argparse
import fileinput

import libssw

__version__ = 20151009

OWNNAME = libssw.ownname(__file__)

VERBOSE = 0

p_url = re.compile(r'^\|\[\[[A-Z0-9-]+>(http:.+?)\]\]')

emsg = libssw.Emsg(OWNNAME)


verbose = None


def get_args():
    """コマンドライン引数の解釈"""
    global VERBOSE
    global verbose

    argparser = argparse.ArgumentParser(
        description='ウィキテキスト(表形式)を補完または置き換え')
    argparser.add_argument('target',
                           help='対象のウィキテキストファイル名(未指定で標準入力)',
                           nargs='?',
                           type=argparse.FileType('r'),
                           default=sys.stdin,
                           metavar='TARGET')

    argparser.add_argument('-i', '--input',
                           help='補完・置き換えデータのファイル',
                           nargs='+',
                           dest='ifiles')
    argparser.add_argument('-o', '--out',
                           help='ファイルに出力 (未指定時は標準出力へ出力)',
                           metavar='FILE')
    argparser.add_argument('-r', '--replace',
                           help='出力ファイルと同名のファイルがあった場合上書きする',
                           action='store_true')

    argparser.add_argument('-f', '--force',
                           help='補完・置き換えファイルの内容で対象を強制的に置き換える',
                           action='store_true')
    argparser.add_argument('-a', '--actress',
                           help='出演者情報のみ置き換え・補完する',
                           action='store_true')
    argparser.add_argument('-p', '--other-page',
                           help='[[別ページ>]]のみ置き換える',
                           action='store_true')
    argparser.add_argument('-d', '--diff',
                           help='修正前と後の差分をウェブブラウザで表示する',
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

    verbose('args: ', (args))
    return args


def take(target, fromf, other, force):
    """情報の選択"""
    if other and fromf.strip().startswith('[[別ページ>'):
        taken = fromf
    else:
        taken = fromf or target if force else target or fromf

    return taken


def complement(target, from_d, args):
    """データの補完ジェネレータ"""
    TarCols = None

    for row in target:
        row = row.strip()

        if not TarCols and row.startswith('|~NO'):
            # カラム情報の取得
            TarCols = libssw.gen_ntfcols('TarCols', row)

        if not row.startswith('|[['):
            yield row
            continue

        url = p_url.findall(row)
        if not url:
            yield row
            continue

        url = url[0]
        verbose('url: ', url)

        rownt = TarCols(*row.split('|'))
        if url in from_d:
            if args.actress:
                mr = rownt._replace(
                    ACTRESS=take(rownt.ACTRESS, from_d[url].ACTRESS,
                                 args.other_page,
                                 args.force))
                mr = list(mr)
            else:
                mr = [take(getattr(rownt, c, ''),
                           getattr(from_d[url], c, ''),
                           args.other_page,
                           args.force)
                      for c in TarCols._fields]

            yield '|'.join(mr)

        else:
            yield row


def main():

    args = get_args()

    libssw.files_exists('r', *args.ifiles)
    if args.out:
        if args.replace:
            writemode = 'w'
        else:
            libssw.files_exists('w', args.out)
            writemode = 'x'
    else:
        writemode = None

    target = args.target.readlines()
    args.target.close()

    from_d = dict()
    FromCols = None
    # 置き換え情報辞書の作成
    with fileinput.input(files=args.ifiles) as f:
        for row in f:
            row = row.strip()
            if not FromCols and row.startswith('|~NO|'):
                # カラム情報の取得
                FromCols = libssw.gen_ntfcols('FromCols', row)

            if not row.startswith('|[['):
                continue

            url = p_url.findall(row)[0]
            from_d[url] = FromCols(*row.split('|'))

    result = tuple(complement(target[:], from_d, args))

    fd = open(args.out, writemode) if args.out else sys.stdout
    print()
    print(*result, sep='\n', file=fd)
    if args.out:
        fd.close()

    if args.diff:
        libssw.show_diff(target, result, '修正前', '修正後')


if __name__ == '__main__':
    main()
