#!/usr/bin/python
# -*- coding: utf-8 -*-

#	2021/07/03(土) photoren.py
#	perlがandroid環境では絶望的なのに対し，pythonは少なくともストレージ種類に関係なく動作できることがわかったんで乗り換えることにする．
#	作りはさしあたりperl時代のものをそのまま移植することを優先する．
#	android環境でデスクトップにショートカットとして貼り付けておくファイル．
#	実際の処理を行うスクリプトはちょくちょくアップデートするんで，いちいちショートカットの貼り直しが面倒になって
#	間接的に起動することにした．

##
## 定番
##
"""
	use strict;
	use File::Basename;
	use File::Path;
	use Cwd 'realpath';
"""
import os
import sys
#import codecs
#sys.stdout = codecs.getwriter('utf_8')(sys.stdout)

##
## 処理実体を呼び出す．というより，ここにインクルード．
## ここはちょくちょく更新するんで仮名 pr で参照する．

import photoren7ca as pr	#実体ファイル名

#roid = ''					## use only android.
pr.main()					## 実体を実行

