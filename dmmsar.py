#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
dmm2ssw.pyのラッパー。
指定されたIDやキーワード等でDMMから一覧を取得し、ウィキテキストを作成する。

書式:
dmmsar.py (-A|-S|-L|-M|-U) [キーワード ...] [オプション...]


説明:
    DMMでキーワード検索、女優、シリーズ、メーカー、あるいは
    レーベルのID(DMMで割り当てているやつ)を直接指定してその検索結果から
    dmm2ssw.pyを呼び出し素人系総合wiki用ウィキテキストをまとめて作成する。
    作品一覧だけを取得したり、ファイルから読み込むこともできる。

    デフォルトでイメージビデオ、総集編、DMM限定、アウトレット製品は除外を
    試みる(-m オプションで調整可)。ただしすべて除外できるとは限らない。
    総集編の判別は:
    ・品番のプレフィクスがあらかじめ登録されている総集編のものと一致
    ・ジャンルに総集編がある
    ・タイトルに「総集編」「BEST」などの関連ワードがある
    ・タイトルに「20人/名」以上/「15本番」以上/「50(連)発」以上/「4時間」以上/「240分」以上のうち
    2つ以上含まれている
    ・メーカーがROOKIEで出演者数が3人を超えている
    ・メーカーがROOKIEでタイトルに4時間以上または200分以上の時間が含まれている


注意:
    一度取得したページはキャッシュされ(一部のページを除く)、Wikiなら最大2時間、
    それ以外は24時間はそれを利用する。
    内部でサイトごとにアクセスに5秒の間隔を置いている。
    この間隔を短く/無くしたりして短時間に大量の情報を取得した場合、(D)DoS攻撃と
    みなされて通報されるかもしれないので注意。


引数:
キーワード(ID/URL/品番/ファイルパス)
    -A/-S/-M/-L を指定した場合は取得するそれのIDか、その一覧ページのURLを
    指定する。
    -U を指定した場合はDMM一覧ページのURLを指定する。
    --cid を指定した場合は cid の範囲を指定する(--cid オプションを参照)。

    IDはDMM上でそれぞれでの一覧を表示した時にそのURLからわかる(id=)。
    -i/-w を指定した場合はファイルのパスを指定する。パスが指定されないと
    標準入力から読み込む。

    IDを複数指定した場合、それらをまとめて1つの一覧を作成する。これは改名して
    いるがDMM上で統合されていない女優の作品一覧の作成を想定しているため。


オプション:
-A, --actress (女優IDで一覧取得)
-S, --series  (シリーズIDで一覧取得)
-L, --label   (レーベルIDで一覧取得)
-M, --maker   (メーカーIDで一覧取得)
-U, --url     (指定したURLのページからそのまま取得)
    検索方法。どれか一つだけ指定できる。
    -A/-S/-M/-L で女優/シリーズ/メーカー/あるいはレーベルのいずれかの
    DMM上のID(またはURL)指定で一覧を取得する。
    キーワードに女優/シリーズ/レーベル/メーカー一覧ページのURLを指定すると
    -A/-S/-L/-M を自動判定する。
    -U では、指定されたURLのページからそのまま取得する。

-i, --from-tsv
    作品情報の一覧をインポートファイル(TSV)から取得する。

    インポートファイル形式:
    --tsv 指定で出力される一覧の形式に情報を追加するイメージ。タブ区切り。

    ファイルフォーマット:
    <カラム> <内容>
        0*   DMM作品ページのURL
        1*   タイトル
        2    品番
        3    出演者[,出演者 ...] (書式は dmm2ssw.py の -a オプション参照)
        4    出演者数
        5    監督[,監督 ...]
        6    備考 (NOTE)[,備考...] (要素ごとにカンマ区切り)
    *:必須

    タイトルとURLは必須。ただしタイトルの先頭に __ (アンダースコア2個)を
    つけておくと最終的に出力されるウィキテキストには使用されず、DMM上の
    タイトルが採用されるので、一意の文字列であれば何でも良い。
    レコードあたりタブが3個以上あれば他の情報はなくてもよい。
    文字列がなくてもタブがあるだけで「データのないカラム」があるとみなされる。

-w, --from-wiki
    素人総合wikiの表形式のウィキテキストから取得する。
    wikiとDMM上の情報をマージできる。
    セルが結合されている表には未対応。

--cid
    作成する作品のDMM上の品番(cid)を直接指定する。
    キーワードの第一引数に"{}"が含まれる場合は、引数を
    "品番の基底文字列" "開始番号" "終了番号" ["ステップ"]
    とみなす。
    例) dmmsar.py -L --cid "h_244saba{}" "080" "085"
    ⇒ cid=h_244saba080,081,082,083,084,085の情報を取得する。
    {} が含まれない場合は単に品番の羅列とみなし、それぞれの情報を取得する。
    指定した品番の作品ページが見つからなかったら発売前の作品とみなしDMMへの
    リンクは作成する。
    --service が指定されていない場合DVDセル版(dvd)とみなす。
    -U 指定時はこのオプションは指定できない。

--cid-l
    --cid と同じだが、指定した品番の作品ページが見つからない場合は発売されなかった
    あるいは発売が中止になったものとしてリンクを作成しない。

-o, --out ファイル名のベース
    指定されたファイルに出力する。未指定時は標準出力に出力する。
    ウィキテキストを作成した場合、実際に出力されるファイル名は、
    女優ページ用なら 識別子 + _actress + ページ数 + 拡張子
    レーベル/シリーズ一覧ページ用なら 識別子 + _table + ページ数 + 拡張子
    となる。
    また、--split (デフォルトは200) の件数ごとに番号を付けてファイルを分ける。
    例) moodyz.wiki ⇒ moodyz_table.1.wiki

-r, --replace
    出力ファイル名と同名のファイルが存在する場合それを上書きする。

-t, --table
    女優ページ用ではなく、一覧ページ用に表形式でウィキテキストを出力する。
    2個以上指定すると両方を作成する。
    --tsv と同時に指定できない。

--tsv
    ウィキテキストを作成せず、作品名とページURLの一覧(タブ区切り)を出力する。
    これで出力した一覧(を修正したもの)を -i オプションの入力とできる。
    -t/-tt と同時に指定できない。

--service {dvd,rental,video,ama,all}
    検索するサービスの種類を指定する。指定できるのは以下のうちどれか一つ。
     dvd     DVD通販 (-A/-S/-M/-L のデフォルト)
     rental  DVDレンタル
     video   動画-ビデオ
     ama     動画-素人
    -U/-i/-w を指定した場合は無視される。
    キーワードにURLが与えられていれば指定不要。

-m, --disable-omit
    イメージビデオを除外しない。
    m を2個指定すると総集編作品も、3個指定するとアウトレットも、
    4個指定すると限定盤も除外しない。
    除外もれ/除外しないもれが発生する場合もある。

--start-pid 品番(例:JMD-112)
    データ作成開始品番。一覧取得後、この品番とプレフィクスが同じで番号がこれ以上の
    ものが見つかればそれ以降のものだけ作成する。大文字小文字は区別しない。
    DMM作品ページのURL(cid=)から品番を作成しているが、URLのcidが実際の品番と
    異なることがあり、このとき抜けやズレが発生する場合がある。
    より厳密にチェックする場合は --start-pid-s オプションを使用する。

--start-pid-s 品番(例:JMD-112)
    --start-pid をより厳密にチェックする。
    作品ごとに作品ページを見に行くので開始品番を見つけるまでの時間がよりかかる。

--start-cid DMM上の品番(例:15jmd112so)
    --start-pid と似ているが、DMM上の品番でチェックする。
    DMM上の品番とは、DMMサイト上でDMMが割り振った品番のこと。
    大文字小文字は区別しない。
    DMM作品ページのURL(cid=)から品番を取得しているが、URLのcidが実際の品番と
    異なることがあり、このとき抜けやズレなどが発生する場合がある。

-e, --last-pid 品番
    Wiki上ですでに作成済みの作品の最後の品番。一覧取得後、この品番がみつかるまで
    スキップし、そのつぎの作品以降を作成する。
    大文字小文字は区別しない。
    DMM作品ページのURL(cid=)から品番を取得しているが、URLのcidが実際の品番と
    異なることがあり、このとき抜けやズレが発生する場合がある。
    より厳密にチェックする場合は --last-pid-s オプションを使用する。

--last-cid DMM上の品番(例:15jmd112so)
    --last-pid と似ているが、DMM上の品番でチェックする。
    DMM上の品番とは、DMMサイト上でDMMが割り振った品番のこと。
    大文字小文字は区別しない。
    DMM作品ページのURL(cid=)から品番を取得しているが、URLのidが実際の品番と
    異なることがあり、このとき抜けやズレなどが発生する場合がある。

--start-date YYYYMMDD
    データ作成開始日。発売/貸出/配信開始日がこの指定日以降のものだけ作成する。

--existings-html Wiki一覧ページのURL/HTML [URL/HTML ...] (一覧ページのHTML)
    Wikiの一覧ページを読み込み、まだWikiに追加されていない作品情報のみ作成する。

--filter-pid フィルターパターン
    品番がフィルターパターン(Python正規表現)にマッチしたものだけ作成する。
    大文字小文字は区別しない。
    DMM作品ページのURLから品番を取得しているが、URLのcidが実際の品番と異なる
    ことがあり、このとき抜けやズレが発生する場合がある。
    より厳密にチェックする場合は --filter-pid-s オプションを使用する。

--filter-pid-s フィルターパターン
    --filter-pid をより厳密にチェックする。
    作品ごとに作品ページを見に行くのでより時間がかかる。

--filter-cid フィルターパターン
    DMM上の品番(cid)がフィルターパターン(Python正規表現)にマッチしたものだけ
    作成する。大文字小文字は区別しない。
    DMM作品ページのURLから品番を取得しているが、URLのcidが実際の品番と異なる
    ことがあり、このとき抜けやズレなどが発生する場合がある。

--filter-title フィルターパターン
    作品名がフィルターパターン(Python正規表現)にマッチしたものだけ作成する。
    大文字小文字は区別しない。

--not-in-series
    シリーズに属していない作品のみ作成する(-L/-M/-U 指定時のみ)。
    見つかったシリーズ名の一覧を最後に出力する。

--row 行番号
    表形式を作成する時の最初のデータのみなし行位置。10件毎のヘッダー挿入やページ
    分割はこの値を基準に決定される。

--pages-last ページ数
    DMM上で一覧ページを、最新順にこのページ数分だけデータを取得し作成する。
    1ページあたり120件。
    --start-pid/--start-cid が指定された場合、該当する pid、cid を
    発見したページ+1ページがこの値を下回った場合はそこで取得を停止する。

--join-tsv ファイル [ファイル ...] (TSV)
    DMMから得た作品と(URLが)同じ作品がファイル内にあった場合、DMMからは取得できなかった
    情報がファイル側にあればそれで補完する(NOTEも含む)。
    ファイル形式については -i オプションの「インポートファイル形式」参照。

--join-wiki ウィキテキスト [ウィキテキスト ...] (一覧ページの表形式)
    DMMから得た作品と(URLが)同じ作品がウィキテキスト内にあった場合、DMMからは取得
    できなかった情報がウィキテキスト側にあればそれで補完する(NOTEも含む)。
    セルが結合されている表には未対応。

--join-html Wiki一覧ページのURL/HTML [URL/HTML ...] (一覧ページのHTML)
    DMMから得た作品と(URLが)同じ作品が、Wikiの一覧ページにあった場合、DMMからは取得
    できなかった情報がWiki側にあればそれで補完する(NOTEも含む)。
    一覧ページを保存したHTMLのファイルでも可。
    セルが結合されている表には未対応。

--hunter
    --join-*オプション指定と同時にこのオプションを指定すると作品タイトルは補完ファイル内の
    ものを優先する。ただし補完ファイル内の作品タイトルが「__」ではじまる場合は無視されDMM
    のものが採用される。

--sort-key {release,pid,title}
    出力する時の並び替えキー。
    デフォルトは品番順(pid)

-d, --add-dir-col
    DIRECTORカラムを出力する。
    -t/-tt オプションが与えられた時用。

--note 文字列
    女優ページ用なら最後に、一覧ページの表形式ならNOTEカラムに文字列を追加する。
    全作品に同じ文字列
    データは固定の文字列と以下の変数を指定できる。
    これら変数はウィキテキスト作成時に対応する文字列に展開される。
    @{media}  メディアの種類
    @{time}   収録時間
    @{series} シリーズ名
    @{maker}  メーカー名
    @{label}  レーベル名
    @{cid}    品番

--add-column [カラム名[:データ] [カラム名[:データ] ...]]
    表形式に任意のカラムを追加する。
    -t/-tt を指定しない場合は無視される。
    書式はカラム名のあとに : とともに各カラム内に出力するデータを指定できる。
    データの書式は --note オプションと同じ。

-s, --series-link [シリーズ一覧ページ名]
    作成する女優ページ用ウィキテキストに同一のシリーズ一覧ページへのリンクを
    強制的に追加・変更する。
    既存のDMMの作品ページ上のものがあっても置き換える。

-l, --label-link [レーベル一覧ページ名]
    作成する女優ページ用ウィキテキストに同一のレーベル一覧ページへのリンクを
    強制的に追加・変更する。
    既存のDMMの作品ページ上のものがあっても置き換える。

--linklabel 一覧ページへのリンクのラベル名
    作品一覧ページへのリンクに表示するラベル(「レーベル一覧」「シリーズ一覧」など)を
    ここで指定した文字列に置き換える。

--hide-list
    女優ページ用ウィキテキストにシリーズ/レーベル一覧へのリンクを追加しない。

--pid-regex パターン 置換文字列
    -t/-tt/-w を指定した場合のみ有効。
    dmm2ssw.py で行う品番の自動置き換えパターンでは対応できない場合用。
    作品のDMM上での品番情報(cid=)がパターン(python正規表現)にマッチしたら置換
    文字列で置き換える。
    マッチング時英字の大文字・小文字は区別しないが、マッチした場合すべて大文字化
    される。
    一部のイレギュラーなレーベルについては個別に対応している
    (dmm2ssw.pyの説明参照)。

--subtitle-regex パターン 置換文字列
    -t/-tt を指定した場合のみ有効。
    このオプションが指定されると、タイトルの文字列をを元に引数に従って副題を生成
    する。
    パターン(python正規表現)にマッチしたものを置換文字列で置き換える。
    マッチしなかったら何もしない。

--disable-series-guide
    メーカー/レーベル一覧ページ(表形式)でのシリーズ作品のシリーズ一覧ページへの
    ガイドを追加しない

--without-header
    先頭にヘッダ情報を出力しない。
    -w を指定した時は無視される。

--split ページあたりのタイトル数
    出力されるタイトル数がページあたりのタイトル数を超えるたび、空行とヘッダを
    挿入する。
    デフォルトは200。
    0を指定するとヘッダ挿入を行わない。
    --without-header 指定時は無視される(0と同じ)。

-f, --disable-follow-redirect
    取得した出演者名のwikiページがリダイレクトページかどうかチェックしない。
    指定しない場合チェックし、そうであればリダイレクト先へのリンクを取得して
    付加する。
    詳細はdmm2ssw.pyの説明参照。

--disable-check-smm
    デフォルトではDMM上に出演者情報がないときにSMMを検索して出演者情報がないか
    確認するが、このオプションが与えられるとそれを行わない。

--check-rental
    レンタル先行メーカーなのにレンタル版以外が指定されていた場合レンタル版のリリース
    情報をチェックしてレンタルが早ければそちらに置き換える。
    デフォルトの挙動はdmm2ssw.pyと逆。

--disable-check-listpage
    Wiki上の実際の一覧ページを探さない。

--disable-check-bd
    デフォルトでは、Blu-ray版製品だったとき、DVD版がないか確認し、DVD版があれば
    Blu-ray版の情報は作成しない(DVD版の方で備考としてBlu-ray版へのリンクを付記
    する)が、このオプションが与えられるとそれを行わず、DVD版と同様に(DVD版があれば
    両方を)作成する。

--fastest
    処理時間に影響する(ウェブページへアクセスする)あらゆる補助処理を行わない。

--recheck
    「ページが見つからない」とキャッシュされているページを再チェックする。

-b, --browser
    ページ名が確定している場合その名前のWikiページを開く。
    --tsv など、ページ名が解決できない場合は無視される。

--clear-cache
    dmm2ssw.py の説明参照。
    キャッシュを終了時に削除する。

-v, --verbose
    デバッグ用情報を出力する。

-V, --version
    バージョン情報を表示して終了する。

-h, --help
    ヘルプメッセージを表示して終了する。


使用例:
 1)
    ・女優「鈴村あいり」の女優ページ用ウィキテキストを作成する。
    ・作成後にWikiの「鈴村あいり」のページをウェブブラウザで開く。(-b)

    dmmsar.py "http://www.dmm.co.jp/mono/dvd/-/list/=/article=actress/id=1019076/" -b

 2)
    ・シリーズ「バコバコ風俗」の女優ページ用とシリーズ一覧ページ用両方のウィキテキストを作成する。(-tt)
    ・作成したウィキテキストをファイル名「bakobako.wiki」に保存する(実際のファイル名は「bakobako_actress.1.wiki」と「bakobako_table.1.wiki」になる)。(-o)

    dmmsar.py "http://www.dmm.co.jp/mono/dvd/-/list/=/article=series/id=8225/" -tt -o bakobako.wiki

 3)
    ・女優「椎名ゆな」の女優ページ用ウィキテキストを作成する。
    ・2014年1月1日以降にリリースされた作品分だけ作成する。(--start-date)

    dmmsar.py "http://www.dmm.co.jp/mono/dvd/-/list/=/article=actress/id=30317/" --start-date 20140101

 4)
    ・シリーズ「PREMIUM STYLISH SOAP」のシリーズ一覧ページ用ウィキテキストを作成する。(-t)
    ・品番 PGD-702 以降の作品分だけ作成する。(--start-pid)
    ・PGD-702 はシリーズ第41作目であることを指定する(表形式の10件ごとのヘッダ挿入用)。(--row)

    dmmsar.py "http://www.dmm.co.jp/mono/dvd/-/list/=/article=series/id=6642/sort=date/" -t --start-pid "pgd-702" --row 41

 5)
    ・素人動画レーベル「恋する花嫁」のレーベル一覧ページ用ウィキテキストを作成する。(-Lt)
    ・cid(DMM上の品番)が khy070 から khy090 までの作品分を作成する。(--cid)
    ・URL指定がなく素人動画レーベルなのでサービス「ama」を指定する。(--service)

    dmmsar.py -Lt --cid "khy{}" "070" "090" --service "ama"

 6)
    ・レーベル「S級素人」のレーベル一覧ページ用ウィキテキストを作成する。(-t)
    ・品番のプレフィクスが SABA のものだけ作成する。(--filter-pid)
    ・品番が SABA-125 以降の作品分だけ作成する。(--start-pid)
    ・総集編を除外しない。(-mm)

    dmmsar.py "http://www.dmm.co.jp/mono/dvd/-/list/=/article=label/id=8893/" -tmm --filter-pid "^saba" --start-pid "saba-125" --row 125

'''
import sys
import re
import io
import argparse
from operator import attrgetter
from itertools import zip_longest

import libssw
import dmm2ssw

__version__ = 20150424

OWNNAME = libssw.ownname(__file__)
VERBOSE = 0

verbose = libssw.Verbose(OWNNAME, VERBOSE)
emsg = libssw.Emsg(OWNNAME)

MSGLEVEL = {'E': 'ERROR',
            'W': 'WARN',
            'I': 'INFO'}

BASEURL = libssw.BASEURL
BASEURL_SSW = libssw.BASEURL_SSW
SERVICEDIC = libssw.SERVICEDIC

ACTINFOPAGE = 'http://actress.dmm.co.jp/-/detail/=/actress_id={}/'
ACTLISTPAGE = 'http://www.dmm.co.jp/mono/dvd/-/list/=/article=actress/id={}/sort=date/'

SPLIT_DEFAULT = 200

# sp_sort = (re.compile(r'/sort=(\w+)/'), '/sort=date/')

p_actdelim = re.compile(r'[（、]')


def get_args(argv):
    '''コマンドライン引数の解釈'''
    global VERBOSE

    argparser = argparse.ArgumentParser(description='DMMから検索して作品一覧を作成する')

    # 処理タイプ
    retrieval = argparser.add_mutually_exclusive_group()
    retrieval.add_argument('-A', '--actress',
                           help='女優IDで一覧取得',
                           action='store_const',
                           dest='retrieval',
                           const='actress')
    retrieval.add_argument('-S', '--series',
                           help='シリーズIDで一覧取得',
                           action='store_const',
                           dest='retrieval',
                           const='series')
    retrieval.add_argument('-L', '--label',
                           help='レーベルIDで一覧取得',
                           action='store_const',
                           dest='retrieval',
                           const='label')
    retrieval.add_argument('-M', '--maker',
                           help='メーカーIDで一覧取得',
                           action='store_const',
                           dest='retrieval',
                           const='maker')
    retrieval.add_argument('-U', '--url',
                           help='していたURLページからそのまま取得',
                           action='store_const',
                           dest='retrieval',
                           const='url')

    # ファイル入力
    from_file = argparser.add_mutually_exclusive_group()
    from_file.add_argument('-i', '--from-tsv',
                           help='TSVファイルから入力',
                           action='store_true')
    from_file.add_argument('-w', '--from-wiki',
                           help='素人総合wikiのウィキテキスト(表形式)から入力',
                           action='store_true')
    from_file.add_argument('--cid',
                           help='DMM上の品番(cid)指定で取得(ページが見つからなくてもリンクは作成する)',
                           action='store_true')
    from_file.add_argument('--cid-l',
                           help='DMM上の品番(cid)指定で取得(ページが見つからなければリンクは作成しない)',
                           action='store_true')

    argparser.add_argument('keyword',
                           help='検索キーワード、ID、品番、URL、またはファイル名',
                           metavar='KEYWORD',
                           nargs='*')

    # ファイル出力
    argparser.add_argument('-o', '--out',
                           help='ファイルに出力 (未指定時は標準出力へ出力)',
                           metavar='FILE')
    argparser.add_argument('-r', '--replace',
                           help='出力ファイルと同名のファイルがあった場合上書きする',
                           action='store_true')

    # 出力形式
    table = argparser.add_mutually_exclusive_group()
    table.add_argument('-t', '--table',
                       help='一覧ページ用の表形式でウィキテキストを作成する, '
                       '2個以上指定すると両方作成する',
                       action='count',
                       default=0)
    table.add_argument('--tsv',
                       help='ウィキテキストを生成せず、タブ区切りの一覧を出力する',
                       action='store_false',
                       dest='wikitext',
                       default=True)

    # データ取得先
    argparser.add_argument('--service',
                           help='一覧を取得するサービスを指定する (デフォルト: '
                           'KEYWORD にURLが与えられればそれから自動判定、'
                           'それ以外なら dvd)',
                           choices=('dvd', 'rental', 'video', 'ama', 'all'))

    # 作品データの除外基準
    argparser.add_argument('-m', '--disable-omit',
                           help='IVを除外しない、2個指定すると総集編も、'
                           '3個指定するとアウトレット版も、'
                           '4個指定すると限定盤も除外しない',
                           dest='no_omit',
                           action='count',
                           default=0)

    # データ作成範囲基準
    id_type = argparser.add_mutually_exclusive_group()
    id_type.add_argument('--start-pid',
                         help='データ作成開始品番(例:JMD-112)',
                         metavar='PID',
                         default='')
    id_type.add_argument('--start-pid-s',
                         help='データ作成開始品番(厳密にチェック)',
                         metavar='PID',
                         default='')
    id_type.add_argument('--start-cid',
                         help='データ作成開始品番(DMM上の品番, 例:15jmd112so)',
                         metavar='CID',
                         default='')
    id_type.add_argument('-e', '--last-pid',
                         help='作成済み作品情報の最後の品番',
                         metavar='PID',
                         default='')
    id_type.add_argument('--last-cid',
                         help='作成済み作品情報の最後の品番(DMM上の品番)',
                         metavar='CID',
                         default='')

    argparser.add_argument('--start-date',
                           help='データ作成対象開始リリース日',
                           metavar='YYYYMMDD')
    argparser.add_argument('--existings-html',
                           help='Wikiの一覧ページに既にある作品の情報は作成しない',
                           nargs='+',
                           metavar='URL/HTML')

    filters = argparser.add_mutually_exclusive_group()
    filters.add_argument('--filter-pid',
                         help='品番(pid)がパターン(正規表現)とマッチしたものだけ作成',
                         metavar='PATTERN')
    filters.add_argument('--filter-pid-s',
                         help='品番(pid)がパターン(正規表現)とマッチしたものだけ作成(厳密にチェク)',
                         metavar='PATTERN')
    filters.add_argument('--filter-cid',
                         help='DMM上の品番(cid)がパターン(正規表現)とマッチしたものだけ作成',
                         metavar='PATTERN')
    filters.add_argument('--filter-title',
                         help='作品名がパターン(正規表現)とマッチしたものだけ作成',
                         metavar='PATTERN')

    argparser.add_argument('--not-in-series',
                           help='シリーズに所属していないもののみ作成(-M/-L/-U 指定時)',
                           action='store_true',
                           dest='n_i_s')

    argparser.add_argument('--row',
                           help='先頭行のみなし行開始位置 (-t/-tt 指定時のみ)',
                           type=int,
                           default=0)

    argparser.add_argument('--pages-last',
                           help='データ収集ページ数(最新からPAGEページ分を収集)',
                           type=int,
                           default=0,
                           metavar='PAGE')

    # 外部からデータ補完
    argparser.add_argument('--join-tsv',
                           help='テキストファイル(TSV)でデータを補完する',
                           nargs='+',
                           metavar='FILE')
    argparser.add_argument('--join-wiki',
                           help='素人系総合Wikiのウィキテキスト(表形式)でデータを補完する',
                           nargs='+',
                           metavar='FILE')
    argparser.add_argument('--join-html',
                           help='素人系総合Wikiの一覧ページを読み込んで補完する',
                           nargs='+',
                           metavar='URL/HTML')

    argparser.add_argument('--hunter',
                           help='--join-*オプションを指定したときに作品タイトルは補完ファイルの'
                           'ものを採用する(Hunter系用)',
                           action='store_true')

    # ソート基準
    argparser.add_argument('--sort-key',
                           help='並び替えキー項目',
                           choices=('release', 'pid', 'title'))

    argparser.add_argument('--note',
                           help='エントリの最後かNOTEカラムにデータを追加する',
                           nargs='+',
                           metavar='DATA',
                           default=[])
    # 表形式出力装飾
    argparser.add_argument('-d', '--add-dir-col',
                           help='DIRECTORカラムを追加する (-t/-tt 指定時のみ)',
                           dest='dir_col',
                           action='store_true')
    argparser.add_argument('--add-column',
                           help='表に任意のカラムとデータを追加する (-t/-tt 指定時のみ)',
                           nargs='+',
                           metavar='COLUMN:DATA',
                           default=[])

    # 一覧ページへのリンク追加
    list_page = argparser.add_mutually_exclusive_group()
    list_page.add_argument('-s', '--series-link',
                           help='女優ページ形式でシリーズ一覧へのリンクを置き換え',
                           dest='series')
    list_page.add_argument('-l', '--label-link',
                           help='女優ページ形式でレーベル一覧へのリンクを置き換え',
                           dest='label')
    list_page.add_argument('--hide-list',
                           help='女優ページ形式で一覧ページへのリンクを追加しない',
                           action='store_true',
                           default=False)

    argparser.add_argument('--linklabel',
                           help='一覧ページへのリンクの表示名を置き換える')

    # 品番・副題など自動調整設定
    argparser.add_argument('--pid-regex',
                           help='品番自動生成のカスタム正規表現 (-t/-tt/-w 指定時のみ)',
                           nargs=2,
                           metavar=('PATTERN', 'REPL'))
    argparser.add_argument('--subtitle-regex',
                           help='副題自動生成のカスタム正規表現 (-t/-tt 指定時のみ)',
                           nargs=2,
                           metavar=('PATTERN', 'REPL'))
    argparser.add_argument('--disable-series-guide',
                           help='レーベル一覧ページからシリーズ一覧ページへのガイドを'
                           '追加しない (-t/-tt 指定時のみ)',
                           dest='series_guide',
                           action='store_false',
                           default=True)

    # 出力装飾
    argparser.add_argument('--without-header',
                           help='ヘッダ情報を出力しない',
                           dest='header',
                           action='store_false',
                           default=True)
    argparser.add_argument('--split',
                           help='1ページあたりのタイトル数 (デフォルト {})'.format(
                               SPLIT_DEFAULT),
                           type=int,
                           default=SPLIT_DEFAULT)

    # 補助チェック
    argparser.add_argument('-f', '--disable-follow-redirect',
                           help='ページのリダイレクト先をチェックしない',
                           dest='follow_rdr',
                           action='store_false',
                           default=True)
    argparser.add_argument('--disable-check-smm',
                           help='出演者情報がないときにSMMを検索しない',
                           action='store_false',
                           dest='smm',
                           default=True)
    argparser.add_argument('--check-rental',
                           help='レンタル先行メーカーでレンタル版じゃなかったのとき'
                           'レンタル版のリリースをチェックする',
                           action='store_true',
                           default=False)
    argparser.add_argument('--disable-check-bd',
                           help='Blu-ray版のときDVD版があってもパスしない',
                           action='store_false',
                           dest='pass_bd',
                           default=True)
    argparser.add_argument('--disable-check-listpage',
                           help='Wiki上の実際の一覧ページを探さない',
                           dest='check_listpage',
                           action='store_false',
                           default=True)
    argparser.add_argument('--disable-longtitle',
                           help='アパッチ、SCOOPの長いタイトルを補完しない',
                           dest='longtitle',
                           action='store_false',
                           default=True)
    argparser.add_argument('--fastest',
                           help='ウェブにアクセスするあらゆる補助処理を行わない',
                           action='store_true')

    argparser.add_argument('--recheck',
                           help='キャッシュしているリダイレクト先を強制再チェック',
                           action='store_true')

    # ブラウザ制御
    argparser.add_argument('-b', '--browser',
                           help='生成後、wikiのページをウェブブラウザで開く',
                           action='store_true')

    # その他
    argparser.add_argument('--clear-cache',
                           help='プログラム終了時にキャッシュをクリアする',
                           action='store_true')
    argparser.add_argument('-v', '--verbose',
                           help='デバッグ用情報を出力する',
                           action='count',
                           default=0)
    argparser.add_argument('-V', '--version',
                           help='バージョン情報を表示して終了する',
                           action='version',
                           version='%(prog)s {}'.format(__version__))

    args = argparser.parse_args(argv)

    verbose.verbose = VERBOSE = args.verbose

    if args.verbose > 1:
        libssw.VERBOSE = libssw.verbose.verbose = \
            dmm2ssw.VERBOSE = dmm2ssw.verbose.verbose = args.verbose - 1
    verbose('Verbose mode on')

    libssw.RECHECK = args.recheck

    if args.retrieval == 'url' and (args.cid or args.cid_l):
        emsg('E', '-U 指定時に --cid/--cid-l は指定できません。')

    # サービス未指定の決定
    # 引数にURLが与えられていればそれから判定
    # TSVやウィキテキスト入力でなければそれ以外ならセル版
    # TSVやウィキテキスト入力ならあとで作品情報から判定
    if args.keyword:
        if not args.service:
            if args.keyword[0].startswith('http://'):
                args.service = libssw.resolve_service(args.keyword[0])
            elif not (args.from_tsv or args.from_wiki):
                args.service = 'dvd'

        if (args.cid or args.cid_l) and '{}' in args.keyword[0]:
            verbose('args.cid check')
            # --row 未指定で --cid(-l) で連番指定の場合の自動決定
            # --start-{p,c}id だけでは連番と確定できないので何もしない
            if not args.row:
                args.row = int(args.keyword[1])
                verbose('row is set by cid: ', args.row)

    # ここで row 未指定時のデフォルト設定
    if not args.row:
        args.row = 1

    # start-pidは大文字、start-cidは小文字固定
    args.start_pid = args.start_pid.upper()
    args.start_pid_s = args.start_pid_s.upper()
    args.start_cid = args.start_cid.lower()

    args.last_pid = args.last_pid.upper()
    args.last_cid = args.last_cid.lower()

    # ヘッダを抑止するときはページ分割もしない
    if not args.header:
        args.split = 0

    if args.fastest:
        for a in ('follow_rdr', 'smm', 'check_rental', 'pass_bd',
                  'check_listpage', 'longtitle'):
            setattr(args, a, False)

    verbose('args: ', args)
    return args


class ExtractIDs:
    '''位置引数からIDと検索対象の抽出'''
    def __call__(self, keywords, is_cid=False):
        self.retrieval = None

        for k in keywords:

            if k.startswith('http://'):

                for i in libssw.get_id(k, is_cid, ignore=True):
                    yield i

                if not self.retrieval:
                    try:
                        self.retrieval = libssw.get_article(k)
                    except IndexError:
                        self.retrieval = 'keyword'
                    verbose('retrieval(extracted): ', self.retrieval)
            else:
                yield k

extr_ids = ExtractIDs()


def makeproditem(cid, service, sp_pid):
    pid = libssw.gen_pid(cid, sp_pid)[0]
    verbose('built cid: {}, pid: {}'.format(cid, pid))
    url = libssw.build_produrl(service, cid)
    return url, libssw.Summary(url=url, title='__' + pid, cid=cid, pid=pid)


def from_sequence(keywords, service, sp_pid):
    '''連続した品番の生成ジェネレータ'''
    try:
        base, start, end = keywords[:3]
    except ValueError:
        emsg('E',
             '--cid オプションで範囲指定する場合は'
             '「基底」、「開始」、「終了」の3個の引数が必要です。')

    step = keywords[3] if len(keywords) >= 4 else 1

    digit = max(len(n) for n in (start, end))
    base = re.sub(r'{}', r'{:0>{}}', base)
    for num in range(int(start), int(end) + 1, int(step)):
        cid = base.format(num, digit)
        yield makeproditem(cid, service, sp_pid)


def fmtheader(atclinfo):
    '''ヘッダ整形'''
    return '\n*{}'.format(
        '／'.join('[[{}>{}]]'.format(a, u) for a, u in atclinfo))


def build_header_actress(actids):
    '''女優名の再構成'''
    verbose('build_header_actress: {}'.format(actids))

    current = ''

    def _getnames(he):
        '''女優名とよみの文字列の取得'''
        nonlocal current

        for name, yomi in zip_longest(*libssw.get_actname(he)):
            yield name if yomi is None else '{}（{}）'.format(name, yomi)

        current = libssw.get_actname.current

    def _build(aids):
        '''女優名の整形とIDのペアを返す'''
        for aid in aids:
            resp, he = libssw.open_url(ACTINFOPAGE.format(aid))
            yield '／'.join(_getnames(he)), ACTLISTPAGE.format(aid)

    header = fmtheader(_build(actids))
    return current, header


def build_header(articles):
    '''ページヘッダ文字列の作成'''
    header = fmtheader(articles)
    return articles[0][0], header


def build_header_listpage(retrieval, service, name, lstid):
    url = libssw.join_priurls(retrieval, lstid, service=service)[0]
    return build_header(((name, url),))


def open_outfile(writemode, split, stem, num, suffix):
    '''指定した出力ファイル名を指定のモードでオープン'''
    pagen = (num // split + 1) if num >= 0 else 0
    verbose('num: ', num, ', split: ', split, ', pagn: ', pagen)
    fd = open('.'.join('{}'.format(p) for p in (stem, pagen, suffix) if p),
              writemode) if writemode else sys.stdout
    return fd, pagen


def truncate_th(cols):
    for col in cols:
        try:
            yield col.split(':')[1]
        except IndexError:
            yield ''


def print_header(fd, article, header, page):
    '''ページヘッダの出力'''
    article_name = article + (' {}'.format(page) if page > 1 else '')
    verbose('prt header article name: ', article_name)
    print('\n{}'.format(article_name),
          file=fd)
    print(header, file=fd)
    return article_name


def print_srchstr(titles, fd):
    '''検索用にDMM上のタイトルをコメントで残す(一覧ページ)'''
    print('\n// 検索用', end='', file=fd)
    for tdmm in titles:
        print('\n//', tdmm, end='', file=fd)


def main(argv=None):

    args = get_args(argv or sys.argv[1:])

    if args.out:

        # ファイル名に拡張子があったら分割
        split, suffix = (args.out.rsplit('.', 1) + [''])[:2]

        outf_act = split + '_actress'
        outf_tbl = split + '_table'

        if args.replace:
            writemode = 'w'
        else:
            chk = []
            if not args.wikitext:
                chk.append(args.out)
            else:
                if args.table:
                    chk.append(outf_tbl)
                if args.table != 1:
                    chk.append(outf_act)

            libssw.files_exists('w', *chk)
            writemode = 'x'
    else:
        outf_act = '_actress'
        outf_tbl = '_table'
        suffix = ''
        writemode = None

    ids = tuple(extr_ids(args.keyword, args.cid))
    verbose('ids: ', ids)

    if not args.retrieval:
        args.retrieval = extr_ids.retrieval or 'keyword'
    emsg('I', '対象: {}'.format(args.retrieval))

    # -L, -M , -U 以外では --not-in-series は意味がない
    if args.retrieval not in ('label', 'maker', 'url'):
        args.n_i_s = False
        verbose('force disabled n_i_s')

    if args.retrieval == 'actress':
        for i in ids:
            if i in libssw.HIDE_NAMES:
                emsg('W', '削除依頼が出されている女優です: {}'.format(
                    libssw.HIDE_NAMES[i]))
                ids.remove(i)

    # 除外対象
    no_omits = libssw.gen_no_omits(args.no_omit)
    verbose('non omit target: ', no_omits)

    # 品番生成用パターンのコンパイル
    sp_pid = (re.compile(args.pid_regex[0], re.I),
              args.pid_regex[1]) if args.pid_regex else None
    # 副題生成用パターンのコンパイル
    p_subtitle = (re.compile(args.subtitle_regex[0], re.I),
                  args.subtitle_regex[1]) if args.subtitle_regex else None

    # フィルター用パターン
    if args.filter_pid:
        filter_id = re.compile(args.filter_pid, re.I)
        fidattr = 'pid'
    elif args.filter_cid:
        filter_id = re.compile(args.filter_cid, re.I)
        fidattr = 'cid'
    else:
        filter_id = None
        fidattr = ''

    p_filter_pid_s = args.filter_pid_s and re.compile(args.filter_pid_s, re.I)
    p_filter_ttl = args.filter_title and re.compile(args.filter_title, re.I)

    # 作成開始品番
    if args.start_pid:
        key_id = args.start_pid
        key_type = 'start'
        kidattr = 'pid'
    elif args.start_cid:
        key_id = args.start_cid
        key_type = 'start'
        kidattr = 'cid'
    elif args.last_pid:
        key_id = libssw.rm_hyphen(args.last_pid)
        key_type = 'last'
        kidattr = 'pid'
    elif args.last_cid:
        key_id = args.last_cid
        key_type = 'last'
        kidattr = 'cid'
    else:
        key_id = None
        key_type = None
        kidattr = 'pid'

    not_key_id = libssw.NotKeyIdYet(key_id, key_type, kidattr)

    if args.add_column:
        add_header = '|'.join(c.split(':')[0] for c in args.add_column) + '|'
        args.add_column = tuple(truncate_th(args.add_column))
    else:
        add_header = ''
    verbose('add header: ', add_header)
    verbose('add column: ', args.add_column)

    listparser = libssw.DMMTitleListParser(no_omits=no_omits, patn_pid=sp_pid)
    seriesparser = libssw.DMMTitleListParser(patn_pid=sp_pid, show_info=False)

    # 作品情報取得用イテラブルの作成
    priurls = ''
    if args.from_tsv:
        # TSVファイルから一覧をインポート
        verbose('Import from_tsv()')
        p_gen = libssw.from_tsv(args.keyword)
    elif args.from_wiki:
        # ウィキテキストから一覧をインポート
        verbose('Import from_wiki()')
        p_gen = libssw.from_wiki(args.keyword)
    elif args.cid or args.cid_l:
        # 品番指定
        if '{}' in ids[0]:
            # '品番基準' 開始番号 終了番号 ステップ
            p_gen = from_sequence(ids, args.service, sp_pid)
        else:
            # 各cidからURLを作成
            p_gen = (makeproditem(c, args.service, sp_pid) for c in ids)
    else:
        # DMMから一覧を検索/取得
        verbose('Call from_dmm()')
        if args.retrieval in ('url', 'keyword'):
            priurls = args.keyword
        else:
            priurls = libssw.join_priurls(args.retrieval,
                                          *ids,
                                          service=args.service)
        p_gen = libssw.from_dmm(listparser, priurls,
                                pages_last=args.pages_last,
                                key_id=key_id,
                                key_type=key_type,
                                idattr=kidattr)

    # 作品情報の取り込み
    # 新着順
    products = libssw.OrderedDict2((u, p) for u, p in p_gen)
    emsg('I', '一覧取得完了')

    if not args.service:
        # TSVやウィキテキスト入力の場合の作品情報からサービス判定
        args.service = libssw.resolve_service(products.head().url)

    total = len(products)
    if not total:
        emsg('E', '検索結果は0件でした。')

    join_d = dict()

    if args.join_tsv:
        # join データ作成(tsv)
        verbose('join tsv')
        join_d.update((k, p) for k, p in libssw.from_tsv(args.join_tsv))

    if args.join_wiki:
        # join データ作成(wiki)
        verbose('join wiki')
        for k, p in libssw.from_wiki(args.join_wiki):
            if k in join_d:
                join_d[k].merge(p)
            else:
                join_d[k] = p

    if args.join_html:
        # jon データ作成(url)
        verbose('join html')
        for k, p in libssw.from_html(args.join_html, service=args.service):
            if k in join_d:
                join_d[k].merge(p)
            else:
                join_d[k] = p

    if (args.join_tsv or args.join_wiki or args.join_html) and not len(join_d):
        emsg('E', '--join-* オプションで読み込んだデータが0件でした。')

    if args.existings_html:
        # 既存の一覧ページから既出の作品情報の取得
        verbose('existings html')
        existings = set(k for k, p in libssw.from_html(args.existings_html,
                                                       service=args.service))

        if not existings:
            emsg('E', '--existings-* オプションで読み込んだデータが0件でした。')

    else:
        existings = set()

    # 作品情報の作成
    verbose('Start building product info')
    if not VERBOSE and args.wikitext:
        print('作成中...', file=sys.stderr, flush=True)

    wikitexts = []
    title_list = []
    series_set = set()
    series_urls = []
    rest = total
    omitted = listparser.omitted
    before = True if key_id else False

    dmmparser = dmm2ssw.DMMParser(no_omits=no_omits,
                                  start_date=args.start_date,
                                  start_pid_s=args.start_pid_s,
                                  filter_pid_s=p_filter_pid_s,
                                  pass_bd=args.pass_bd,
                                  n_i_s=args.n_i_s)
    dmm2ssw.sp_pid = sp_pid

    if args.retrieval in ('maker', 'label', 'series'):
        keyiter = libssw.sort_by_id(products)
    else:
        keyiter = iter(products)

    for url in keyiter:
        props = products[url]

        # 品番の生成
        if not props.pid:
            props.pid, props.cid = libssw.gen_pid(props.url, sp_pid)

        # 開始ID指定処理(--{start,last}-{p,c}id)
        if before:
            # 指定された品番が見つかるまでスキップ
            if not_key_id(getattr(props, kidattr)):
                emsg('I', '作品を除外しました: {}={} (id not met yet)'.format(
                    kidattr, getattr(props, kidattr)))
                omitted += 1
                rest -= 1
                continue
            else:
                before = False
                if key_type == 'start':
                    emsg('I', '開始IDが見つかりました: {}'.format(
                        getattr(props, kidattr)))
                else:
                    emsg('I', '最終IDが見つかりました: {}'.format(
                        getattr(props, kidattr)))
                    continue

        # 品番(pid/cid)が指定されたパターンにマッチしないものはスキップ処理(--filter-{p,c}id)
        if filter_id and not filter_id.search(getattr(props, fidattr)):
            emsg('I', '作品を除外しました: {}={} (filtered)'.format(
                fidattr, getattr(props, fidattr)))
            omitted += 1
            rest -= 1
            continue

        # 作品名が指定されたパターンにマッチしないものはスキップ処理(--filter-title)
        if args.filter_title and not p_filter_ttl.search(props.title):
            emsg('I', '作品を除外しました: title={} (filtered)'.format(
                props.title))
            omitted += 1
            rest -= 1
            continue

        # 一覧ページ内に既存の作品はスキップ(--existings-)
        if props.url in existings:
            emsg('I', '作品を除外しました: pid={} (already existent)'.format(
                props.pid))
            omitted += 1
            rest -= 1
            continue

        # 既知のシリーズ物のURLならスキップ (--not-in-series)
        if props.url in series_urls:
            emsg('I', '作品を除外しました: title="{}" (known series)'.format(
                props.title))
            omitted += 1
            rest -= 1
            continue

        if props.url in join_d:
            # joinデータがあるとデータをマージ
            props.merge(join_d[props.url])
            if args.hunter:
                props.title = join_d[props.url].title

        # 副題の生成
        if args.retrieval == 'series':
            # シリーズ一覧時のカスタムサブタイトル
            props.subtitle = libssw.sub(p_subtitle, props.title).strip() \
                if args.subtitle_regex else ''

        if args.wikitext:
            # ウィキテキストを作成
            libssw.inprogress('(残り {} 件/全 {} 件: 除外 {} 件)  '.format(
                rest, total, omitted))

            verbose('Call dmm2ssw')
            b, status, data = dmm2ssw.main(props, args, dmmparser)
            verbose('Return from dmm2ssw: {}, {}, {}'.format(
                b, status, data))
            # 除外対象だったとき、data は (key, hue) のタプルになる。

            if b:
                wikitexts.append(data)
            elif status == 404:
                wikitexts.append(data)
            else:
                emsg('I', '作品を除外しました: '
                     'cid={0}, reason=("{1[0]}", {1[1]})'.format(
                         props.cid, data))
                if args.n_i_s and data[0] == 'series':
                    # no-in-series用シリーズ作品先行取得
                    verbose('Retriving series products...')
                    series_set.add(data[1])
                    priurls = libssw.join_priurls('series',
                                                  data[1][0],
                                                  service=args.service)
                    series_urls.extend(
                        u for u, p in libssw.from_dmm(seriesparser, priurls))
                omitted += 1

        else:
            # 一覧出力
            title_list.append(props.tsv('url', 'title', 'pid', 'actress',
                                        'number', 'director', 'note'))

        rest -= 1

    if not VERBOSE and args.wikitext:
        print(file=sys.stderr)

    if wikitexts:
        # ウィキテキストの書き出し
        verbose('Writing wikitext')

        # アーティクル名の決定
        if args.retrieval == 'actress':
            # 女優ID指定:
            article_name, article_header = build_header_actress(ids)
        else:
            # その他
            if libssw.from_wiki.article:
                article_name, article_header = build_header(
                    libssw.from_wiki.article)
            elif args.retrieval == 'series':
                article_name, article_header = build_header_listpage(
                    args.retrieval, args.service, *wikitexts[0].series)
            elif args.retrieval == 'label':
                article_name, article_header = build_header_listpage(
                    args.retrieval, args.service, *wikitexts[0].label)
            elif args.retrieval == 'maker':
                article_name, article_header = build_header_listpage(
                    args.retrieval, args.service, *wikitexts[0].maker)
            elif listparser.article:
                article_name, article_header = build_header(
                    listparser.article)
            else:
                article_name = article_header = ''

        verbose('article name: ', article_name)
        verbose('article header: ', repr(article_header))

        if not libssw.le80bytes(article_name):
            emsg('W', 'ページ名が80バイトを超えています')

        # ヘッダ文字列の作成
        if args.header and args.table:
            table_header = \
                '|~{{}}|PHOTO|{}|ACTRESS|{}{}RELEASE|NOTE|'.format(
                    'SUBTITLE' if args.retrieval == 'series' else 'TITLE',
                    'DIRECTOR|' if args.dir_col else '',
                    add_header if add_header else '')

        # ソート
        if args.sort_key == 'title':
            # 第1キー:タイトル、第2キー:リリース日
            sortkeys = 'release', 'title'
        elif args.sort_key == 'release':
            # 第1キー:リリース日、第2キー:品番
            sortkeys = 'pid', 'release'
        elif args.sort_key == 'pid':
            sortkeys = 'release', 'pid'
        else:
            sortkeys = ()

        for k in sortkeys:
            wikitexts.sort(key=attrgetter(k))

        print()

        page_names = set()

        if args.table:
            # table形式

            titles_dmm = []

            if args.split and (args.row - 1) % args.split:
                fd, pagen = open_outfile(writemode, args.split,
                                         outf_tbl, args.row - 1, suffix)
            else:
                fd = io.IOBase()  # Dummy

            for j, item in enumerate(wikitexts, start=args.row - 1):
                verbose('Row #', j)

                if args.split and not j % args.split:
                    # ページ切り替え処理

                    # DMM上のタイトルを変更している作品のDMMタイトルをコメントで残す
                    if titles_dmm:
                        print_srchstr(titles_dmm, fd)
                        titles_dmm.clear()

                    if args.out:
                        fd.close()

                    fd, pagen = open_outfile(writemode, args.split,
                                             outf_tbl, j, suffix)

                    # ページヘッダの出力
                    page_names.add(print_header(fd,
                                                article_name, article_header,
                                                pagen))

                if not j % 10:
                    # 10件ごとの表ヘッダの出力
                    remainder = j % args.split
                    print(table_header.format(remainder
                                              if remainder else 'NO'),
                          file=fd)
                    verbose('Header: ', j)

                # 作品情報の出力
                print(item.wktxt_t, file=fd)

                if item.title_dmm:
                    titles_dmm.append(item.title_dmm)

            print('\n■関連ページ', file=fd)
            print('-[[]]', file=fd)

            if titles_dmm:
                print_srchstr(titles_dmm, fd)

            if args.out:
                fd.close()

        print()

        if args.table != 1:
            # 女優ページ

            if args.split and (args.row - 1) % args.split:
                fd, pagen = open_outfile(writemode, args.split,
                                         outf_act, args.row - 1, suffix)
            else:
                fd = io.IOBase()  # Dummy

            for j, item in enumerate(wikitexts, start=args.row - 1):
                verbose('Item #', j)

                if not item.url:
                    verbose('Empty entry')
                    continue

                if args.split and not j % args.split:
                    # ページ切り替え処理

                    if args.out:
                        fd.close()

                    fd, pagen = open_outfile(writemode, args.split,
                                             outf_act, j, suffix)

                    # ページヘッダの出力
                    page_names.add(print_header(fd,
                                                article_name, article_header,
                                                pagen))

                # 作品情報の出力
                print(item.wktxt_a, file=fd)

            if args.out:
                fd.close()

        if args.browser and page_names:
            # ブラウザで開く
            for p in page_names:
                libssw.open_ssw(p)

    else:
        # タブ区切り一覧の書き出し

        fd = open(args.out, writemode) if args.out else sys.stdout

        print(*title_list, sep='\n', file=fd)

        if args.out:
            fd.close()

    if args.n_i_s:
        print('** 見つかったシリーズ一覧(順不同)')
        for i, s in series_set:
            print('-[[{}]]'.format(s))

    # キャッシュディレクトリの削除
    if args.clear_cache:
        libssw.clear_cache()


if __name__ == '__main__':
    main()
