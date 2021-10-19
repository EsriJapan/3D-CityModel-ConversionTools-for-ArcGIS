# coding : utf-8
"""
Name        :Create_FME_PARAMETER_FILE.py
Purpose     :3D都市モデルのCityGMLからの変換時、FME.exe だけで実行するパラメータファイルを作成する補助ツール
1) FME.exe のコマンド等の詳細は「Batch Processing Method 1: Command Line or Batch File」を参照
https://community.safe.com/s/article/batch-processing-method-2-command-file-1

2) パラメータファイルを実行する場合のコマンド
>cd "C:\Program Files\ArcGIS\Data Interoperability for ArcGIS Pro"
>fme PARAMETER_FILE <parameterFile>
※1 Data Interoperability はFME.exe へのパスを環境変数に設定していないので実行前にCDが必要
※2 parameterFile は1つだけしか指定できないので、使うパラメータ情報をファイル内にすべて含める

3) パラメータファイルの中身
※1 ファイルの拡張子は何でもよいが、コマンドプロンプトからの呼び出しのため、ファイルはShift-JISにしておく
※2 複数ファイルをデータソースとして渡す場合は、Help に書いてあるダブルクオートの前にバックスラッシュを入れる\
c:\temp\command.fmw --SourceDataset_ACAD "\"\"C:\FMEData\Data\Water\distribution_L25.dwg\" \"C:\FMEData\Data\Water\distribution_L26.dwg\"\"" --DestDataset_DGNV8 c:\temp\output.dgn

10/19の更新： 
・v118用にiur1.4のxsdスキーマファイルを指定できるように更新

Author      :
Copyright   :
Created     :2021/06/08
LastUpdated :2021/10/19
ArcGIS Version: ArcGIS Pro 2.6 以上
"""

import os,sys
import glob
import arcpy
import winreg

PARAM1_SOURCE_DATASET=r"--SourceDataset_CITYGML"
PARAM2_TEMPLATE_XML=r"--TEMPLATEFILE_GEODATABASE_FILE"
PARAM3_DEST_DATASET=r"--DestDataset_GEODATABASE_FILE"
PARAM4_ADE_XSD=r"--ADE_XSD_DOC_CITYGML"

#FME_EXE_PATH=r"C:\Program Files\ArcGIS\Data Interoperability for ArcGIS Pro\fme.exe"
PARAM_PARAMETER_FILE=r"PARAMETER_FILE"

def getArcGISPro_InstallDir():
    '''
    レジストリからArcGIS Pro の InstallDir を取得
    '''
    pro_path = ""
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\ESRI\ArcGISPro", 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY ) as key:
        pro_path = winreg.QueryValueEx(key, "InstallDir")[0]
    return pro_path

def getDataInterop_InstallDir():
    '''
    レジストリからData Interoperability for ArcGIS Pro の InstallDir を取得
    '''
    interop_path = ""
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\ESRI\Data Interoperability for ArcGIS Pro", 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY ) as key:
        interop_path = winreg.QueryValueEx(key, "InstallDir")[0]
    return interop_path

def createMultipleDatasetPath(files):
    '''
    Helpの説明にあるように
    ダブルクオートとバックスラッシュと入れた複数ファイルを指定するパラメータを作成
    '''
    sfiles = ""
    cnt = 0
    for f in files:
        cnt += 1
        if cnt == 1:
            sfiles += "\\\"{}\\\"".format(f)
        else:
            sfiles += " \\\"{}\\\"".format(f)
    sfiles = "\\\"{}\\\"".format(sfiles)
    return sfiles

def createParameterFile(fmw_model, citygml_folders, schema_xml, output_gdb, param_file, xsd_file):
    '''
    >fme.exe PARAMETER_FILE <parameterFile>
    での実行用にparameterFile　を作成する
    '''
    blResult = True
    try:
        param0 = "\"{0}\"".format(fmw_model)
        param2 = "{0} \"{1}\"".format(PARAM2_TEMPLATE_XML, schema_xml)
        param3 = "{0} \"{1}\"".format(PARAM3_DEST_DATASET, output_gdb)
        param4 = "{0} \"{1}\"".format(PARAM4_ADE_XSD, xsd_file)
        #単独フォルダ：
        #files = glob.glob(citygml_folder + os.path.sep + "*.gml")
        #files_param = createMultipleDatasetPath(files)
        #複数フォルダ：
        folders = citygml_folders.split(";")
        fileslist = []
        for folder in folders:
            files = glob.glob(folder + os.path.sep + "*.gml")
            fileslist.extend(files)
        files_param = createMultipleDatasetPath(fileslist)
        param1 = "{0} \"{1}\"".format(PARAM1_SOURCE_DATASET, files_param)
        
        params = "{0} {1} {2} {3}".format(param0, param1, param2, param3)
        #v118用にiur1.4のxsdスキーマファイルを指定
        if xsd_file is not None:
            params = "{0} {1} {2} {3} {4}".format(param0, param1, param2, param3, param4)
            
        with open(param_file, 'w', encoding='shift_jis') as f:
            f.write(params)
    except Exception as e:
        arcpy.AddError(e.args[0])
        blResult = False
    return blResult
        


def main():
    try:
        arcpy.AddMessage(u"PARAMETER_FILEの作成開始：")
        
        #FMW のモデル
        fmw_model = arcpy.GetParameterAsText(0) #"bldg_import_tokyo23_55cities_v110.fmw"
        
        #テンプレートGDBスキーマファイル
        schema_xml =  arcpy.GetParameterAsText(1) #"bldg_tokyo23_55cities_v112.xml"
        
        #変換するCityGMLが入っているフォルダ
        #水害や23区の対応のために複数フォルダを指定できるようにする
        citygml_folders = arcpy.GetParameterAsText(2) #"11100_saitama-shi_citygml_2\11100_saitama-shi_citygml\udx\bldg" 
        
        #出力する3D都市モデルのFGDB
        output_gdb = arcpy.GetParameterAsText(3) #"11100_saitama-shi_batch_bldg.gdb" 
        
        #出力するパラメータファイル
        param_file = arcpy.GetParameterAsText(4) #"ConvBuilding.par"
        
        #v118用にiur1.4のxsdスキーマファイルを指定
        xsd_file = None
        if arcpy.GetArgumentCount() == 6:
            xsd_file = arcpy.GetParameterAsText(5)
        
        #チェック
        
        #パラメータファイルの中身を作成

        
        #パラメータファイルをSJISファイルとして保存
        blResult = createParameterFile(fmw_model, citygml_folders, schema_xml, output_gdb, param_file, xsd_file)      

        if blResult:
            arcpy.AddMessage(u"PARAMETER_FILEの作成終了")
            # パラメータファイルを指定したコマンドを作成
            FME_EXE_PATH = os.path.join(getDataInterop_InstallDir(), "fme.exe")
            cmd = "\"{0}\" {1} \"{2}\"".format(FME_EXE_PATH, PARAM_PARAMETER_FILE, param_file)
            arcpy.AddMessage(u"次の実行コマンドで実行してください: {0}".format(cmd))

        arcpy.AddMessage(u"処理終了：")
    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
    except Exception as e:
        arcpy.AddError(e.args[0])

if __name__ == '__main__':
    main()