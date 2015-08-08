#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
その他アダルトサイトから素人系Wikiのウィキテキストを作成

書式：
others2ssw.py "作品ページのURL" ["URL" ...]

対応サイト：
・JAPORN.TV系(avfantasy, aventertainments, mediafreakcity)
・一本道
・カリビアンコム(含プレミアム)
・HEYZO
・HEY動画
・Tokyo-Hot(my.tokyo-hot.comの方)
・パコパコママ
・天然むすめ
・熟女倶楽部
・人妻パラダイス
・人妻切り
'''
import argparse
import re
from urllib.parse import urlparse

import libssw

__version__ = 20150808

VERBOSE = 0

OWNNAME = libssw.ownname(__file__)

FOLLOW_RDR = None

verbose = libssw.Verbose(OWNNAME, VERBOSE)
emsg = libssw.Emsg(OWNNAME)

p_musume_title = re.compile(r'素人アダルト動画　天然むすめ  (.*)')
p_heyzo_title = re.compile(r'の無修正アダルト動画「(.+)」のご案内')


def get_args():
    global VERBOSE

    argparser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='無修正系サイトのURLから素人系総合wiki用ウィキテキストを作成する',
        epilog='対応サイト: JAPORN.TV, 一本道, カリビアンコム(含プレミアム), HEYZO, '
        'HEY動画, Tokyo-Hot(my.tokyo-hot.com), パコパコママ, 天然むすめ, 熟女倶楽部, 人妻パラダイス, 人妻切り')
    argparser.add_argument('url',
                           help='作品ページのURL',
                           nargs='+',
                           metavar='URL')
    argparser.add_argument('-f', '--disable-follow-redirect',
                           help='ページのリダイレクト先を取得しない',
                           dest='follow_rdr',
                           action='store_false',
                           default=True)
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


def build_pfmrs(performers):
    return tuple((p, '', '') for p in performers)


def uncensored(url, release, title, studio, performers, note):
    performers = build_pfmrs(performers)
    verbose('release: ', release)
    verbose('title: ', title)
    verbose('studio: ', studio)
    verbose('performers: ', performers)

    if release:
        print('//{0[0]}.{0[1]:0>2}.{0[2]:0>2}'.format(release))

    print('-[[{}（{}）>{}]]{}'.format(title, studio, url, note))

    if len(performers) > 1:
        # 出演者情報の作成
        pfmstr, anum = libssw.stringize_performers(
            performers, number=0, follow=FOLLOW_RDR)
        print('--出演者：{}'.format(pfmstr))


def censored(url, release, title, studio, performers, img_s, img_l, note):
    performers = build_pfmrs(performers)
    verbose('release: ', release)
    verbose('title: ', title)
    verbose('studio: ', studio)
    verbose('performers: ', performers)

    if release:
        print('//{0[0]}.{0[1]:0>2}.{0[2]:0>2}'.format(release))

    print('[[{}（{}）>{}]]'.format(title, studio, url))
    print('[[{}>{}]]'.format(img_s, img_l))

    if len(performers) > 1:
        # 出演者情報の作成
        pfmstr, anum = libssw.stringize_performers(
            performers, number=0, follow=FOLLOW_RDR)
        print('--出演者：{}'.format(pfmstr))

    if note:
        print(note)


def japorn(he, url):
    '''JAPORN.TV'''
    note = ''
    current_tab = he.xpath('//ol[@class="tab  current"][1]/a')[0]
    if current_tab.get('title') == 'DVD':
        # DVDのときのBlu-ray版チェック
        bd = he.xpath('//a[@title="BLU-RAY"]')
        if len(bd):
            bdlink = bd[0].get('href')
            note = ' ([[Blu-ray版>{}]])'.format(bdlink)
    elif current_tab.get('title') == 'BLU-RAY':
        # Blu-ray版のときのDVD版チェック
        dvd = he.xpath('//a[@title="DVD"]')
        if len(dvd):
            dvdlink = dvd[0].get('href')
            note = ' ([[DVD版>{}]])'.format(dvdlink)

    title = he.xpath(
        '//div[@id="mini-tabet"]/h2')[0].text.strip()

    for redtitle in he.iterfind('.//span[@class="redtitle"]'):
        label = redtitle.text.strip()
        if label.startswith('主演女優'):
            performers = [t.strip() for t in
                          redtitle.getparent().xpath('a/text()')]
        elif label.startswith('スタジオ'):
            studio = redtitle.getnext().text.strip()
        elif label.startswith('発売日'):
            reltext = redtitle.tail.strip()
            release = libssw.p_number.findall(reltext)
            release = [release[i] for i in (2, 0, 1)]

    uncensored(url, release, title, studio, performers, note)


def ipondo(he, url):
    studio = '一本道'

    title = he.xpath('//h1')[0].getnext().text_content().strip()
    performers = he.xpath('//h1/a')[0].text.strip().split()

    # 検索結果ページから配信開始日を取得する
    # 検索文字列(URL)の作成
    qlist = performers[:]
    qlist.append(title)
    verbose('qlist: ', qlist)
    searchurl = 'http://www.1pondo.tv/list.php?q={}&op=and'.format(
        '+'.join(libssw.quote(s) for s in qlist))
    verbose('searchurl: ', searchurl)

    release = None
    while not release:
        r, e = libssw.open_url(searchurl)
        for div in e.iterfind(
                './/div[@class="list_container"]/div'):
            a = div.xpath('a')[0]
            verbose('a: ', a.get('href'))
            if a.get('href') == url:
                release = libssw.p_number.findall(
                    div.xpath('p')[0].text_content())
                break
        else:
            # ページ内に見つからなかったら次のページヘ
            for pagin in he.iterfind(
                    './/div[@class="listblock"]/p[@align="right"]/a'):
                if pagin.text.strip() == '次へ':
                    searchurl = 'http://www.1pondo.tv{}'.format(
                        pagin.get('href'))
                    break
            else:
                # 最後まで見つからなかったらダミーリストを返す
                emsg('W', '配信開始日を取得できませんでした。')
                release = tuple('0000', '00', '00')

    uncensored(url, release, title, studio, performers, '')


def caribbean(he, netloc, url):
    if netloc == 'www.caribbeancom.com':
        studio = 'カリビアンコム'
        title = he.xpath('//span[@class="movie-title"]/h1')[0].text.strip()
    else:
        studio = 'カリビアンコム プレミアム'
        title = he.find_class('video-detail')[0].xpath('.//h1')[0].text.strip()

    release = libssw.p_number.findall(
        he.find_class('movie-info')[0].xpath('dl[3]/dd')[0].text)

    performers = he.find_class(
        'movie-info')[0].xpath('dl[1]/dd')[0].text_content().split()

    uncensored(url, release, title, studio, performers, '')


def heyzo(he, url):
    studio = 'HEYZO'

    title = he.xpath('//meta[@name="description"]')[0].get('content')
    title = p_heyzo_title.findall(title)[0]

    release = libssw.p_number.findall(
        he.find_class('release-day')[0].getnext().text.strip())

    performers = he.xpath(
        '//div[@class="movieInfo"]//span[@class="actor"]')[0].getnext().xpath(
            'a//text()')

    uncensored(url, release, title, studio, performers, '')


def heydouga(he, url):
    studio = 'HEY動画'

    title = he.xpath('//meta[@name="description"]')[0].get('content')

    movieinfo = he.find_class('movieInfo')[0]

    release = libssw.p_number.findall(movieinfo.xpath('li[1]')[0].text)

    performers = movieinfo.xpath('li[2]/a')[0].text.split()

    uncensored(release, title, studio, performers, '')


def tokyohot(he, url):
    studio = 'Tokyo-Hot'

    title = he.xpath('//div[@class="pagetitle"]/h2')[0].text.strip()

    release = libssw.p_number.findall(
        he.xpath('//dl[@class="info"][2]/dd[1]/text()')[0])

    performers = [t.strip() for t in
                  he.xpath('//dl[@class="info"][1]/dd[1]/a/text()')]

    uncensored(url, release, title, studio, performers, '')


def pacopacomama(he, url):
    studio = 'パコパコママ'

    title = he.xpath('//title')[0].text.strip()

    release = libssw.p_number.findall(he.find_class('date')[0].text)[:3]

    performers = he.xpath(
        '//div[@class="detail-info-l"]//table/tr[1]/td/a'
    )[0].text.strip().split()

    uncensored(url, release, title, studio, performers, '')


def tenmusume(he, url):
    studio = '天然むすめ'

    title = p_musume_title.findall(he.xpath('//title')[0].text.strip())[0]

    release = libssw.p_number.findall(
        he.get_element_by_id('info').xpath('div[1]/ul/li[1]/em')[0].tail)

    performers = he.get_element_by_id('info').xpath(
        'div[1]/ul/li[2]/a')[0].text.strip().split()

    uncensored(url, release, title, studio, performers, '')


def jukujoclub(he, url):
    studio = '熟女倶楽部'

    movdata = he.find_class('movie_data_bottom')[0].xpath('table')[0]

    title = movdata.xpath('tr[2]/td')[1].text.strip()

    release = ['0000'] + libssw.p_number.findall(
        movdata.xpath('tr[7]/td')[1].text)

    performers = movdata.xpath('tr[3]/td')[1].text_content().split()

    uncensored(url, release, title, studio, performers, '')


def h_paradise(he, url):
    studio = '人妻パラダイス'

    title = he.find_class("gold-bar")[0].text_content()

    img_s = he.find_class('model-prof')[0].find('img').get('src')

    censored(url, None, title, studio, (), img_s, url, '')


def hitodumagiri(he, url):
    studio = '人妻斬り'

    performer = he.find_class('name_JP_hitozuma')[0].text.strip()
    age = libssw.p_number.findall(
        he.xpath('//table[@summary="movie info"][1]//tr[1]/td')[1].text)[0]

    title = performer + age + '才'

    qname = '+'.join(libssw.quote(n) for n in performer.split())
    srchurl = 'http://www.c0930.com/search/?q={}&x=0&y=0&category_search_type=and&flag_match_type=0'.format(qname)

    release = None
    while not release:
        resp, srchp = libssw.open_url(srchurl)
        for div in srchp.find_class('unit-thumbs ori1'):
            if div[1].get('href') == url:
                release = libssw.p_number.findall(div[0].text)
        else:
            nextbold = he.find_class('next bold')
            if nextbold is not None:
                srchurl = nextbold[0].get('href')

    uncensored(url, release, title, studio, [performer], '')


def main():
    global FOLLOW_RDR

    args = get_args()

    FOLLOW_RDR = args.follow_rdr

    urls = ('http://' + u if not u.startswith('http://') else u
            for u in args.url)

    for url in urls:

        netloc = urlparse(url).netloc
        resp, he = libssw.open_url(
            url,
            charset='euc_jisx0213' if netloc.endswith('h-paradise.net')
            else None)

        if netloc in ('www.aventertainments.com',
                      'www.avfantasy.com',
                      'www.mediafreakcity.com'):
            japorn(he, url)

        elif netloc == 'www.1pondo.tv':
            release, title, studio, performers, note = ipondo(he, url)

        elif netloc in ('www.caribbeancom.com',
                        'www.caribbeancompr.com'):
            caribbean(he, netloc, url)

        elif netloc == 'www.heyzo.com':
            heyzo(he, url)

        elif netloc == 'www.heydouga.com':
            heydouga(he, url)

        elif netloc == 'my.tokyo-hot.com':
            tokyohot(he, url)

        elif netloc == 'www.pacopacomama.com':
            pacopacomama(he, url)

        elif netloc == 'www.10musume.com':
            tenmusume(he, url)

        elif netloc == 'www.jukujo-club.com':
            jukujoclub(he, url)

        elif netloc.endswith('h-paradise.net'):
            h_paradise(he, url)

        elif netloc == 'www.c0930.com':
            hitodumagiri(he, url)

        else:
            emsg('E', '未知のサイトです。')


if __name__ == '__main__':
    main()
