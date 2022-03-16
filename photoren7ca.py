#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
	todo:
	・ 設定情報の読み書きを configparser に引っ越し
	・3gp
	Exif情報が腐ってるかも．
	1947年とか2015年9月15日00時36分5秒とか．
	・subなり関数なりに切り出し．
	・移動した後，空ディレクトリが残った場合の掃除は？

2022/03/16(水)
	済 画面表意している処理対象ファイルの数を修正．

2021/07/17(土)
	済 細かい起動オプションをファイルに外だし．./photoren_default.txt
	これに伴い，ソース上の初期値は，/l だけを1にする．あとはdefaultファイルかコマンドラインで設定する．

2021/07/16(金)
	済 動画の時差．
		mp4ファイルの中身がじつはUTCではなく，ローカル時刻だった．
		んで，config/sourceファイルにオプションを新設する．",utc" をつけるとメタデータをUTCと見做して時差補正をする．なければそのままローカル値として使う．

2021/07/15(木)
	済 mp4_descripter.pyを使う．mutagenは捨てる．
	exiftoolもそのほか出来合いのものは使わない．自力でやる．
	get_tag_mp4()からmp4_descripterを呼び出すまではなんとかなった模様．問題は，どうやって値をスマートに戻すか．
	共通のグローバルか，関数の戻り値にクラスメンバを作る？？？


2021/07/08(木)
	済 gPRINT() PRINT()にFlagDebugの機能を取り込んたもの．
	mutagen で mp4のタグを集めてみる．動画フォーマット1個づつこうやって書くことになるのかな．

2021/07/07(水)
	済 単独でもphotoren.pyからでも起動できるようにmain()呼び出しを最後に追加しておいた．
	済 オプション引数の解析がおかしい．
	コマンドラインオプション ソースで初期設定しているデフォルト値をset側にもneg側にも変更できるように拡張．
	オプション変数を書き換える処理が冗長なのが気にらず書き直しを試みたが失敗．無駄に終わった．

2021/07/06(火)
	済 ファイルの選択，改名ルール，移動先の指定を汎用化．

	FlagShowAll タグ全部表示
	exifタグ make, model追加
	その他，pngやmp4等でtagが拾えない場合のエラーとラップを強化
	sourceFile_*_.txt	ExtSpec_*.txt から改名．拡張子だけという制限を外し，
		サブフォルダを含むかどうかを明示的に記述させるよう改めた．
	sourceDir_*_.txt	source_*.txt から改名．
	グローブで使えるワイルドカードはワイルドカードであって正規表現ではなかったさんざん書いて全部起きませんでしたボツ
	オプション変数だけを外部ファイルに出してimportするだけで設定変更をやりやすくしようと思ったんだけど
	importすると何かプレフィックスをつけなきゃいけなくなってめんどくさいからやめた

2021/07/05(月)
	済 動画系はタグが拾えないばかりかpillowがエラーで落ちる。トラップしてファイルタイムスタンプでごまかす。
	perlではexiftoolで時差の問題はあったけどタグは拾えてた。やっぱ何らかの対策は必要か。
2021/07/04(日)
	済 PRINT()出力がファイルに全部出力されずに終了してしまう．
	済 Dump_Log_And_Die()でPRINT()にflushオプションtrueを渡す．

	済 androidとwindowsで動きが違う．やっと動き始めた。
	試行錯誤多数．引数の整理．処理の分割

	get_filelist() ↓の警告が出る．するとその後ログが出なくなったり画面文字エンコードがおかしくなる．
		photoren7ca.py:491: FutureWarning: Possible nested set at position 12
	その対策？
		c:\> py -3 -m pip install pytest-pycodestyle
	これだけでは違いは無かった．わからんなー．
	warnings.simplefilter( 'ignore')で消すことはできるが，文字化けは変化無しだった．


2021/07/03(土) pythonに移植を開始．
	windows10 python39	をインストール．
		途中のオプションでpathに
		　c:\apps\python39\scripts;c:\apps\python39;
		を追加してある．既に拡張子　py, pymが実行可能として追加されているらしく．pyファイルを
		cmdから叩くとpythonが起動して実行を試みてくれる．
		けど，外部パッケージが入ってないから大抵は動かない．
		c:\....\>pip install PILLOW
		とかで，手動で必要なパッケージをインストールする必要がある．
		必要なもんなんだったら勝手にインストーラを起動位してくれても良さそうなもんだけどな．

	済 strip()の動きが納得いかない．"\n"が残る．strip( " \r\n\t" )としてもダメ．

"""

#######
#
# global vars.
#

## コマンドラインオプション，その初期値
FlagCc		 = 0	# カーボンコピーを実行
FlagDeleteTN = 0	# サムネイルの削除 ※廃止予定
FlagListOnly = 1	# リストするだけで変更をしない．
FlagDebug	 = 0	# デバッグ出力
FlagShowAll =  0	# EXIFtagを全部表示
LogFileName = "pr"	# ログファイルプレフィックス
ConfigDirName="config"	# 設定ファイルDir

## 実行環境
OsID	= ""		# 実行環境の識別
ScriptDir = ""		# ベースDir
FileSpecList = []	# 対象ファイルマスクパターン,時差補正オプションのリスト
SEP = "/"			# パスの区切り文字
FH_LOG	= 0 		# ログファイルのハンドル
SrcTnDir = None 	# カーボンコピー先のパス

## ファイル名置換辞書 キーワードと初期値
SubStituteTable = {}	# 改名テーブル 連想配列
## その初期値	行内コメントが書けないとはねー．
SubStituteTable_init = {
	"{YYYY}": "YYYY"	#	西暦4桁	こういう改行とコメントが書けるのかな．
,	"{YY}"	: "YY"	# 西暦2桁
,	"{MM}"	: "MM"	# 月2桁
,	"{DD}"	: "DD"	# 日2桁
,	"{hh}"	: "hh"	# 時2桁
,	"{mm}"	: "mm"	# 分2桁
,	"{ss}"	: "ss"	# 秒2桁
,	"{make}": "make"	# 製造者
,	"{model}": "model"	# 機種
,	"{base}": "base"	# 元のファイル名
,	"{ext}" : "ext" 	# 拡張子
}


####################################################
def main():

	global FlagCc
	global FlagDeleteTN
	global FlagListOnly
	global FlagDebug
	global FlagShowAll
	global LogFileName
	global ConfigDirName

	global SubStituteTable
	global SubStituteTable_init
	global OsId
	global SEP
	global FileSpecList
	global FH_LOG
	global SrcTnDir

	import os
	import shutil
	import sys
	import glob
	import re
	from pathlib import Path
	import codecs
	import warnings
	#sys.stdout = codecs.getwriter('utf_8')(sys.stdout) 	#error

	#
	# 警告エラーを無視する．blogがfutruewaringを出すと以降，文字出力が腐るため．
	# あら，これやっても警告は出なくなるけど，文字化けは変らずだ．
	#warnings.simplefilter('ignore')
	#
	# OS環境
	#
	ScriptDir = os.getcwd() 	## home location
	SEP = os.path.sep			## slash or back-slash
	OsId = get_OsId()

	# コマンドラインオプションの展開
	ermsg = get_options()
	if( ermsg ):
		print( ermsg )
		sys.exit( 0 )

	#
	# ログファイルを開く
	#	指定したファイル名の後ろに実行環境名をくっつけておく．
	#	標準出力を指定したログファイル名に置き換えて処理を進める．
	#	PRINT()関数内で標準出力とログファイルに同時に出力してる．

	LogFileName = LogFileName + "_" + OsId + ".log"
	f = codecs.open('test', 'ab', 'cp932', 'ignore')
	FH_LOG = codecs.open( LogFileName, "wb", 'utf-8', 'ignore' )

	PRINT( "Photo Rename starting up...\n" )

	#
	# 実行環境の確認
	#
	PRINT(	 " script  [", os.path.basename( __file__ ) \
		, "]\n os      [", OsId \
		, "]\n args    [", ",".join(sys.argv)	\
		, "]\n base dir[", os.path.dirname( __file__ ) \
		, "]\n conf dir[", ConfigDirName	\
		, "]\n log file[", LogFileName	\
		, "]\n options [cc=" + str(FlagCc) + " DelTN=" + str(FlagDeleteTN) \
					+ " ListOnly=" + str(FlagListOnly) + " Debug=" + str(FlagDebug) \
					+ " ShowAll=" + str(FlagShowAll) \
		, "]\n" )

	# タイムゾーン．あれれ？
	#$ENV{"TZ"}="JST-9";

	# 設定ファイルの保存場所
	ConfigPath = ScriptDir + SEP + ConfigDirName + SEP

	# 対象ファイルのディレクトリ．末尾に/は付けない．
	#	5a サブディレクトリはすべて再帰検索する．
	#	   見つからない場合は単純無視．
	SourceDirList = get_config( ConfigPath + "sourceDir_" + OsId + ".txt", 1 )

	# 対象ファイルの仕様．ファイルを特定するワイルドカード．perl時代にあった拡張子部分を温存するための"()"は廃止した．
	#	複数の種類のファイルを指定可能とするため，設定ファイルも複数行指定できるようにした．
	# メタデータのUTCかローカルか問題を人間の管理に任せる．オプション utc を付けたらそのメタデータはUTCとして扱うことにした．
	FileSpecList = []
	tmp_FileSpecList = get_config( ConfigPath + "sourceFile_" + OsId + ".txt", 1 )
	# ファイル名とオプションを分離しておく
	for s in tmp_FileSpecList:
		if( "," in s ):
			s_file, s_opt = s.split( "," )
		else:
			s_file = s; s_opt = ""
		s_file = s_file.strip()
		s_opt = s_opt.strip()
		FileSpecList.append( [ s_file, s_opt ] )

	# 置換書式．途中にサブディレクトリを含むことができる．
	#	todo 現在は全てのソースに対して1個だけ．ソースファイル名，ソースディレクトリ毎に拡張するかも．
	# 指定が無ければ初期値で置換する．
	#	重複回避のための連番と，拡張子は自動的に付加する．んで，ここには記述しないこと．
	DestSubstSpec = get_config( ConfigPath + "destSubst_" + OsId + ".txt", 0 )
	if( DestSubstSpec == "" ):	#デフォルト値
		DestSubstSpec = "{YYYY}" + SEP + "{YYYY}{MM}{DD}" + SEP + "{YYYY}{MM}{DD}-{hh}{mm}{ss}"

	# 改名テーブル 連想配列 辞書初期化
	SubStituteTable = SubStituteTable_init

	# 置換後の移動先のベースディレクトリ．末尾に/は付けない．
	# 1個だけ．
	DestDir = get_config( ConfigPath + "dest_" + OsId + ".txt", 0 )
	#DestDir = "./p"				# for debug

	# バックアップ用のカーボンコピー
	# ※移動に成功したあとのファイルに対するものであることに注意
	# ※LANなどを想定しているため，エラー発生しても停止はしないで無視するだけとする．
	SrvDir = get_config( ConfigPath + "destCc_" + OsId + ".txt", 0 )
	if( SrvDir == "" ): #存在しない場合はコピーしない
		FlagCc = 0

	# 対象ファイルのサムネイル置き場		※廃止予定
	# ※画像キャッシュの掃除が目的だったがandroidの最近のバージョンでは無用となってる．廃止削除しても良いかも
	#SH-13C #my $srctndir = "/mnt/sdcard/DCIM/.thumbnails";
	SrcTnDir =			SEP + "sdcard" + SEP + "external_sd" + SEP + "DCIM" + SEP + ".thumbnails"

	##
	## ソースDirを順にまわって対象のファイルを集め，改名と移動する
	## 5a ソースディレクトリを複数指定可能に，かつ，再帰検索して下位のフォルダ内も検索対象とした．
	##
	numfilesFound = 0		# ファイル総数
	numFilesDone = 0	# 処理した数
	srcfilelist = []	# 対象ファイル名のリスト
	tmp_count = 0

	dPRINT( "---loop start---\n" )
	for part_dir in SourceDirList:	# ソースDirリストから1個ごとに

		#
		# ソースDirの中にある対象ファイルをすべて集めて一つのファイルリストにする
		#
		srcfilelist = get_filelist( part_dir )	#ソースDirの中の対象ファイルのリスト
		numfiles = len( srcfilelist )
		numfilesFound += numfiles

		if( PRINT( " --files[" + str( numfiles ) + "] found in[" + part_dir + "]\n" ) ):
			for tmp_file, opt in srcfilelist:
				tmp_count += 1
				PRINT( "  ( " + str( tmp_count ) + ") [ " + tmp_file + "] (" + opt + ")\n" )

		##
		## ファイル毎に改名と移動
		##
		dPRINT( " --build new name--\n" )
		for SrcFullPathName, opt in srcfilelist:

			#
			#ソースファイルの親Dir，ベースファイル名，拡張子
			# Dir名
			SrcDir	= os.path.dirname( SrcFullPathName )
			# ファイル名 パス無し．拡張子有
			SrcName = os.path.basename( SrcFullPathName )
			# ファイル名，拡張子
			SrcBase, SrcExt = os.path.splitext( SrcName )
			# ピリオドがついてるんで取り除いておく
			SrcExt = SrcExt.replace( ".", "" )

			SubStituteTable["{base}"] = SrcBase
			SubStituteTable["{ext}" ] = SrcExt
			# これは無意味．
			# 置換してる段階では何個かぶってるかわからない．
			#SubStituteTable["{seq}" ] = "000"

			#PRINT( "===file[" + SrcDir + "]" + SEP + "[" + SrcBase + "].[" + SrcExt + "]\n" )

			#
			# ファイルの種類に応じてメタデータを拾い，置換辞書を作る
			#
			Get_tag( SrcExt, SrcFullPathName, opt )

			#
			# 置換．ファイル名書式に含まれるキーワードを辞書を引いて置換える．
			#
			dPRINT( " SubStituteInfo->>\n" )
			DestPathName = DestSubstSpec		#初期値は置換書式文字列
			for key, value in SubStituteTable.items():
				DestPathName = DestPathName.replace( key, value )

				dPRINT( "   subst[" + key + "] val[" + value + "]\n" )
			dPRINT( " SubStituteInfo-<<\n" )

			#
			# 書式にDir区切り文字が含まれていた場合はサブDirを作る必要があるが，
			# どうせ移動先もどこかのDirなのでまとめて作る．．
			#
			DestFullBaseName = DestDir + SEP + DestPathName 		# フルパスだけど拡張子はまだつけない
			DestFullDirName  = os.path.dirname( DestFullBaseName )

			dPRINT( " to dir[" + DestFullDirName + "], part name[" + os.path.basename( DestFullBaseName ) + "]\n" )

			#
			# 移動先のベースと，置換先のファイル名を元に最終的な親Dirを求め．存在しなければ知らん顔して作る．
			#
			ermsg = ""
			try:
				os.makedirs( DestFullDirName, exist_ok = True )
			except:
				ermsg = "Destination Dir create failed.[" + DestFullDirName + "]"
				PRINT( "\nWaring:" + ermsg + "\n" );
				pass
			#
			# Dir作成に成功したら最終的なファイル名を決める．
			# 必要に応じて連番を振る．
			#
			if( ermsg == "" ):
				# 試しに連番無しでファイル名を組み立てて，かぶったらかぶらなくなるまで連番を増やす
				DestFullPathName = DestFullBaseName + "." + SubStituteTable["{ext}"]
				SeqNumber = 0
				while( os.path.isfile( DestFullPathName ) ):
					SeqNumber += 1
					DestFullPathName = DestFullBaseName + "_{:03d}.".format( SeqNumber ) + SubStituteTable["{ext}"]
					# todo リミットチェック

				dPRINT( " new fullname[" + DestFullPathName + "]\n" )

				#
				# 改名と同時に移動．
				#
				# sl4a perlではOSバージョンが変る度にいろいろ問題があったけど
				# python Android11では非常にすんなりと動いてるようだ．気味悪いな．
				#PRINT( " --rename and move--\n" )

				# リストだけなのか実際に移動したのか，失敗したのかを追加表示しておく．
				if( FlagListOnly ): 				# 予行演習モード
					result = "-"
					numFilesDone += 1
				else:
					try:
						shutil.move( SrcFullPathName, DestFullPathName )
						result = "o";
						numFilesDone += 1
					except:
						ermsg = " Move faild."
						result = "x";
						pass
				#
				# 移動結果もくっつけて表示
				#
				PRINT( "   " + result + " " + SrcFullPathName + " -> " + DestFullPathName + "\n" )

			#
			# 何かに失敗してたらここで終わる
			#
			if( ermsg != "" ):
				Dump_Log_And_Die( "\nError:" + ermsg + "\n" );
			#
			# 移動成功したファイルについて，
			# LAN接続が生きてればそっちにもバックアップコピー
			# 何かエラーが起きたら無視してそれ以降の呼び出しをやめる．
			#
			if( FlagCc == 1 ):
				FlagCc = CarbonCopy( DestDir, DestFullPathName.replace( DestDir,""), SrvDir )
	#
	# remove THumbnails if required
	#
	if( FlagDeleteTN ):
		Delete_Thumbnail()

	tmp_ListOnly = " [ListOnly]" if( FlagListOnly == 1 ) else ""

	PRINT( "\n " \
	 + " Files total[" + str( numfilesFound ) + "]\n" \
	 + "      renamed[" + str( numFilesDone ) + "]" + tmp_ListOnly + "\n" \
	 + "End of Photo Rename.\n" );
	FH_LOG.close()
	sys.exit( 0 )
###################
#
# 動画ファイルのタグはEXIFでは拾ってくれないんだそうな
# 融通効かねえなー。
#
""" まだ書きかけ
def Get_MovieInfo( filepath ):
	from mp4file.mp4file import Mp4File

	movietaglist = file.find(".//%s//data" % name)
	#return atom.get_attribute("data")

	title = find_metadata_atom(file, "title")
	tvshow = find_metadata_atom(file, "tvsh")
"""

###################
#
# 拡張子をもとにタグ集め処理を振り分ける
#
#	args
#		in	srcExt	拡張子
#		in	fullpath	ファイルフルパス名
#		in	opt		タグオプション
#			"utc" 時刻はUTCからローカルへの変換が必要
#
#	return
#		なし

def Get_tag( srcExt, fullpath, opt ):

	import re
	global SubStituteTable

	tag_date = ""
	tag_make = ""
	tag_model = ""

	# 面倒だからひとまず大文字に
	srcExt = srcExt.upper()

	if( re.search( r"(JP.+|PN.+)", srcExt ) ):
		tag_date, tag_make, tag_model = get_tag_exif( fullpath )
	else:
		tag_date, tag_make, tag_model = get_tag_mp4( fullpath, opt ) #それ以外全部　mp4, 3gp,...Quicktime由来の動画を想定


	if( tag_date == "" ):
		# 代わりにファイルのタイムスタンプを使う
		#
		tag_date = Get_FileTimeStamp( fullpath )
		#
	# 日付文字列を確定
	#
	# Exif情報が見つからないならファイルのタイムスタンプを使う．
	# Exif情報が見つかっていても値が変だったら……これがなかなか問題．
	#
	#	0123456789012345678
	#	YYYY:MM:DD hh:mm:ss
	#
	# 置換テーブルを用意する
	#
	dPRINT( "tag_date[" + tag_date + "]\n" )

	SubStituteTable["{YYYY}"] = tag_date[0:4]
	SubStituteTable["{YY}"	] = tag_date[2:4]
	SubStituteTable["{MM}"	] = tag_date[5:7]
	SubStituteTable["{DD}"	] = tag_date[8:10]
	SubStituteTable["{hh}"	] = tag_date[11:13]
	SubStituteTable["{mm}"	] = tag_date[14:16]
	SubStituteTable["{ss}"	] = tag_date[17:19]
	SubStituteTable["{make}" ] = tag_make
	SubStituteTable["{model}"] = tag_model

###################
def get_tag_mp4( filepath, opt ):
	"""
	mutagen() を使ってメタデータを集める．
	アクセスエラーがあっても警告は出すが処理は停めない．

	args
	  filepath	in	対象ファイルのフルパス名
	  opt		in	オプション
	  				"utc"	メタタグはUTCなんでローカルへ変換を行う
	return
	  ( date, make, model )

	"""

	from datetime import datetime
	import mp4_descripter as mp4

	mp4taglist =mp4.gettag( filepath, opt  )

	# 日付を文字列に整形 "yyyy:mm:dd hh:mm:ss"	todo この書式は日本以外でも同じ？
	#dc = datetime.fromtimestamp( mp4taglist["CTime"] )
	#dm = datetime.fromtimestamp( mp4taglist["MTime"] )

	dPRINT( " mp4 tag list->>\n" )
	dPRINT( "Duration = ", str(mp4taglist["Duration"]), "\n" )
	dPRINT( "ctime    = ", mp4taglist["CTime"], "\n" )
	dPRINT( "mtime    = ", mp4taglist["MTime"], "\n" )
	dPRINT( "Make    = ", mp4taglist["Make"], "\n" )
	dPRINT( "Model   = ", mp4taglist["Model"], "\n" )
	dPRINT( " <<--mp4 tag list\n" )
	tag_date = mp4taglist["CTime"]

	tag_make = ""		#まだない
	tag_model = ""

	dPRINT( " mp4 tag list-<<\n" )

	return tag_date, tag_make, tag_model


###################
# Exif情報を拾って，置換辞書を作る
# EXifアクセスエラーがあっても警告は出すが処理は停めない．
#
# args
#	filepath	in	対象ファイルのフルパス名
# return
#	( date, make, model )
#
# 外部変数
#	ermsg	エラー発生時にメッセージ文字列を設定．
#	SubStituteTable	辞書
#
def get_tag_exif( filepath ):

	from PIL import Image
	from PIL.ExifTags import TAGS

	global FlagDebug

	EXIF_datetaglist = ( \
		"DateTimeOriginal" \
	,	"DateTimeDigitized" \
	,	"DateTime" \
	)

	#
	# Exif情報を取得
	#
	tag_date = ""
	tag_make = ""
	tag_model = ""
	try:
		img = Image.open( filepath )
		SrcExifList = img._getexif()
		img.close()
	except:
		PRINT( "Warning: getExif: No info found.[" + filepath + "]\n" )
		SrcExifList = {}	# 空に初期化しておく
		pass
	#
	# 可読形式に変換．
	# todo 無駄だからコードを一度調べればいいんではないだろうか．
	# todo TAGS.get()で名称文字に変換されないタグもある。結構いい加減かも。
	# だったら最初に目的のタグのidだけしらべておけば
	# 不要なタグ全部拾い集める必要は無さそう。
	# まぁ、タグ一覧が欲しいって時もあるんだろうけどね。
	# コード番号だけ調べて、この処理は不要にしたら？
	#
	exif_table = {} #連想配列

	dPRINT( " exifInfo->>\n" )
	if( SrcExifList is None ):
		dPRINT( " none\n" )
	else:
		for tag_id, tag_value in SrcExifList.items():
			tag = str( TAGS.get( tag_id, tag_id ) )
			if( FlagDebug or FlagShowAll ):
				if( "DATE" in tag.upper())or( FlagShowAll ) :	#たくさん出てくるんで日付関係に限定する
					PRINT( "  exif[" + str(tag_id) + " : " + tag + " = "  + str(tag_value) + "]\n" )
			exif_table[tag] = str(tag_value)

		#
		# 今のところ，欲しいのは撮影日だけ
		# なんで違うんだろう？ ["CreateDate"]
		# タグ名がブレるんで適当に選ぶ

		for t in EXIF_datetaglist:
			if( t in exif_table.keys() ):
				v = exif_table[t]
				if( v != "" ):
					tag_date = v
					break

		tag_make  = exif_table["Make"  ] if( "Make"  in exif_table.keys() ) else ""
		tag_model = exif_table["Model"] if( "Model" in exif_table.keys() ) else ""
	dPRINT( " exifInfo-<<\n" )

	return tag_date, tag_make, tag_model

######################################################
#
# get time stamp from file.(alternative if EXIF not found)
#
# args: 	in full path string of file that already exists.
# return:	regular time-stamp string
#
def Get_FileTimeStamp( fullpathname ):
	import os
	import datetime

#try:
	dt_internal = os.path.getmtime( fullpathname )
	dt_string	= str(datetime.datetime.fromtimestamp( dt_internal ))
#except:
	#dt_internal = ""
	#dt_string = "1900/00/00 00:00:00"
	#pass
	dPRINT( "Get_FileTimeStamp raw[" + str(dt_internal) + "] [" + dt_string + "]\n")
	return dt_string
######################################################
#
# ベールフォルダ DirLookingFor 配下から改名対象のファイルを差が出して fillist に集積する．
#
#	args	DirLookingFor	in	start point for search
#			※pythonではglobが使えるんでここで再帰関数にする必要は無くなった．

#	return	filelist
#
#	global in FileSpecList		RegEx filepattern list about looking for.
#
#	usage	fileList = get_filelist( "C:\neko" )
#			for file in filelist:
#				PRINT( "found " + file + "\n" )
#
def get_filelist( DirLookingFor ):

	import os
	import glob
	import re
	global FlagSpecList

	filelist = []

	dPRINT("get_filelist[" + DirLookingFor + "]\n" )

	# パスの下にマスクを付けて検索．
	for mask, opt in FileSpecList:
		dPRINT( " pattern[" + DirLookingFor + mask + "]\n" )

		for fname in glob.glob( DirLookingFor + mask, recursive = True ):

			# マスクパターンにひっかかったやつだけをリストに追加
			# ディレクトリ他は無視
			if( os.path.isfile( fname ) ):

				dPRINT( "   found[" + fname + "](" + opt + ")\n")
				filelist.append( [ fname, opt ]  )
				#break
	return filelist
#######################################################
#
# 設定ファイルを行単位で読み込んで，
#	"#"以降はコメント行として無視し，
#	先行する白文字を削除し，
#	その他の有効な行だけをリストにして返す．
#	ただし，フラグによって返す数を選択できる．
#
#	args	in filename 	設定ファイル パス
#			in FlagMulti	!=0 見つかったリストを全部
#							でなければ	最初の1個だけ
#	return	itemlist
#
#	todo Pythonにはiniファイルのアクセス関数があるらしい．そっちに引っ越しする？
#
def get_config( filename, FlagMulti ):

	global FlagDebug

	itemlist = []
	ermsg = ""

	dPRINT( "get_config( source[", filename, "] multi[", str(FlagMulti), "]\n" )

	try:
		fh = open( filename, "r" , encoding = "UTF-8" )
	except:
		ermsg = filename
		dPRINT( "  .. error:\n" )
		pass	#ファイルが読めなくても中断はしない

	if( ermsg == "" ):

		items = fh.readlines()
		lines = 0
		#PRINT( "items[" + str(items) + "]\n" )
		for s in items:
			lines += 1
			n = s.find( "#" )	# 見つかればその位置，見つからなければ-1を返す．
			if( n >= 0 ):		# コメント部分があれば消去する
				s = s[:n]
			s = s.strip()		# " \t\r\n" 一通り消してくれる模様
			if( len( s ) > 0 ): 	# 最後まで残っているのは希望だそうだ
				dPRINT( " item[" + str(lines) + "] [", s, "] len[", str(len( s )), "]\n" )
				itemlist.append( s )
				if( not FlagMulti ):	#1個だけの時はリストではなく要素だけを返す
					return itemlist[0]
	return itemlist
#######################################################
#
# ファイルハンドルを始末して終了する．
#	ログ出力をPRINT()にしたんでこの関数は無意味になった
#	この関数の中で終了もさせないようになった．
#	……もう必要無いかもね．
#	──と，思ったんだけどやっぱり復活．この関数を使うとそこで終了．
#
#	args
#		msg 	in 出力メッセージ
#	return	なし
#
#	外部参照
#		FH_LOG	ログファイルハンドル

def Dump_Log_And_Die( msg ):

	import sys
	global FH_LOG

	PRINT( msg, quit = True )

######################################################
#
# PRINT() print()の引数を減らして整形を無効化したバージョン
# ログファイルに同じ内容を平行して出力する．
#	args
#		print()と同じ．ただし，引数のデフォルト値を書換える．
#			flush は quitに変える．
#		quit = True 元のperlのdieと同じく，出力バッファをフラッシュしてから全終了する

def PRINT( *msgs, sep = "", end = "", file = "", quit = False ):

	import sys
	global FH_LOG	#出力先ファイルハンドル デフォルト=sys.stdou

	sep_arg = sep	#sep
	end_arg = end	#end
	flush_arg = quit

	#
	# 複数のオブジェクト引数が1個のタプルになって渡ってきてるんで，
	# join()を使って文字列に組み立て直してから出力する．
	#
	print( "".join(msgs), sep = sep_arg, end = end_arg, file = FH_LOG, flush = flush_arg )	#log file
	print( "".join(msgs), sep = sep_arg, end = end_arg )									#file = sys.stdout

	#
	# 終了指定があればここでおしまい
	#
	if( quit ):
		FH_LOG.close()
		sys.exit(0)

######################################################
#
# dPRINT()
# デバッグフラグが有効なときだけ出力するPRINT()
# デバッグ中の手の込んだ出力を助けるために，デバッグフラグ値を返す
#	returns
#		0	デバッグ中ではない
#		!=0 デバッグ中

def dPRINT( *msgs, sep = "", end = "", file = "", quit = False ):

	global FlagDebug

	if( FlagDebug ):
		import sys
		global FH_LOG	#出力先ファイルハンドル デフォルト=sys.stdou

		sep_arg = sep	#sep
		end_arg = end	#end
		flush_arg = quit

		#
		# 複数のオブジェクト引数が1個のタプルになって渡ってきてるんで，
		# join()を使って文字列に組み立て直してから出力する．
		#
		if( FH_LOG	!= 0 ):
			print( "".join(msgs), sep = sep_arg, end = end_arg, file = FH_LOG, flush = flush_arg )	#log file
		print( "".join(msgs), sep = sep_arg, end = end_arg )									#file = sys.stdout

		#
		# 終了指定があればここでおしまい
		#
		if( quit ):
			FH_LOG.close()
			sys.exit(0)

	return FlagDebug

######################################################
#
# hardware platform
# 動作プラットフォームの違いをここで吸収する．
# os名はperl時代に使ってたやつを尊重する
#
def get_OsId():

	import os

	# 実行環境の識別	python	perl
	#		Linux	....posix	android
	#		MSWin32 ....nt		Windows10
	# perlとPythonで違うんでここで吸収する
	OSID_MSWIN_pl	= "MSWin32" 	# Windows perlでのOS名
	OSID_MSWIN_py	= "nt"			# Windows pythonで
	OSID_ANDROID_pl = "linux"		# android perlでのOS名
	OSID_ANDROID_py = "posix"		# androif pythonで
	OSID_ANDROID	= OSID_ANDROID_py	# これを使う

	if( os.name == OSID_ANDROID ):
		return OSID_ANDROID_pl
	else:
		return OSID_MSWIN_pl
#########################
#
# 端末内の改名&移動の他に，もう1箇所，コピーを同じツリー構造で保存する．
# LANなどの接続が不確かな場所も想定されるため，エラー発生しても無視して先に進む．
#	既に正常にrename,moveが完了したファイルをsrcとする．
#	下の例ではソースファイルは次の場所に格納される
#			\\srv\share\dir\subdir\y\m\d\yms-hms.jpg
#	args
#		srcBaseDir	in	コピー元 ツリーベースDir					c:\doc\photo\
#		srcSubPath	in	コピー元 ツリーベース以下パスファイル名 	y\m\d\ymd-hms.jpg
#		DestBaseDir in	コピー先 ツリーベースDir					\\srv\share\doc\photo\
#	return
#		1	成功
#		0	失敗した
def CarbonCopy( srcBaseDir, srcSubPath, DestBaseDir ):

	import os

	#
	# コピー先のフルパスを仮に組み立ててみる
	#
	destFullPathName = DestBaseDir + srcSubPath
	PRINT( "Carboncopy to [" + DestBaseDir + "][" + srcSubPath + "]\n" )

	#
	# コピー先の親Dir
	#
	DestFullDirName  = os.path.dirname( destFullPathName )

	#
	# コピー先の親dirを掘る．
	# 作れなければそこでおしまい．
	#
	ermsg = ""
	try:
		os.makedirs( DestFullDirName, exist_ok = True )
	except:
		ermsg = "cc Dir create failed.[" + DestFullDirName + "]"
		PRINT( "\nWaring:" + ermsg + "\n" );
		pass

	if( ermsg == "" ):
		#
		# コピーする
		#
		# リストだけなのか実際に移動したのか，失敗したのかを追加表示しておく．
		if( FlagListOnly ): 				# 予行演習モード
			result = "-"
		else:
			try:
				#コピー先は 完全ファイル名 を指定する
				PRINT( " cc [" + srcBaseDir + "][" + srcSubPath + "] -> [" + destFullPathName + "]\n" )

				shutil.copyfile( srcBaseDir + srcSubPath, destFullPathName )
				result = "o";
			except:
				ermsg = "cc copy failed."
				result = "x";
				pass

		#
		# 移動結果もくっつけて表示
		#
		PRINT( "cc " + result + " " + destFullPathName + "\n" )

	#
	# 何かに失敗してたら以降は触らない．ローカルの処理が残っているかも知れないんで終了はしない．
	#
	if( ermsg != "" ):
		PRINT( "\nWarning:" + ermsg + "\n" );
		return 0	#一度でもエラー発生したら以降はもう呼び出ししない
	else:
		return 1
########################
#
# 昔のandroidが画像ファイルの移動に対し，メディアストレージの更新が遅かったり，
# 既存のサムネールキャッシュとの整合が崩れたりすることがあったときの名残．
# 今日では無用と思われる．廃止予定．
#
def Delete_Thumbnail():

	import os
	global SrcTnDir
	global FlagListOnly
	global SEP

	PRINT( "delete Thumbnails..\n" )
	if( not os.path.isdir( SrcTnDir ) ):
		Dump_Log_And_Die( "Warning:thumbnail dir not found.[" + SrcTnDir + "]\n" )
	else:
		if( FlagListOnly ): 				# 予行演習モード
			PRINT( "  Now List Only mode.　Or will be delete:[" + SrcTnDir + "]\n" )
		else:
			try:
				os.rmtree( SrcTnDir + SEP )
			except:
				Dump_Log_And_Die( "Error: remove thumbnail dir.[" + SrcTnDir + "]\n" )
######################################################
#
# コマンドラインオプション
#	return
#		なし．異常値を見つけたらヘルプメッセージを返す．呼び出し元で後始末して終了すること．

#	外部変数
#	オプション値に相当する変数をここで設定する．デフォルト値は現在の値．
#	オプションにキーワードが現れた場合にだけ，変数値をキーワードの値で変更する．

def get_options():

	import os
	import sys

	global FlagCc
	global FlagDeleteTN
	global FlagListOnly
	global FlagDebug
	global FlagShowAll
	global LogFileName
	global ConfigDirName
	global SEP

	# 引数のデフォルト値．
	# 外だしファイル *_default.py が存在したらそっちを優先する．
	default_valuefilename = "." + SEP + "photoren_default.txt"
	if( os.path.isfile( default_valuefilename ) ):
		print( " Default Options overwrites from:" + default_valuefilename )
		items = []
		items = get_config( default_valuefilename, True )
		for KeyAndValue in items:
			key, val = KeyAndValue.split( "=" )
			key = key.strip()
			val = val.strip()
			if(   key == "FlagDeleteTN"	):	FlagDeleteTN	= int( val )
			elif( key == "FlagListOnly"	):	FlagListOnly	= int( val )
			elif( key == "FlagDebug"	):	FlagDebug		= int( val )
			elif( key == "FlagShowAll"	):	FlagShowAll		= int( val )
			elif( key == "LogFileName"	):	LogFileName		= val
			elif( key == "ConfigDirName"):	ConfigDirName	= val

	"""
	print(
	 "FlagCc	=",	FlagCc
	, "\nFlagDeleteTN	=",	FlagDeleteTN
	, "\nFlagListOnly	=",	FlagListOnly
	, "\nFlagDebug	=",	FlagDebug
	, "\nFlagShowAll	=",	FlagShowAll
	, "\nLogFileName	=",	LogFileName
	, "\nConfigDirName=",	ConfigDirName
	)
	"""
	ermsg =  "\nusage " + os.path.basename( sys.argv[0] ) + " [[argments]...]\n"	\
		 " /c[-] copy also to backup.[or not]\n"	\
		 " /t[-] delete thumbnails.  [or not]\n"		\
		 " /l[-] listing only, do not move.[or not]\n"	\
		 " /d[-] show further info.[or not]\n"				\
		 " /s[-] show all tag data.[or not]\n"	\
		 " /fxx  log file prefix xx instead [" + LogFileName + "] as default.\n"	\
		 " /pxx  dir xx of parameter files instead [" + ConfigDirName + "] as default.\n"	\
		 " /h or else show this message.\n" \
		 " ---\n"	\
		 " See default valu file in[" + default_valuefilename + "]" \
		 " \n     configration files in[." + os.path.sep + "config" + os.path.sep + "*.txt].\n"

	if( len( sys.argv ) > 1 ):
		for argment in sys.argv[1:]:
			if(   "/c" == argment[0:2] ): FlagCc	   = 0 if( "-" in argment[2:3] ) else 1
			elif( "/t" == argment[0:2] ): FlagDeleteTN = 0 if( "-" in argment[2:3] ) else 1
			elif( "/l" == argment[0:2] ): FlagListOnly = 0 if( "-" in argment[2:3] ) else 1
			elif( "/d" == argment[0:2] ): FlagDebug    = 0 if( "-" in argment[2:3] ) else 1
			elif( "/s" == argment[0:2] ): FlagShowAll  = 0 if( "-" in argment[2:3] ) else 1
			elif( "/f" == argment[0:2] ): LogFileName  = argment[2:]
			elif( "/p" == argment[0:2] ): ConfigDirName= argment[2:]
			else:
				#異常な値が含まれていたらヘルプメッセージを表示してそこで終了してもらう
				#Dump_Log_And_Die( ermsg )
				return ermsg
	# 引数無し，または正しい値だけだったら正常終了．
	return None
##############################
#
# コマンドラインオプションの設定or解除
# 引数の値を書き換えることに注意
#
#	args
#		in	keyword 	オプション文字列	"/?"
#		in	keyword_neg そのオプションを抑止する意味の記号 "-"
#		in	argv		引数文字列
#		io	var 		オプション変数 0 or 1
#
# return	== 0 このオプションが見つからなかった(値は変更しない)
#			!= 0 見つかった（引数の値を書き換える）
#
#	※※ python おそるべし．引数の書き換えは実質使えない．この関数は没．
#
def set_option_value( keyword, keyword_neg, argv, var ):
	if( keyword in argv ):
		t = var
		var = 0 if( keyword_neg in argv ) else 1
		dPRINT( " opt[" + keyword + "] before[", t, "] after[", var,  "]" )
		return 1
	else:
		return 0
####################
#
# 通常はphotore.pyにimportされて呼び出されるが，
# 書いてる途中では面倒だからこのスクリプト単体でも起動できるようにしとく．
#
if( __name__ == "__main__" ):
	main()
### enf of file ####
