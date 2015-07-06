#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
ひらがなのみの女優名の採取

名前がひらがなのみで5文字未満で、DVDセルおよびレンタル最新作のリリース(わかるかぎり総集編除く)が
1年以内の女優名をリストアップ
'''
import sqlite3
import argparse

from datetime import date

import libssw
import dmm2ssw


VERBOSE = 0

OWNNAME = libssw.ownname(__file__)
verbose = libssw.Verbose(OWNNAME, VERBOSE)
emsg = libssw.Emsg(OWNNAME)


def get_args():
    global VERBOSE

    argparser = argparse.ArgumentParser()
    argparser.add_argument('-i', '--id',
                           help='女優ID',
                           nargs='+')
    argparser.add_argument('-p', '--path',
                           help='DBのパス')
    argparser.add_argument('-v', '--verbose',
                           help='デバッグ用情報を出力する',
                           action='count',
                           default=0)

    args = argparser.parse_args()

    verbose.verbose = VERBOSE = args.verbose

    if args.verbose > 1:
        libssw.VERBOSE = libssw.verbose.verbose = \
            dmm2ssw.VERBOSE = dmm2ssw.verbose.verbose = args.verbose - 1
    verbose('verbose mode on')

    return args


def select_allhiragana(ids, today, path):
    dmmparser = dmm2ssw.DMMParser(no_omits=(), deeper=False, pass_bd=True)
    conn = sqlite3.connect(path or 'dmm_actress.db')
    cur = conn.cursor()

    if ids:
        sql = 'select id,current from main where id in({})'.format(
            ','.join('?' * len(ids)))
        cur.execute(sql, ids)
    else:
        cur.execute('select id,current from main '
                    'where retired is null and deleted is null')

    for aid, name in cur:
        verbose('id: ', aid, ', name: ', name)

        if libssw.p_neghirag.search(name) or len(name) > 4:
            continue

        print(aid, name + ': ', end='')
        url = 'http://actress.dmm.co.jp/-/detail/=/actress_id={}/'.format(aid)
        verbose('url: ', url)

        resp, he = libssw.open_url(url)

        info = he.find('.//td[@class="info_works1"]')
        if info is None:
            print('negative')
            continue

        for tr in info.getparent().getparent()[1:]:
            verbose('title: ', tr.find('td/a').text)

            if tr[4].text == '---' or tr[6].text == '---':
                verbose('Not DVD or Rental')
                continue

            b, status, values = dmm2ssw.main(
                props=libssw.Summary(url=tr[4].find('a').get('href')),
                p_args=argparse.Namespace(fastest=True),
                dmmparser=dmmparser)
            if status in ('Omitted', 404):
                verbose('Omitted: status=', status, ', values=', values)
                continue

            lastrel = date(*(int(d) for d in tr[7].text.split('-')))

            if (today - lastrel).days < 366:

                yield name
                print('positive ({})'.format(lastrel.year))

            else:
                print('negative ({})'.format(lastrel.year))

            break

        else:
            print('negative')

    conn.close()


def main():

    args = get_args()

    today = date.today()

    positive = set(select_allhiragana(args.id, today, args.path))
    print('# 1年以内にリリース実績のある実在するひらがなのみで4文字以下の名前 ({}現在)'.format(
        str(today)))
    print('_allhiraganas = ', end='')
    print(sorted(positive))


if __name__ == '__main__':
    main()
