# coding : utf-8
"""
Name        :calculate_genericAttributeSet_field_v110.py
Purpose     :ワークベンチを使って、3D都市モデルの汎用属性(gen:stringAttribute)と
             汎用属性セット(gen:genericAttributeSet) を、xml_genericAttributeSet フィールドに入れてある。
             そのXMLを展開して、フィールドを作成し、値をフィールドに格納するまでの処理を後処理で行うツール
Author      :
Copyright   :
Created     :2021/03/24
ArcGIS Version: ArcGIS Pro 2.6 以上
"""

import os
import arcpy
import xml.etree.ElementTree as et
import pandas as pd

XMLFIELDNAME = "xml_genericAttributeSet"

#適用するフィーチャークラス名 の一覧を定義
#FGDB内での対象フィーチャクラスを追加する場合、ここにフィーチャクラス名を追加すると処理対象になります。
FCNAMES = ["lod0_Building", "lod1_Building", "lod2_Building", "lod0_LandUse", "lod0_GenericCityObject", "lod0_WaterBody", "lod1_WaterBody"]

def fieldChecker(names):
    '''
    同じname がある場合に2つ目以降は "name_x" のフィールドにして重複しない形式で返却（x=2から付番されます） 
    '''
    new_names = []
    count_dict={}
    for name in names:
        count_dict[name] = count_dict.get(name,0) + 1
        if count_dict[name] == 1:
            new_names.append(name)
        else:
            new_name = name + "_{0}".format(count_dict.get(name,0))
            new_names.append(new_name)
    return new_names

def createRowFromXmlfield(field_value):
    '''
    xml_genericAttributeSet に格納されたXMLから'name:type' をキーにしたディクショナリを作成
    '''
    root = et.fromstring(field_value)
    names = [c.attrib['name'] for c in root]
    new_names = fieldChecker(names)
    row_dict = {}
    i = 0
    for c in root:
        key = new_names[i] + ":{0}".format(c.attrib["type"]) # key を name:type の形式にする
        row_dict[key] = c.text
        i += 1
    return row_dict

def convertXmlfieldToFields(fc):
    '''
    指定フィーチャクラス の xml_genericAttributeSet をフラットに展開する処理
    '''
    blResult = True
    try:
        arcpy.AddMessage(u"{0} の xml_genericAttributeSet　展開処理を開始します".format(fc))
        
        # 全レコードの xml_genericAttributeSet　を展開したものをDataFrame に格納
        rows = []
        xmlvalues = [row[0] for row in arcpy.da.SearchCursor(fc, XMLFIELDNAME)]
        for xmlvalue in xmlvalues:
            row = createRowFromXmlfield(xmlvalue)
            rows.append(row)
        df = pd.DataFrame(data=rows)
        
        # フィールドの追加
        lstFields = arcpy.ListFields(fc)
        field_names = [f.name for f in lstFields]
        for column in  df.columns:
            fieldName, fieldType = column.split(":")
            #fieldType も DATE型 などの場合はstring で扱いたいので分岐を追加する必要があります。
            if fieldName not in field_names:
                arcpy.AddMessage(u"{0}: フィールド を追加します".format(fieldName))
                arcpy.AddField_management(fc, fieldName, fieldType)
            else:
                arcpy.AddWarning(u"{0}: フィールド はすでに存在しているので、フィールド追加の処理はスキップします".format(fieldName))
        
        # UpdateCursor を使って、フィールドを更新
        update_fields = [c.split(":")[0] for c in df.columns]
        if len(update_fields) > 0:
            arcpy.AddMessage(u"{0}: のフィールドに値を展開します".format(update_fields))
            i = 0
            with arcpy.da.UpdateCursor(fc, update_fields) as cur:
                for r in cur:
                    r = df.values[i] # 1行を取得
                    cur.updateRow(r) # update_fieldsに指定したものが DataFrame のカラムの並び順なのでそのまま渡す
                    i += 1
        else:
            arcpy.AddWarning(u"対象フィールド が存在しないため、xml_genericAttributeSet　展開処理はスキップしました")
        
        # 後始末
        del xmlvalues
        del rows
        del df

        arcpy.AddMessage(u"xml_genericAttributeSet　展開処理を終了しました")
    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
        blResult = False
    except Exception as e:
        arcpy.AddError(e.args[0])
        blResult = False
    
    return blResult


def main():
    try:
        arcpy.AddMessage(u"処理開始：")

        input_gdb = arcpy.GetParameterAsText(0)

        arcpy.env.overwriteOutput = True
        
        arcpy.env.workspace = input_gdb
        for fc in FCNAMES:
            if arcpy.Exists(fc):
                if int(arcpy.GetCount_management(fc)[0]) > 0:
                    bl = convertXmlfieldToFields(fc)
                else:
                    arcpy.AddWarning(u"{0} の レコードがないため処理をスキップします".format(fc))

        arcpy.AddMessage(u"処理終了：")
    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
    except Exception as e:
        arcpy.AddError(e.args[0])

if __name__ == '__main__':
    main()
