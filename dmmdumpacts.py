#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
DMM女優DBから名前情報をダンプ
'''
import os
import argparse
import sqlite3
import time
import shutil
from itertools import chain
from tempfile import TemporaryDirectory, gettempdir

from dmmretacts import Profile
import libssw

OWNNAME = libssw.ownname(__file__)

PRODURL = 'http://www.dmm.co.jp/mono/dvd/-/list/=/article=actress/id={}/'
ACTURL = 'http://actress.dmm.co.jp/-/detail/=/actress_id={}/'


emsg = libssw.Emsg(OWNNAME)


def get_args():
    '''
    コマンドライン引数の解釈
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('path',
                        help='DBのパス',
                        type=str,
                        nargs='?')

    parser.add_argument('-n', '--names',
                        help='名前と読みリスト',
                        action='store_true')
    parser.add_argument('-i', '--info',
                        help='女優情報リスト',
                        action='store_true')
    parser.add_argument('-b', '--both',
                        help='両方 (default)',
                        action='store_true')

    parser.add_argument('-s', '--start',
                        help='開始IDを指定',
                        type=int)
    parser.add_argument('-l', '--limit',
                        help='処理数上限を指定',
                        type=int)
    parser.add_argument('-d', '--stdout',
                        help='標準出力に出力',
                        action='store_true')
    parser.add_argument('-o', '--overwrite',
                        help='既存のファイルを置き換える',
                        action='store_true')

    args = parser.parse_args()

    if args.both or not (args.names and args.info):
        args.names = args.info = True

    if args.stdout and args.names and args.info:
        emsg('E', 'Specified both outouts to stdout.')

    for a in ('start', 'limit'):
        num = getattr(args, a, None)
        if num and not (isinstance(num, int) and num > 0):
            emsg('E', 'Parameter "{}" must be positive integer'.format(a))

    return args


def main():

    args = get_args()

    cwd = os.getcwd()
    db_path = args.path or os.path.join(cwd, 'dmm_actress.db')
    if not os.path.exists(db_path):
        emsg('E', 'Database file not found')

    tmpdir = TemporaryDirectory(dir=gettempdir())
    tmpdb_path = shutil.copy(db_path, tmpdir.name)
    os.chdir(tmpdir.name)

    conn = sqlite3.connect(tmpdb_path)
    cur = conn.cursor()

    cur.execute('select max(id) from main')
    id_max = cur.fetchone()[0]
    id_len = len(str(id_max))

    startid = args.start or 1

    if args.stdout:
        onames = oinfo = None
    else:
        if args.names:
            fname = 'dmm_actress_names-{}.txt'.format(time.strftime('%Y%m%d'))
            onames = open(fname, 'w' if args.overwrite else 'x',
                          encoding='utf-8', newline='\r\n')
        if args.info:
            finfo = 'dmm_actress_info-{}.txt'.format(time.strftime('%Y%m%d'))
            oinfo = open(finfo, 'w' if args.overwrite else 'x',
                         encoding='utf-8', newline='\r\n')
            print('ID\t名前\t誕生日\t星座\t血液型\t'
                  '身長\tバスト\tカップ\tウエスト\tヒップ\t'
                  '出身地\t趣味・特技', file=oinfo)

    id_cur = conn.cursor()
    sql_i = '''select id,current,birthday,starsign,bloodtype,
                      height,bust,cup,waist,hip,hometown,hobby
               from main_view
               where deleted is null and current is not null and
                     id >= ? order by id '''
    if args.limit:
        id_cur.execute(sql_i + 'limit ?', (startid, args.limit))
    else:
        id_cur.execute(sql_i, (startid,))

    totalcnt = 0

    for act_info in id_cur:
        totalcnt += 1
        profile = Profile(*act_info)
        print('{}/{}'.format(profile.actid, id_max), end='\r')

        names = []
        for r in conn.execute(
                'select name, yomi, current from names where id=? ',
                (profile.actid,)):
            if r[2] == 'C':
                names.insert(0, r[:-1])
            else:
                names.append(r[:-1])
        assert all(names), 'Patchy data: {}'.format(names)

        url = PRODURL.format(profile.actid)

        if args.names:
            # 名前と読み情報
            namestr = '\t'.join(chain.from_iterable(names))
            print('{:>{}}\t{}\t{}'.format(profile.actid, id_len, namestr, url),
                  file=onames)

        if args.info:
            # 女優情報
            namestr = '{0[0]} ({0[1]})'.format(names[0])
            if len(names) > 1:
                namestr += ', ' + ', '.join(
                    '{} ({})'.format(n, y) for n, y in names[1:])
            profile.current = namestr
            plist = '\t'.join(str(a) if a else '' for a in profile.values())
            print('{}\t{}'.format(plist, url), file=oinfo)

    if not args.stdout:
        if args.names:
            onames.close()
            shutil.move(fname, cwd)
        if args.info:
            oinfo.close()
            shutil.move(finfo, cwd)

    id_cur.close()
    cur.close()
    tmpdir.cleanup()

    emsg('I', '**************************************')
    emsg('I', ' Proccessed total : {}'.format(totalcnt))
    emsg('I', '**************************************')


if __name__ == '__main__':
    main()
