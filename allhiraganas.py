#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
ひらがなのみの女優名の採取

名前がひらがなのみで5文字未満で、DVDセルおよびレンタル最新作のリリースが前年までの女優名をリストアップ
'''
import sqlite3
import time
import argparse

import libssw
import dmm2ssw


VERBOSE = 0

OWNNAME = libssw.ownname(__file__)
verbose = libssw.Verbose(OWNNAME, VERBOSE)
emsg = libssw.Emsg(OWNNAME)


def get_args():
    global VERBOSE

    argeparser = argparse.ArgumentParser()
    argeparser.add_argument('-i', '--id',
                            help='女優ID',
                            nargs='+')
    argeparser.add_argument('-v', '--verbose',
                            help='デバッグ用情報を出力する',
                            action='count',
                            default=0)

    args = argeparser.parse_args()

    verbose.verbose = VERBOSE = args.verbose

    if args.verbose > 1:
        libssw.VERBOSE = libssw.verbose.verbose = \
            dmm2ssw.VERBOSE = dmm2ssw.verbose.verbose = args.verbose - 1
    verbose('verbose mode on')

    return args


def select_allhiragana(ids):
    thisyr = time.localtime().tm_year
    dmmparser = dmm2ssw.DMMParser(no_omits=(), deeper=False, pass_bd=True)
    conn = sqlite3.connect('dmm_actress.db')
    cur = conn.cursor()

    if ids:
        length = len(ids)
        sql = 'select id,current from main where id in({})'.format(
            ','.join('?' * length))
        cur.execute(sql, ids)
    else:
        cur.execute('select id,current from main '
                    'where retired is null and deleted is null')

    for aid, name in cur:
        verbose('id: ', aid, ', name: ', name)
        if not libssw.p_neghirag.search(name) and len(name) < 5:
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
                    verbose('Not DVD and Rental')
                    continue

                b, status, values = dmm2ssw.main(
                    props=libssw.Summary(url=tr[4].find('a').get('href')),
                    p_args=argparse.Namespace(fastest=True),
                    dmmparser=dmmparser)
                if status in ('Omitted', 404):
                    verbose('Omitted: status=', status, ', values=', values)
                    continue

                lastrel = int(tr[7].text.strip().split('-', 1)[0])
                if thisyr - lastrel < 2:
                    yield name
                    print('positive ({})'.format(lastrel))
                else:
                    print('negative ({})'.format(lastrel))
                break
            else:
                print('negative')

    conn.close()


def main():

    args = get_args()

    positive = set(select_allhiragana(args.id))
    print('# 1年以内にリリース実績のある実在するひらがなのみの名前 ({}現在)'.format(
        time.strftime('%Y-%m-%d')))
    print('_allhiraganas = ', end='')
    print(sorted(positive))


if __name__ == '__main__':
    main()
