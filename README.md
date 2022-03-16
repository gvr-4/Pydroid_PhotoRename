# Pydroid_PhotoRename
Rename and move picture files into External SDcard by python script on pydroid.

Android端末のpydroidで動く，Pythonで書いたスクリプトです．
このスクリプトは，かつて私が愛用していた傑作アプリ，DSC AUTO RENAME が機能しなくなって以降，
仕方なく大昔に作っていた perl(SL4A，Windows兼用)スクリプトを改造拡張してpythonに書換えたものです．

設定ファイルに記した ファイル拡張子，検索ディレクトリ，改名ルールを基にして，
同じく設定ファイルに記した 移動先ディレクトリ，サブディレクトリに改名したファイルを移動します．

私のAndroid端末 SHARP AQUOS R2 Compact android 11にはmicroSDXCカードが挿入してあり，
カメラアプリで保存したオリジナルの画像ファイルを次の場所に，次のようなディレクトリとファイル名で移動させています．

/storage/0000-0000/doc/photo/yyyy/yyyymmdd/yyyymmdd-hhmmss.jpg
 
 目下の課題は，このPythonスクリプトを実行する方法が，
 　デスクトップアイコン Pydroidをクリックしてpydroidを起動して，
  ファイルメニューからスクリプト photoren.py を読み込んで，
  実行アイコンをクリックして，
  処理が終了するのを画面で確認して，
  pydroidを終了する．
 ……という，およそ信じられないほどの多大な手間と労力を毎回費やしていることです．
　なんとかして自動実行する方法がないか，模索しているところです．
 誰かの良いアイデアを求めています．読んでくれてありがとう．
