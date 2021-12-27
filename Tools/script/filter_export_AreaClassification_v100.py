# coding:utf-8
"""
Name        :filter_export_AreaClassification_v100.py
Purpose     :CityGML の設計上、lod0_AreaClassification (lod0_区域区分) として一つのフィーチャクラスにデータを格納しているが、
             そのままではデータとしてポリゴンの重複がかなりあり、データとしては使いづらいので、urf_class の値をもとに別フィーチャクラスに出力するツール
             
             設定ファイルは2021年12月27日時点では地域地区と、区域区分のものを用意して、[config] フォルダー下に配置（utf-8, 区切り文字は;）
             
             例）config_区域区分_分類出力.txt
               フィーチャクラス;エイリアス;クエリ
               lod0_AreaClassification_cigaika;市街化区域・市街化調整区域・非線引き区域;urf_class in ('22','23','24','25')
               lod0_AreaClassification_kyojuyudo;居住誘導区域;urf_class in ('31')
               lod0_AreaClassification_tosiyudo;都市機能誘導区域;urf_class in ('32')
               
Author      :
Copyright   :
Created     :2021/12/27
Last Updated:2021/12/27
ArcGIS Version: ArcGIS Pro 2.6 以上
"""
import arcpy
import os
import traceback

# 使いまわし可能な関数をimport 
import filter_export_DistrictAndZones_v100 as flexp

#フィルタ条件を設定する対象のフィールド
CONFIG_PATH = "config"
CONFIG_FILENAME = r"config_区域区分_分類出力.txt"

#入力ファイル名
INPUT_FILENAME = "lod0_AreaClassification"

def getConfigFile():
    '''
    設定ファイルの保存先のパスを取得
    '''
    folder = os.path.dirname(__file__) #このスクリプトのディレクトリ
    config_folder = os.path.join(folder, CONFIG_PATH) # config フォルダのディレクトリ
    return os.path.join(config_folder, CONFIG_FILENAME)

def main():
    try:
        arcpy.AddMessage(u"処理開始：")
        
        input_fc = arcpy.GetParameterAsText(0) # lod0_AreaClassification フィーチャクラスを指定
        
        out_ws = arcpy.GetParameterAsText(1) # 出力するワークスペースを指定
        
        # 入力ファイルのチェック
        if os.path.basename(input_fc) != INPUT_FILENAME:
            arcpy.AddError(u"{0} というファイルを選択する必要があります(大文字小文字を含め同一である必要があります)".format(INPUT_FILENAME))
            return

        config_file = getConfigFile() # Export 条件を設定したファイルを指定
        
        flexp.filterExport(input_fc, out_ws, config_file)

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

