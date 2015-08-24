#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
素人系Wiki女優ページの移動(内部リンクの張り替え)

書式:
sswmv.py [移動先ページ名] [オプション ...]

'''
import sys
import re
import argparse
from itertools import chain
import libssw

__version__ = 20140812

VERBOSE = 0

OWNNAME = libssw.ownname(__file__)
verbose = libssw.Verbose(OWNNAME, VERBOSE)
emsg = libssw.Emsg(OWNNAME)


p_label = re.compile(r'\[\[(.+?)>')


def get_args():
    global VERBOSE

    argparser = argparse.ArgumentParser(
        description='素人系総合Wikiのページ移動用リンクの張替え')
    argparser.add_argument('moves_to',
                           help='移動先ページ名',
                           metavar='MOVES_TO')
    argparser.add_argument('-i', '--input',
                           help='ウィキテキストを格納したファイル(未指定で標準入力から入力)',
                           metavar='INPUT')
    argparser.add_argument('-o', '--out',
                           help='出力ファイル(未指定で標準出力へ出力)',
                           metavar='OUTPUT')
    argparser.add_argument('-r', '--replace',
                           help='出力ファイルと同名のファイルがあった場合上書きする',
                           action='store_true')

    argparser.add_argument('-d', '--diff',
                           help='データ修正前と後の差分をウェブブラウザで表示する',
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

    return args


def main():
    args = get_args()

    if args.out:
        if args.replace:
            writemode = 'w'
        else:
            libssw.files_exists('w', args.out)
            writemode = 'x'
    else:
        writemode = None

    fd = open(args.input, 'r') if args.input else sys.stdin
    header = fd.readline()
    verbose('header: ', header)
    body = fd.read()
    verbose('body len: ', len(body))
    if args.input:
        fd.close()

    current = body[:]

    labels = p_label.findall(header)
    names = chain.from_iterable(a.split('／') for a in labels)
    names = tuple(libssw.p_inbracket.split(name)[0] for name in names)
    emsg('I', 'names: ', names)

    fd = open(args.out, writemode) if args.out else sys.stdout
    for name in names:
        if name == args.moves_to:
            emsg('I', '[[{0}>.+]] → [[{0}]]'.format(name))
            body = re.sub(r'\[\[{}>.+?\]\]'.format(name),
                          '[[{}]]'.format(name),
                          body)
        else:
            emsg('I', '[[{0}>.+]] → [[{0}>{1}]]'.format(name, args.moves_to))
            emsg('I', '[[{0}]] → [[{0}>{1}]]'.format(name, args.moves_to))
            body = re.sub(r'\[\[{}>.+?\]\]'.format(name),
                          '[[{}>{}]]'.format(name, args.moves_to),
                          body)
            body = re.sub(r'\[\[{}\]\]'.format(name),
                          '[[{}>{}]]'.format(name, args.moves_to),
                          body)
    print(header, file=fd, end='')
    print(body, file=fd)
    if args.out:
        fd.close()

    if args.diff:
        libssw.show_diff(current.split('\n'),
                         body.split('\n'),
                         '修正前',
                         '修正後')


if __name__ == '__main__':
    main()
