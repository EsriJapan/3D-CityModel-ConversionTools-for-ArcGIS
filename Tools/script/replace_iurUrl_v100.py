# coding:utf-8
"""
Name        :replace_iurUrl_v100.py
Purpose     :2021年9月18日にi-UR1.4の名前空間及びXMLSchema ファイルの所在が変更されたことに伴い
             2020年度に整備された3D都市モデルのデータを変換する場合、ローカルにアーカイブされたXMLSchemaファイル（*.xsd）が必要となった。
             
             各インポートツールの対応は、マニュアルの4.4 に説明してあるように、パラメータを公開することにより対応してあるが、
             ジオプロツールから呼び出す場合は、複数のXMLSchemaファイルを指定できないため、genericのスキーマを使っている建物等は警告が出る場合がある。
             
             また、水部、災害リスクなど、本来i-UR1.4の名前空間のスキーマを使用しないCityGML ファイルにも宣言がされているため、FMEはそのURLをチェックを行ってエラーとなる。
             その回避としては、CityGML2.0 のwaterBody.xsd やgenerics.xsd をローカルにダウンロードして、変換時に指定するようパラメータを公開した。
             
             本ツールは、上記のローカルでのxsd ファイルを指定しなくても変換可能なように、2020年度のCityGML　ファイルのi-UR1.4の所在を強制的にi-UR1.5のものに置換してしまうツールです。
             このツールでURLの文字をi-UR1.5のものに置換すると、各インポートツールでのXSDスキーマファイルの指定は不要になります。
Author      :
Copyright   :
Created     :2021/12/17
Last Updated:202x/xx/xx
ArcGIS Version: ArcGIS Pro 2.6 以上
"""
import arcpy
import os
import traceback

# 置換するURLの文字列を定義
IUR14_SCHEMAS_URL = "http://www.kantei.go.jp/jp/singi/tiiki/toshisaisei/itoshisaisei/iur/schemas/uro/1.4"
IUR14_URL = "http://www.kantei.go.jp/jp/singi/tiiki/toshisaisei/itoshisaisei/iur/uro/1.4"

IUR15_SCHEMAS_URL = "https://www.chisou.go.jp/tiiki/toshisaisei/itoshisaisei/iur/schemas/uro/1.5"
IUR15_URL = "https://www.chisou.go.jp/tiiki/toshisaisei/itoshisaisei/iur/uro/1.5"

def convertUrls(folder):
    '''
    指定フォルダ内の*.gml ファイルを開いて、URLを書きかえて別ファイルに保存する処理
    出力ファイル名は元ファイル名の接頭辞に"o_"をつけて、"o_元のファイル名.gml"　として決め打ち
    '''

    blResult = True
    try:
        
        arcpy.AddMessage(u"CityGML ファイルのURL 置換処理を開始します。")
        arcpy.env.workspace = folder
        input_files = arcpy.ListFiles("*.gml")

        # 進捗表示のメッセージ用
        cnt = 0
        num = len(input_files)
        
        if num == 0:
            arcpy.AddError(u"{0} には処理対象のCityGML ファイル（*.gml）がありません。".format(folder))
            return
        
        for input_file_name in input_files:
            # 出力ファイル名は接頭辞に"o_"をつける
            out_file_name = "o_{0}".format(input_file_name)
            
            # 入出力のファイルをフルパスに
            out_file = os.path.join(folder, out_file_name)
            input_file = os.path.join(folder, input_file_name)
            
            # すでにある場合は削除
            if arcpy.Exists(out_file):
                arcpy.management.Delete(out_file)
            
            cnt += 1
            if (cnt == 1) or (cnt == num) or (cnt % 10000 == 1):
                s = u"{0}/{1}の URL 置換処理中・・・ファイル:{2}".format(cnt, num, input_file_name)
                arcpy.AddMessage(s)             
            
            # URLの書き換え処理
            with open(input_file, "r", encoding='utf-8') as infile, open(out_file, "w", encoding='utf-8') as outfile:
                data = infile.read()
                data = data.replace(IUR14_SCHEMAS_URL, IUR15_SCHEMAS_URL)
                data = data.replace(IUR14_URL, IUR15_URL)    
                outfile.write(data)

        arcpy.AddMessage(u"CityGML ファイルのURL 置換処理を終了しました")
    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
        blResult = False
    except Exception as e:
        err = e.args[0]
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(err)
        arcpy.AddError(pymsg)        
        blResult = False
    
    return blResult


def main():
    try:
        arcpy.AddMessage(u"処理開始：")
        
        folder = arcpy.GetParameterAsText(0) # 解凍したcityを入れてあるフォルダ

        # フォルダ内に格納されているCityGML ファイルのURLを置換する処理
        convertUrls(folder)

        arcpy.AddMessage(u"処理終了：")
    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
    except Exception as e:
        err = e.args[0]
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(err)
        arcpy.AddError(pymsg)

if __name__ == '__main__':
    main()

