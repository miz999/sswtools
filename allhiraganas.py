#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
ひらがなのみの女優名の採取

名前がひらがなのみで5文字未満で、DVDセルおよびレンタル最新作のリリース(わかるかぎり総集編除く)が
1年以内の女優名をリストアップ
'''
import sqlite3
import argparse
import os

from datetime import date, timedelta

import libssw
import dmm2ssw


VERBOSE = 0

OWNNAME = libssw.ownname(__file__)
verbose = libssw.Verbose(OWNNAME, VERBOSE)
emsg = libssw.Emsg(OWNNAME)


ACTURL_BASE = libssw.ACTURL_BASE
ACTURL = libssw.ACTURL


def get_args():
    global VERBOSE
    global verbose

    argparser = argparse.ArgumentParser()
    argparser.add_argument('-i', '--id',
                           help='女優ID',
                           nargs='+')
    argparser.add_argument('-p', '--path',
                           help='DBのパス')
    argparser.add_argument('-s', '--selfcheck',
                           help='最終リリースを自身で再チェック',
                           action='store_true')
    argparser.add_argument('-v', '--verbose',
                           help='デバッグ用情報を出力する',
                           action='count',
                           default=0)

    args = argparser.parse_args()

    verbose.verbose = VERBOSE = args.verbose

    if not VERBOSE:
        verbose = libssw.verbose = lambda *x: None
    elif VERBOSE > 1:
        libssw.VERBOSE = libssw.verbose.verbose = \
            dmm2ssw.VERBOSE = dmm2ssw.verbose.verbose = VERBOSE - 1
        verbose('verbose mode on')

    return args


def select_allhiragana(ids, today, path, selfcheck):
    no_omits = libssw.gen_no_omits((0, 4))

    dmmparser = dmm2ssw.DMMParser(no_omits=no_omits,
                                  deeper=False,
                                  pass_bd=True,
                                  quiet=True)
    conn = sqlite3.connect(path)
    cur = conn.cursor()

    if ids:
        sql = 'select id,current,last_release from main where id in({}) '.format(
            ','.join('?' * len(ids)))
        ph = [sql, ids]
    else:
        sql = 'select id,current,last_release from main ' \
              'where last_release is not null and ' \
              'retired is null and deleted is null '
        ph = []

    if not selfcheck:
        ayearago = str(today - timedelta(days=365))
        sql += 'and last_release > ?'
        ph.append(ayearago)

    print('sql:', sql, ', ph:', ph)

    for aid, name, last_release in filter(
            lambda n: not libssw.p_neghirag.search(n[1]) and len(n[1]) < 5,
            cur.execute(sql, ph)):
        verbose(aid, name)
        print(aid, name + ': ', end='')
        url = 'http://actress.dmm.co.jp/-/detail/=/actress_id={}/'.format(aid)
        verbose('url: ', url)

        if not selfcheck:
            # 自分でチェックしないなら名前を返すだけ
            print('({})'.format(last_release))
            yield name
            continue

        resp, he = libssw.open_url(url)

        while he is not None:
            info = he.find('.//td[@class="info_works1"]')
            if info is None:
                print('negative')
                continue

            for tr in info.getparent().getparent()[1:]:
                title = tr.find('td/a').text
                verbose('title: ', title)

                if tr[4].text == '---' and tr[6].text == '---':
                    verbose('Not DVD and Rental')
                    continue

                sale = tr[4].find('a')
                rental = tr[6].find('a')
                prod_url = sale.get('href') if sale is not None else rental.get('href')
                verbose('prod url: ', prod_url)
                cid = libssw.get_id(prod_url, cid=True)[0]

                if libssw.check_omit(title, cid, no_omits=no_omits):
                    continue

                b, status, values = dmm2ssw.main(
                    props=libssw.Summary(url=prod_url),
                    p_args=argparse.Namespace(fastest=True, hide_list=True),
                    dmmparser=dmmparser)
                if status in ('Omitted', 404):
                    verbose('Omitted: status=', status, ', values=', values)
                    continue

                last_web = tr[7].text.strip()
                if last_release != last_web:
                    print('last_rel is different (db:{} <=> web:{}), '.format(
                        last_release, last_web),
                          end='')
                datelast = date(*(int(d) for d in last_web.split('-')))

                if (today - datelast).days < 366:

                    yield name
                    print('\033[1;33mpositive ({})\033[0m'.format(last_web))

                else:
                    print('negative ({})'.format(last_web))

                he = None
                break

            else:
                mu = he.get_element_by_id("mu").xpath('table[last()]//a')
                if len(mu) and mu[-1].text == '次へ':
                    resp, he = libssw.open_url(ACTURL_BASE + mu[-1].get('href'))
                else:
                    print('negative')
                    break

    conn.close()


def main():

    args = get_args()

    dbpath = args.path or 'dmm_actress.db'
    if not os.path.exists(dbpath):
        emsg('DB file not found')

    today = date.today()

    positive = set(select_allhiragana(args.id, today, dbpath, args.selfcheck))
    print('# 1年以内にリリース実績のある実在するひらがなのみで4文字以下の名前 ({}現在)'.format(
        str(today)))
    print('_allhiraganas = ', end='')
    print(tuple(sorted(positive)))


if __name__ == '__main__':
    main()
