# coding:utf-8
"""
Name        :field_calculate_buildingName_v100.py
Purpose     :3D都市モデルの建物（Building）で、gml:name 属性の型は、gml:CodeType [0..1]となっています。
             本来はCodeTypeを定義したファイル（Building_name.xml）にその建物名称が定義されているのが仕様に忠実なのですが、
             2020年度に整備させたほとんどの自治体のケースは、gml:name 属性にそのまま文字列で〇〇市役所が入っているケースが多いです。
             しかし、福岡県宗像市の建物では、仕様に忠実にCityGMLを作ってあったため、gml_name の属性は、フィーチャクラスではコードの値のままになっています。
             
             そのようなケースに対応するため、拡張属性のコード値ドメインの割り当てツール で書いたXML からディクショナリに読み込む実装を使って、
             gml_name の属性に格納されているコードの値を、Building_name.xml 内のgml:description の説明で置換するツールを作成しました。
             
Author      :
Copyright   :
Created     :2022/11/19
Last Updated:
ArcGIS Version: ArcGIS Pro 2.6 以上
"""
import arcpy
import os
import xml.etree.ElementTree as et
import pandas as pd
import traceback #v112

# 使いまわし可能な関数をimport 
import assign_extendedAttributes_v113 as exattr

# 文字列置換の対象フィールド名
FIELDNAME = "gml_name"

# 建物のgml:name のCodeTypeを定義しているファイル名
BUILDING_NAME_FILE = "Building_name.xml"

# gml_name の属性を置換するフィーチャクラス名。とりあえず Building, BuildingPart のみにする
FCNAMES = ["lod0_Building", "lod1_Building", "lod2_Building", "lod1_BuildingPart", "lod2_BuildingPart"]

def main():
    try:
        arcpy.AddMessage(u"処理開始：")
        
        building_name_xml = arcpy.GetParameterAsText(0)
        gdb = arcpy.GetParameterAsText(1)
        folder = os.path.dirname(building_name_xml)
        filename = os.path.basename(building_name_xml)

        # 入力値のチェック
        if filename != BUILDING_NAME_FILE:
            arcpy.AddError(u"{0} というファイルを選択する必要があります(大文字小文字を含め同一である必要があります)".format(BUILDING_NAME_FILE))
            return
        if os.path.splitext(gdb)[1].upper() != ".GDB":
            arcpy.AddError(u"{0} は3D都市モデルの変換先ファイル ジオデータベースを選択する必要があります".format(gdb))
            return

        arcpy.env.workspace = gdb

        # 1) Building_name.xml をもとに、コード値と説明を取得する
        domainName, domainDict = exattr.createDomainValues(building_name_xml)

        # 2) gml_name フィールドのコード値から説明へ置換
        for fc in FCNAMES:
            if arcpy.Exists(fc):
                num = int(arcpy.GetCount_management(fc).getOutput(0))
                if num > 0:
                    arcpy.AddMessage(u"{0} の gml_name  コード値 を説明 へ置換する処理を開始します".format(fc))
                    # 文字列置換の対象フィールド名
                    update_fields = [FIELDNAME]
                    cnt = 0
                    i = 0
                    with arcpy.da.UpdateCursor(fc, update_fields) as cur:
                        for r in cur:
                            cnt += 1
                            if (cnt == 1) or (cnt == num) or (cnt % 10000 == 1):
                                s = u"{0}/{1}の gml_name のコード値 を説明 へ置換中・・・".format(cnt, num)
                                arcpy.AddMessage(s)
                            key = r[0]
                            if not key == None:
                                desc = domainDict.get(key) # ディクショナリからdescription を取得(例外が発生しないようにgetで取得)
                                if not desc == None:
                                    arcpy.AddMessage(u"{0} を {1} へ置換します".format(key, desc))
                                    r[0] = desc
                                    i += 1
                            cur.updateRow(r)
                    arcpy.AddMessage(u"{0} の gml_name  コード値 {1} 件を説明 へ置換しました".format(fc, i))
                else:
                    arcpy.AddWarning(u"{0} の レコードがないため処理をスキップします".format(fc))

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

