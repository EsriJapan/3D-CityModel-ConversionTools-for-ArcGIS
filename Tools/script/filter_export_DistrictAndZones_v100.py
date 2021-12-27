# coding:utf-8
"""
Name        :filter_export_DistrictAndZones_v100.py
Purpose     :CityGML の設計上、lod0_DistrictAndZones (lod0_地域地区) として一つのフィーチャクラスにデータを格納しているが、
             そのままではデータとしてポリゴンの重複がかなりあり、データとしては使いづらいので、urf_class の値をもとに別フィーチャクラスに出力するツール
             
             設定ファイルは2021年12月27日時点では地域地区と、区域区分のものを用意して、[config] フォルダー下に配置（utf-8, 区切り文字は;）
             
             例）config_地域地区_分類出力.txt
               フィーチャクラス;エイリアス;クエリ
               lod0_DistrictAndZones_yoto;用途地域;urf_class in ('0','1','2','3','4','5','6','7','8','9','10','11','12','13')
               lod0_DistrictAndZones_tokuyoto;特別用途地区;urf_class in ('14')
               ～省略～
               
Author      :
Copyright   :
Created     :2021/12/27
Last Updated:2021/12/27
ArcGIS Version: ArcGIS Pro 2.6 以上
"""
import arcpy
import os
import traceback

#フィルタ条件を設定する対象のフィールド
CONFIG_PATH = "config"
CONFIG_FILENAME = r"config_地域地区_分類出力.txt"

#入力ファイル名
INPUT_FILENAME = "lod0_DistrictAndZones"

def getConfigFile():
    '''
    設定ファイルの保存先のパスを取得
    '''
    folder = os.path.dirname(__file__) #このスクリプトのディレクトリ
    config_folder = os.path.join(folder, CONFIG_PATH) # config フォルダのディレクトリ
    return os.path.join(config_folder, CONFIG_FILENAME)

def filterExport(input_fc, out_ws, config_file):
    '''
    '''
    blResult = True
    try:
        infc_name = os.path.basename(input_fc)
        arcpy.env.workspace = os.path.dirname(input_fc)
        
        # 設定ファイルの存在チェック
        if not os.path.exists(config_file):
            arcpy.AddError(u"設定ファイル: {0} が存在しません".format(config_file))
            return
        
        # 設定ファイルから出力フィーチャクラス、エイリアス、フィルタ条件を読み込み
        exportParams = []
        with open(config_file, encoding='utf-8') as f:
            next(f) # ヘッダーは読み飛ばす
            for line in f:
                line = line.rstrip("\n")
                params = line.split(";")
                exportParams.append(params)
        
        # 設定ファイルから出力フィーチャクラス、エイリアス、フィルタ条件を読み込みし、
        # クエリ後 > 0 の場合にFeatureClassToFeatureClass でエクスポート
        for p in exportParams:
            outfc_name = p[0] #出力フィーチャクラス
            alias_name = p[1] #エイリアス
            expression = p[2] #フィルタ条件
            lyr = arcpy.SelectLayerByAttribute_management(input_fc, "NEW_SELECTION", expression)
            cnt = int(arcpy.GetCount_management(lyr).getOutput(0))
            if cnt > 0:
                arcpy.AddMessage(u"{0} ({1}) へエクスポート".format(outfc_name, alias_name))
                out_fc = os.path.join(out_ws, outfc_name)
                if arcpy.Exists(out_fc): #既存のフィーチャクラスがある場合は削除
                    arcpy.Delete_management(out_fc)
                arcpy.FeatureClassToFeatureClass_conversion(input_fc, out_ws, outfc_name, expression)
                arcpy.AlterAliasName(out_fc, alias_name)
            else:
                arcpy.AddWarning(u"{0} ({1}) は該当データがないためエクスポートをスキップしました".format(outfc_name, alias_name))
        
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
        
        input_fc = arcpy.GetParameterAsText(0) # lod0_DistrictAndZones フィーチャクラスを指定
        
        out_ws = arcpy.GetParameterAsText(1) # 出力するワークスペースを指定
        
        # 入力ファイルのチェック
        if os.path.basename(input_fc) != INPUT_FILENAME:
            arcpy.AddError(u"{0} というファイルを選択する必要があります(大文字小文字を含め同一である必要があります)".format(INPUT_FILENAME))
            return
        
        config_file = getConfigFile() # Export 条件を設定したファイルを指定
        
        filterExport(input_fc, out_ws, config_file)

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

