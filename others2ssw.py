#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
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
・MGS動画
・FC2コンテンツマーケット
"""
import argparse
import re
from urllib.parse import urlparse

import libssw

__version__ = 20151009

VERBOSE = 0

OWNNAME = libssw.ownname(__file__)

FOLLOW_RDR = True
COPY = False
BROWSER = False

emsg = libssw.Emsg(OWNNAME)

re_musume_title = re.compile(r'素人アダルト動画　天然むすめ  (.*)')
re_heyzo_title = re.compile(r'の無修正アダルト動画「(.+)」のご案内')


verbose = None


def get_args():
    global VERBOSE
    global verbose
    global FOLLOW_RDR
    global COPY
    global BROWSER

    argparser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='無修正系サイトのURLから素人系総合wiki用ウィキテキストを作成する',
        epilog='対応サイト: JAPORN.TV, 一本道, カリビアンコム(含プレミアム), HEYZO, '
        'HEY動画, Tokyo-Hot(my.tokyo-hot.com), パコパコママ, 天然むすめ,MGS動画,FC2コンテンツマーケット'
        '熟女倶楽部, 人妻パラダイス, 人妻切り')
    argparser.add_argument('url',
                           help='作品ページのURL',
                           nargs='+',
                           metavar='URL')
    argparser.add_argument('-f', '--disable-follow-redirect',
                           help='ページのリダイレクト先を取得しない',
                           dest='follow_rdr',
                           action='store_false',
                           default=True)

    argparser.add_argument('-c', '--copy',
                           help='作成したウィキテキストをクリップボードへコピーする',
                           action='store_true')
    argparser.add_argument('-b', '--browser',
                           help='生成後、wikiのページをウェブブラウザで開く',
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

    FOLLOW_RDR = args.follow_rdr
    COPY = args.copy
    BROWSER = args.browser

    return args


def build_pfmrs(performers):
    return tuple((p, '', '') for p in performers)


def uncensored(url, release, title, studio, performers, note):
    performers = build_pfmrs(performers)
    verbose('release: ', release)
    verbose('title: ', title)
    verbose('studio: ', studio)
    verbose('performers: ', performers)

    wtxt = []

    if release:
        wtxt.append('//{0[0]}.{0[1]:0>2}.{0[2]:0>2}'.format(release))

    wtxt.append('-[[{}（{}）>{}]]{}'.format(title, studio, url, note))

    if len(performers) > 1:
        # 出演者情報の作成
        pfmstr, anum = libssw.stringize_performers(
            performers, number=0, follow=FOLLOW_RDR)
        wtxt.append('--出演者：{}'.format(pfmstr))

    wtxt = '\n'.join(wtxt)
    print(wtxt)
    if COPY:
        libssw.copy2clipboard(wtxt)
    if BROWSER:
        libssw.open_ssw(*(p[1] or p[0] for p in performers))


def censored(url, release, title, label, performers, img_s, img_l, note, pno=False, width=False):
    performers = build_pfmrs(performers)
    verbose('release: ', release)
    verbose('title: ', title)
    verbose('label: ', label)
    verbose('performers: ', performers)

    wtxt = []

    if release:
        # wtxt.append('//{0[0]}.{0[1]:0>2}.{0[2]:0>2}'.format(release))
        if pno:
            print('//{0[0]}.{0[1]:0>2}.{0[2]:0>2}'.format(release) + " " + pno)
        else:
            print('//{0[0]}.{0[1]:0>2}.{0[2]:0>2}'.format(release))

    if label:
        print('[[{}（{}）>{}]] [[(レーベル一覧>{})]]'.format(title, label, url, label))
    else:
        print('[[{}（{}）>{}]]'.format(title, label, url))

    if width:
        print('[[&ref({}, {})>{}]]'.format(img_s, width, img_l))
    else:
        print('[[{}>{}]]'.format(img_s, img_l))

    if len(performers) > 1:
        # 出演者情報の作成
        pfmstr, anum = libssw.stringize_performers(
            performers, number=0, follow=FOLLOW_RDR)
        wtxt.append('--出演者：{}'.format(pfmstr))

    if note:
        wtxt.append(note)

    wtxt = '\n'.join(wtxt)
    print(wtxt)
    if COPY:
        libssw.copy2clipboard(wtxt)
    if BROWSER:
        libssw.open_ssw(*(p[1] or p[0] for p in performers))


def japorn(he, url):
    """JAPORN.TV"""
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

    title = he.xpath('//div[@id="mini-tabet"]/h2')[0].text.strip()

    for redtitle in he.iterfind('.//span[@class="redtitle"]'):
        label = redtitle.text.strip()
        if label.startswith('主演女優'):
            performers = [t.strip() for t in
                          redtitle.getparent().xpath('a/text()')]
        elif label.startswith('スタジオ'):
            studio = redtitle.getnext().text.strip()
        elif label.startswith('発売日'):
            reltext = redtitle.tail.strip()
            release = libssw.extr_num(reltext)
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
        for div in e.iterfind('.//div[@class="list_container"]/div'):
            a = div.xpath('a')[0]
            verbose('a: ', a.get('href'))
            if a.get('href') == url:
                release = libssw.extr_num(div.xpath('p')[0].text_content())
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
        title = he.find('.//h1[@itemprop="name"]').text.strip()
        release = libssw.extr_num(
            he.find('.//dd[@itemprop="uploadDate"]').text)
    else:
        studio = 'カリビアンコム プレミアム'
        title = he.find_class('video-detail')[0].xpath('.//h1')[0].text.strip()
        release = libssw.extr_num(
            he.find('.//div[@class="movie-info"]/dl[3]/dd[1]').text)

    performers = he.find_class(
        'movie-info')[0].xpath('dl[1]/dd')[0].text_content().split()

    uncensored(url, release, title, studio, performers, '')


def heyzo(he, url):
    studio = 'HEYZO'

    title = he.xpath('//meta[@name="description"]')[0].get('content')
    title = re_heyzo_title.findall(title)[0]

    release = libssw.extr_num(
        he.find_class('release-day')[0].getnext().text.strip())

    performers = he.xpath(
        '//div[@class="movieInfo"]//span[@class="actor"]')[0].getnext().xpath(
            'a//text()')

    uncensored(url, release, title, studio, performers, '')


def heydouga(he, url):
    studio = 'HEY動画'

    title = he.xpath('//meta[@name="description"]')[0].get('content')

    movieinfo = he.find_class('movieInfo')[0]

    release = libssw.extr_num(movieinfo.xpath('li[1]')[0].text)

    performers = movieinfo.xpath('li[2]/a')[0].text.split()

    uncensored(release, title, studio, performers, '')


def tokyohot(he, url):
    studio = 'Tokyo-Hot'

    title = he.xpath('//div[@class="pagetitle"]/h2')[0].text.strip()

    release = libssw.extr_num(
        he.xpath('//dl[@class="info"][2]/dd[1]/text()')[0])

    performers = [t.strip() for t in
                  he.xpath('//dl[@class="info"][1]/dd[1]/a/text()')]

    uncensored(url, release, title, studio, performers, '')


def pacopacomama(he, url):
    studio = 'パコパコママ'

    title = he.xpath('//title')[0].text.strip()

    release = libssw.extr_num(he.find_class('date')[0].text)[:3]

    performers = he.xpath(
        '//div[@class="detail-info-l"]//table/tr[1]/td/a'
    )[0].text.strip().split()

    uncensored(url, release, title, studio, performers, '')


def tenmusume(he, url):
    studio = '天然むすめ'

    title = re_musume_title.findall(he.xpath('//title')[0].text.strip())[0]

    release = libssw.extr_num(
        he.get_element_by_id('info').xpath('div[1]/ul/li[1]/em')[0].tail)

    performers = he.get_element_by_id('info').xpath(
        'div[1]/ul/li[2]/a')[0].text.strip().split()

    uncensored(url, release, title, studio, performers, '')


def jukujoclub(he, url):
    studio = '熟女倶楽部'

    movdata = he.find_class('movie_data_bottom')[0].xpath('table')[0]

    title = movdata.xpath('tr[2]/td')[1].text.strip()

    release = ['0000'] + libssw.extr_num(movdata.xpath('tr[7]/td')[1].text)

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
    age = libssw.extr_num(
        he.xpath('//table[@summary="movie info"][1]//tr[1]/td')[1].text)[0]

    title = performer + age + '才'

    qname = '+'.join(map(libssw.quote, performer.split()))
    srchurl = 'http://www.c0930.com/search/?q={}&x=0&y=0&category_search_type=and&flag_match_type=0'.format(qname)

    release = None
    while not release:
        resp, srchp = libssw.open_url(srchurl)
        for div in srchp.find_class('unit-thumbs ori1'):
            if div[1].get('href') == url:
                release = libssw.extr_num(div[0].text)
        else:
            nextbold = he.find_class('next bold')
            if nextbold is not None:
                srchurl = nextbold[0].get('href')

    uncensored(url, release, title, studio, [performer], '')

class fc2:
    studio = 'FC2コンテンツマーケット'
    url = ""
    release = ""
    title = ""
    img_s = ""
    img_l = ""
    comment = ""
    series = ""
    fc2_id = ""

    def url2id(self, url):
        r = re.match(".+id=([0-9]+)", url)
        if r:
            return r[1]
        else:
            return False

    def id2url(self, fc2_id):
        self.fc2_id = fc2_id
        return "https://adult.contents.fc2.com/article_search.php?id=" + self.fc2_id
        
    def parse_contents_market(self, url, he=None):
        self.url = url
        if he is None:
            resp, he = libssw.open_url(url,None)

        self.title = he.find_class('detail')[0].find('h2').text_content()
        self.release = he.find_class('main_info_block')[0].find('dl').findall('dd')[3].text_content().split("/")
        self.series = he.find_class('main_info_block')[0].find('dl').findall('dd')[4].text_content()
        # release = he.find_class('main_info_block')[0].find('h2').find('dd')[5].text_content()
        self.img_s = "http:" + he.find_class('analyticsLinkClick_mainThum')[0].find('img').get('src')
        self.img_l = he.find_class('analyticsLinkClick_mainThum')[0].get('href')

        # return {"url":url, "release":release, "title":title, "studio":studio, "img_s":img_s, "img_l":img_l, "comment":'FC2 ' + fc2_id}

    def print_cencered(self):
        censored(self.url, self.release, "FC2 " + self.title, self.series, (), self.img_s, self.img_l, '', 'FC2 ' + self.fc2_id, 147)

class mgs:
    studio = "MGS動画"
    url = ""
    actress = ""
    release = ""
    title = ""
    series = ""
    img_s = ""
    img_l = ""
    comment = ""
    id = ""

    def url2id(self, url):
        r = re.match("https://www.mgstage.com/product/product_detail/(.+)/$", url)
        if r:
            self.id = r[1]
            return self.id
        else:
            return False

    def id2url(self, id):
        self.id = id
        self.url = "https://www.mgstage.com/product/product_detail/" + id
        return self.url

    def parse(self, url):
        # lxmlバージョン　動かない
        self.url = url
        
        resp, he = libssw.open_url(self.url,set_cookie="adc=1")

        self.title = he.find_class('tag')[0].text_content()
        # self.title = he.find('h1')
        self.release = he.xpath('//div[@class="detail_data"]/table[1]')[0].text_content()
        self.release = he.findall("table")
        # self.release = he.findall("table")[1].find("td")
        return self.title

    def parse_by_bs4(self, url):
        if self.url == "":
            self.url = url

        if self.id == "":
            self.url2id(url)
            
        # lxmlではmgstageの壊れている不正ななhtmlはパースできない
        from bs4 import BeautifulSoup
        import urllib.request

        data = {
            "Cookie": 'adc=1',
        }
        req = urllib.request.Request(url, None, data)
        with urllib.request.urlopen(req) as res:
            s = res.read()
        soup = BeautifulSoup(s, "html.parser")

        self.title = soup.find("h1", class_="tag").text.strip()
        self.actress = soup.findAll("table")[1].findAll("td")[0].text.strip()
        self.release = soup.findAll("table")[1].findAll("td")[4].text.split("/")
        self.series = soup.findAll("table")[1].findAll("td")[6].text.strip()
        self.img_s = soup.find("img", class_="enlarge_image").attrs["src"]
        self.img_l = soup.find("a", id="EnlargeImage").attrs["href"]

        return

    def print_cencered(self):
        censored(self.url, self.release, self.title, self.series, (), self.img_s, self.img_l, '', 'MGS ' + self.id)


class mgs:
    url = ""
    actress = ""
    release = ""
    title = ""
    studio = ""
    img_s = ""
    img_l = ""
    comment = ""

    def parse(self, url):
        self.url = url
        
        resp, he = libssw.open_url(self.url,set_cookie="adc=1")

        self.title = he.find_class('tag')[0].text_content()
        # self.title = he.find('h1')
        self.release = he.xpath('//div[@class="detail_data"]/table[1]')[0].text_content()
        # self.release = he.find_class('detail_data')[0].findall("table")[1].find("td")
        return self.title
        # self.title = he.find_class('tag')[0].find('h1').text_content()

    def parse_by_bs4(self, url):
        # lxmlではmgstageの不完全なhtmlはパースできない
        from bs4 import BeautifulSoup
        import urllib.request

        # url = "https://www.mgstage.com/product/product_detail/" + cid
        data = {
            "Cookie": 'adc=1',
        }
        req = urllib.request.Request(url, None, data)
        with urllib.request.urlopen(req) as res:
            s = res.read()
        soup = BeautifulSoup(s, "html.parser")

        self.title = soup.find("h1", class_="tag").text.strip()
        self.actress = soup.find("div", class_="detail_data").findAll("table")
        self.img_s = soup.find("img", class_="enlarge_image").attrs["src"]
        self.img_l = soup.find("a", id="EnlargeImage").attrs["href"]

        return


def main():

    args = get_args()

    # urls = ('http://' + u if not u.startswith('http://') else u
            # for u in args.url)

    urls = ('https://' + u if not re.match('^https?://.+',u) else u
            for u in args.url)

    for url in urls:

        netloc = urlparse(url).netloc

        if netloc == 'www.mgstage.com':
            f = mgs()
            f.parse_by_bs4(url)
            # f.parse(url)
            f.print_cencered()

        else:
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

            elif netloc == 'adult.contents.fc2.com':
                f = fc2()
                fc2_id = f.url2id(url)
                f.fc2_id = fc2_id
                f.parse_contents_market(url, he=he)
                f.print_cencered()

            else:
                emsg('E', '未知のサイトです。')


if __name__ == '__main__':
    main()
