#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
DMM上の女優情報の取得やチェック
'''

import os
import re
import argparse
import sqlite3
from tempfile import gettempdir
from itertools import zip_longest, count
from shutil import rmtree

import libssw

OWNNAME = libssw.ownname(__file__)
emsg = libssw.Emsg(OWNNAME)

CACHEDIR = gettempdir() + '/dmm_ret_cache'

PRODURL = 'http://www.dmm.co.jp/mono/dvd/-/list/=/article=actress/id={}/'
ACTURL = 'http://actress.dmm.co.jp/-/detail/=/actress_id={}/'

VOIDS = 100  # エラーページ(404など)が連続した場合の処理中止基準

PROCESSED = 0
TOTALCNT = 0
VOIDCNT = 0
MAXVOIDS = 0

BLOODTYPE = dict()
HOMETOWN = dict()
STARSIGN = dict()

p_birthday = re.compile(r'(?P<year>\d{4})年(?P<month>\d+)月(?P<day>\d+)日')
p_size = re.compile(r'''(?:T(?P<height>\d+)cm)?\ *
                        (?:B(?P<bust>\d+)cm)?\ *
                        (?:\((?P<cup>[A-Z])カップ\))?\ *
                        (?:W(?P<waist>\d+)cm)?\ *
                        (?:H(?P<hip>\d+)cm)?''', re.X)


class Profile:
    '''
    女優情報用クラス
    '''
    __slots__ = ('actid', 'current', 'birthday', 'starsign', 'bloodtype',
                 'height', 'bust', 'cup', 'waist', 'hip',
                 'hometown', 'hobby', 'retired', 'deleted')

    def __init__(self,
                 actid=None,
                 current=None,
                 birthday=None,
                 starsign=None,
                 bloodtype=None,
                 height=None,
                 bust=None,
                 cup=None,
                 waist=None,
                 hip=None,
                 hometown=None,
                 hobby=None,
                 retired=None,
                 deleted=None):
        self.actid = actid
        self.current = current
        self.birthday = birthday
        self.starsign = starsign
        self.bloodtype = bloodtype
        self.height = height
        self.bust = bust
        self.cup = cup
        self.waist = waist
        self.hip = hip
        self.hometown = hometown
        self.hobby = hobby
        self.retired = retired
        self.deleted = deleted

    def __call__(self, *args):
        attrs = args or self.__slots__
        return list((a, getattr(self, a)) for a in attrs)

    def values(self, *args):
        attrs = args or self.__slots__
        return list(getattr(self, a) for a in attrs)


class IsPositive:
    '''
    argparseのchoises用に作ったけど意味なかった。
    in 演算子で比較された時に値が正の整数ならTrueをそれ以外ならFalseを返す。
    ついでに関数呼び出しも。
    '''
    def is_positive(self, item):
        return isinstance(item, int) and item > 0

    def __contains__(self, item):
        return self.is_positive(item)

    def __call__(self, item):
        return self.is_positive(item)


class QuitException(Exception):
    '''
    解析終了例外
    '''
    def __init__(self):
        pass


def ask(p, choices=tuple(), num=None):
    '''
    選択肢の入力
    p プロンプト文字列
    choices 選択肢 (英文字)
    num 数値入力の有無 None でなければ入力できる最大値
    '''
    is_num = False

    choices = tuple(c.upper() for c in choices)

    while True:

        reply = input('\033[1;35m{}\033[0m'.format(p))

        if reply.isdecimal():
            norm = int(reply)
            if num and norm > num:
                print('Out of range')
                continue
            is_num = True
        else:
            norm = reply.upper()

        if (norm in choices) or (is_num and num):
            return norm


def get_args():
    '''
    コマンドライン引数の解釈
    '''
    parser = argparse.ArgumentParser()

    parser.add_argument('command',
                        help='newcomer (新規データの有無をチェック, default), '
                        'recheck (既知データを照合), '
                        'unused (既知データ間の欠番を再チェック)',
                        nargs='?',
                        default='newcomer')

    parser.add_argument('-s', '--start',
                        help='開始IDを指定',
                        type=int)

    id_range = parser.add_mutually_exclusive_group()
    id_range.add_argument('-l', '--limit',
                          help='全処理数上限を指定',
                          type=int)
    id_range.add_argument('-e', '--end',
                          help='終了IDを指定',
                          type=int)

    parser.add_argument('-v', '--void',
                        help='エラーページが連続した場合の処理上限 (default {})'.format(VOIDS),
                        type=int)

    parser.add_argument('-a', '--all-yes',
                        help='Answer all yes',
                        action='store_true')

    parser.add_argument('-r', '--reverse',
                        help='降順にチェック',
                        action='store_true')
    parser.add_argument('-d', '--db',
                        help='DBのパス',
                        type=str)

    parser.add_argument('-x', '--max',
                        help='最大IDを出力して終了',
                        action='store_true')
    parser.add_argument('-t', '--count',
                        help='有効データ件数を表示して終了',
                        action='store_true')

    parser.add_argument('-c', '--clear-cache',
                        help='プログラム終了時にHTTPキャッシュをクリアする',
                        action='store_true')

    args = parser.parse_args()

    if args.command in ('n', 'new', 'ne'):
        args.command = 'newcomer'
    elif args.command in ('r', 're', 'rc'):
        args.command = 'recheck'
    elif args.command in ('u', 'un', 'uu'):
        args.command = 'unused'

    for a in ('start', 'end', 'limit', 'void'):
        num = getattr(args, a, None)
        if num and num not in IsPositive():
            emsg('E', 'Parameter "{}" must be positive integer'.format(a))

    if args.limit and args.limit > 9999:
        emsg('E', 'Limit "{}" is too large.'.format(args.limit))

    return args


def gen_ref_data(conn):
    '''
    マスターDBから逆引き辞書の作成
    '''
    global BLOODTYPE
    global STARSIGN
    global HOMETOWN

    cur = conn.cursor()

    # 血液型
    cur.execute('select bloodtype, name from bloodtype_master')
    BLOODTYPE = {m[1]: m[0] for m in cur}

    # 星座
    cur.execute('select starsign, name from starsign_master')
    STARSIGN = {m[1]: m[0] for m in cur}

    # 出身地
    cur.execute('select hometown, name from hometown_master')
    HOMETOWN = {m[1]: m[0] for m in cur}

    cur.close()


def add_hometown(conn, place):
    '''
    未登録出身地名の追加
    '''
    global HOMETOWN

    emsg('W', '>>> Unknown hometown found : {}'.format(place))
    with conn:
        conn.execute('insert into hometown_master(name) values(?)',
                     (place,))
    # 出身地逆引き辞書への追加
    htid = conn.execute('select hometown from hometown_master where name=?',
                        (place,)).fetchone()[0]
    HOMETOWN[place] = htid
    emsg('W', '>>> place "{}" has been added into hometown'.format(place))

    return htid


def unused_id_range(conn, start_id, end_id):
    '''
    既存IDを少しずつ取得しながら
    未使用のIDをyieldするジェネレータ
    開始および終了ID指定
    '''
    fetchsize = 1000
    ids = (0,)
    cur = conn.cursor()

    for cand in range(start_id, end_id):
        if cand > ids[-1]:
            cur.execute(
                'select id from main where id >= ? order by id limit ?',
                (cand, fetchsize))
            ids = tuple(i for (i,) in cur)

        if cand not in ids:
            yield cand

    cur.close()


def unused_id_limit(conn, start_id, limit, rev=False):
    '''
    既存IDを少しずつ取得しながら
    未使用のIDをyieldするジェネレータ
    処理数上限指定
    '''
    fetchsize = 1000
    ids = (0,)
    cand = start_id
    cnt = 1
    id_len = 0
    cur = conn.cursor()

    if rev:
        sql = 'select id from main where id <= ? order by id desc limit ?'
        ac = -1
    else:
        sql = 'select id from main where id >= ? order by id asc limit ?'
        ac = 1

    while cnt < limit:
        if id_len == 0:
            cur.execute(sql, (cand, fetchsize))
            ids = tuple(i for (i,) in cur)
            id_len = len(ids)

        if cand not in ids:
            yield cand
            cnt += 1

        cand += ac
        id_len -= 1

    cur.close()


class DmmActressParser():
    '''
    HTMLの解析
    '''
    def __init__(self, conn):
        self.conn = conn

    def get_profile(self, tr):
        '''プロフィールの取得'''
        label = tr[0].text.strip()
        data = tr[1].text

        if data:
            data = data.strip().strip('-')

        if not data:
            return

        if label == '生年月日 ：':
            bi = p_birthday.search(data).groups()
            self.profile.birthday = '{0[0]}-{0[1]:0>2}-{0[2]:0>2}'.format(bi)

        elif label == '星座 ：':
            self.profile.starsign = STARSIGN[data]

        elif label == '血液型 ：':
            self.profile.bloodtype = BLOODTYPE[data]

        elif label == 'サイズ ：':
            size = p_size.search(data)

            if not any(data):
                # data が空文字ではないのに None しか見つからなければ検出失敗
                emsg('E', 'Could not catch size data : {}'.data)

            if size.group('height'):
                self.profile.height = int(size.group('height'))
            if size.group('bust'):
                self.profile.bust = int(size.group('bust'))
            if size.group('cup'):
                self.profile.cup = size.group('cup')
            if size.group('waist'):
                self.profile.waist = int(size.group('waist'))
            if size.group('hip'):
                self.profile.hip = int(size.group('hip'))

        elif label == '出身地 ：':
            if data in HOMETOWN:
                self.profile.hometown = HOMETOWN[data]
            else:
                self.profile.hometown = add_hometown(self.conn, data)

        elif label == '趣味・特技 ：':
            self.profile.hobby = data

    def feed(self, he, actid):
        self.profile = Profile()
        self.profile.actid = actid

        self.name, self.yomi = libssw.get_actname(he)
        self.profile.current = libssw.get_actname.current

        p_el = he.find_class('area-av30')[0].xpath('td[2]/table[1]')[0]
        for tr in p_el:
            self.get_profile(tr)


def recheck(conn, parser, args, startid, lastid):
    '''
    既存データと照合
    '''
    global PROCESSED
    global TOTALCNT

    def ask_deleted(cur, actid):
        '''
        削除フラグ立て
        '''
        reply = ask(' Flag as "deleted"? (y/n/q) ', 'YNQ')

        if reply == 'N':
            return False
        elif reply == 'Q':
            emsg('E')

        cur.execute('update main set deleted="D" where id=?', (actid,))
        emsg('W', '>>> data replaced')
        return True

    def ask_replace(cur, db, web, actid):
        '''
        データ置き換え
        '''
        nonlocal all_yes
        nonlocal all_yes_for_her

        reply = ask(' Replace db data with web? (y/n/a/t/q) ', 'YNATQ') \
            if not (all_yes or all_yes_for_her) else 'Y'

        if reply == 'N':
            return
        elif reply == 'Q':
            emsg('E')

        cur.execute(
            'update main set {}=? where id=?'.format(db[0]), (web[1], actid))
        emsg('W', '>>> data replaced')

        if reply == 'A':
            all_yes = True
        elif reply == 'T':
            all_yes_for_her = True

    def ask_insert_newname(cur, web_name, actid, current):
        '''
        新規名前登録
        '''
        for i, name in enumerate(web_name, start=1):
            emsg('W', '>>> New name: {} "{}"'.format(i, name))

        reply = ask('Insert new name? (y/n/q/<num>) ', 'YNQ', len(web_name))

        if reply == 'N':
            return
        elif reply == 'Q':
            emsg('E')

        for j, web in enumerate(web_name):
            if not all(web):
                emsg('E', 'Missing data:{}'.format(web))

            cur.execute(
                'select name from names where id=? and current="C"', (actid,))
            c_curr = cur.fetchone()

            if c_curr:
                cur.execute(
                    'update names set current=null where id=? and name=?',
                    (actid, c_curr[0]))

            cur.execute(
                'insert into names values(?,?,?,?,?)',
                (actid, web[0], web[1],
                 "C" if web[0] == current or j == reply else None,
                 None))

        emsg('W', '>>> New name added')

    cur = conn.cursor()
    id_cur = conn.cursor()

    sqlbase = 'select id,current,birthday,starsign,bloodtype,' \
              '       height,bust,cup,waist,hip,hometown,hobby ' \
              'from main where deleted is null and '

    if args.end:
        sql = sqlbase + 'id between ? and ? order by id'
        ph = (startid, args.end)
    else:
        if args.reverse:
            sql = sqlbase + 'id <= ? order by id desc'
        else:
            sql = sqlbase + 'id >= ? order by id'

        if args.limit:
            sql += ' limit ?'
            ph = (startid, args.limit)
        else:
            ph = (startid,)

    id_cur.execute(sql, ph)
    id_iter = tuple(i for i in id_cur)
    all_yes = args.all_yes

    # for act_info in id_cur:
    for act_info in id_iter:

        profile = Profile(*act_info)

        actid = profile.actid
        emsg('I', 'id: {}'.format(actid))

        TOTALCNT += 1
        emsg('I', ' totalcnt: {}'.format(TOTALCNT))
        if args.limit:
            emsg('I', ' {} id(s) rest'.format(args.limit - TOTALCNT))

        emsg('I', '>>> r: {}'.format(act_info))

        # ページの採取
        resp, he = libssw.open_url(ACTURL.format(actid))
        if resp.status == 404:
            # 既知の情報が削除されてたら削除フラグを設定
            emsg('W', '>>> id {} ({}) has been deleted from DMM.'.format(
                actid, profile.current))
            cur.execute('update main set deleted="D" where id=?', (actid,))
            continue
        elif resp.status != 200:
            emsg('W', '>>> Error on id {}: status={}'.format(actid,
                                                             resp.status))
            continue

        # HTMLの解析
        parser.feed(he, actid)

        #
        # DB上とWebページ上の基本情報の食い違いチェック
        #
        all_yes_for_her = False
        for db, web in zip(profile(), parser.profile()):
            # db == web == (属性名, データ)

            # この項目がまったく同じなら次へ
            if db[1] == web[1]:
                continue

            # この項目に変更あり
            emsg('W', '>>> Profile is different')
            emsg('W',
                 '...  {}: db={}, web={}'.format(db[0], db[1], web[1]))

            if db[0] == 'current' and web[1].startswith('このIDは'):

                # 女優情報が削除
                if ask_deleted(cur, actid):
                    continue

            else:

                # データの置き換え
                ask_replace(cur, db, web, actid)

        #
        # 名前と読みデータの食い違いチェック
        #
        cur.execute('select name, yomi from names where id=? order by name',
                    (actid,))
        db_name = cur.fetchall()
        web_name = sorted(zip_longest(parser.name, parser.yomi))

        if db_name == web_name:
            continue

        for db in db_name:
            # データの修正による食い違いかどうかチェック
            # (DBデータ内に現在のエントリが存在すればそれを取り除いていく)
            if db in web_name:
                web_name.remove(db)

        web_name = tuple(wn for wn in web_name
                         if not wn[0].startswith('このIDは'))
        if web_name:
            # DBにない名前があれば追加
            emsg('W', '>>> Name data mismatched.')
            ask_insert_newname(cur, web_name, actid, parser.profile.current)

        conn.commit()
        PROCESSED += 1

    id_cur.close()
    cur.close()


def newcomer(conn, parser, args, startid, lastid, voidlimit):
    '''
    新規データチェック
    '''
    global PROCESSED
    global TOTALCNT
    global VOIDCNT
    global MAXVOIDS

    cur = conn.cursor()

    if args.command == 'newcomer':
        # 新規番号チェック用ジェネレータ作成
        if args.limit:
            # 処理数上限
            endid = startid + args.limit
            id_iter = range(startid, endid)
            # ID上限
        elif args.end:
            endid = args.end
            id_iter = range(startid, endid)
        else:
            # 終了は voidlimit 依存
            id_iter = count(startid)
            endid = None
    else:
        # 欠番再チェック用ジェネレータ作成
        if args.limit:
            # 処理数上限
            endid = startid + args.limit
            id_iter = unused_id_limit(conn, startid, args.limit, args.reverse)
        else:
            if args.end:
                # ID上限 lastidより大きいならlastidで
                endid = args.end if args.end <= lastid else lastid
            else:
                endid = lastid
            id_iter = unused_id_range(conn, startid, endid)

    for actid in id_iter:
        emsg('I', 'id : {}'.format(actid))

        TOTALCNT += 1
        emsg('I', ' totalcnt: {}'.format(TOTALCNT))
        if args.limit:
            emsg('I', ' {} id(s) rest'.format(args.limit - TOTALCNT))

        #
        # ページの採取
        #
        resp, he = libssw.open_url(ACTURL.format(actid))
        if resp.status != 200:
            # エラーページ(404など)時の扱い
            emsg('W', '>>> Error on id {}: status={}'.format(actid,
                                                             resp.status))
            if args.command == 'newcomer':
                VOIDCNT += 1
                if VOIDCNT > 1:
                    emsg('W', '>>> {} empties in a row'.format(VOIDCNT))
                if VOIDCNT > MAXVOIDS:
                    MAXVOIDS = VOIDCNT
                if VOIDCNT >= voidlimit:
                    break
            continue
        else:
            # 女優ページ発見
            VOIDCNT = 0
            if args.command == 'newcomer':
                lastid = actid
            else:
                emsg('W', 'New comer found!')

        #
        # HTMLの解析
        #
        parser.feed(he, actid)

        if not parser.profile.actid:
            emsg('E', '>>> Data retrieving failed:{}, {}'.format(
                parser.profile.actid, parser.profile.current))

        if parser.profile.current.startswith('このIDは'):
            parser.profile.deleted = 'D'

        # 女優基本情報のDB書き込み
        emsg('I', '>>> profile: {}'.format(parser.profile.values()))
        cur.execute(
            'insert into main values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,null)',
            parser.profile.values())

        # 女優名と読みの組み合わせのDB書き込み
        # 先頭の要素を現在の名前とする
        for na, yo, cr in zip_longest(parser.name, parser.yomi, ('C',)):
            emsg('I', '>>> n: {}  y: {} {}'.format(na, yo, cr))
            cur.execute('insert into names values(?,?,?,?,null)',
                        (parser.profile.actid, na, yo, cr))

        conn.commit()
        PROCESSED += 1

    cur.close()
    return lastid


def main():

    args = get_args()

    db_path = args.db or os.path.join(os.getcwd(), 'dmm_actress.db')
    if not os.path.exists(db_path):
        emsg('E', 'Database file not found')

    conn = sqlite3.connect(db_path)

    lastid = conn.execute('select max(id) from main').fetchone()[0]

    if args.max:
        emsg('I', 'Max ID: {}'.format(lastid))
        raise SystemExit()

    if args.count:
        recn = conn.execute(
            'select count(*) from main '
            'where deleted is null and current is not null').fetchone()[0]
        emsg('I', 'Actual records: {}'.format(recn))
        raise SystemExit()

    if args.start and args.end and args.start > args.end and not args.reverse:
        # 明らかに逆順しなければならないのに指定がないとき強制変更
        args.reverse = True

    parser = DmmActressParser(conn)

    gen_ref_data(conn)

    if args.start:
        if args.command == 'newcomer':
            # 新規番号チェック時に開始IDがラスト以前の場合強制的にラスト+1へ
            startid = args.start if lastid <= args.start else lastid + 1
        else:
            startid = args.start
    else:
        # 新規番号チェックならラスト+1、それ以外なら1
        if args.command == 'newcomer':
            startid = lastid + 1
        elif args.reverse:
            startid = lastid
        else:
            startid = 1

    voidlimit = args.void or VOIDS
    emsg('I', '>>> voidlimit: {}'.format(voidlimit))

    if args.reverse:
        emsg('I', '>>> reverse mode')

    if args.command == 'recheck':
        # 既存データの照合
        recheck(conn, parser, args, startid, lastid)
    else:
        # 新規データのチェック
        lastid = newcomer(conn, parser, args, startid, lastid, voidlimit)

    emsg('I', '**************************************')
    emsg('I', ' Actual record(s): {}'.format(PROCESSED))
    emsg('I', ' Last ID: {}'.format(lastid))
    if MAXVOIDS:
        emsg('I', ' Max void(s) in a row: {}'.format(MAXVOIDS))

    if not args.command == 'unused' and voidlimit <= VOIDCNT <= TOTALCNT:
        emsg('W', ' voidcnt limit reached')
    emsg('I', '**************************************')

    # キャッシュディレクトリの削除
    if args.clear_cache:
        rmtree(CACHEDIR, ignore_errors=True)


if __name__ == '__main__':
    main()
