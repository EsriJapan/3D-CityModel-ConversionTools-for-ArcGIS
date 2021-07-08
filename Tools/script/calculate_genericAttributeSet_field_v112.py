# coding : utf-8
"""
Name        :calculate_genericAttributeSet_field_v112.py
Purpose     :ワークベンチを使って、3D都市モデルの汎用属性(gen:stringAttribute)と
             汎用属性セット(gen:genericAttributeSet) を、xml_genericAttributeSet フィールドに入れてある。
             そのXMLを展開して、フィールドを作成し、値をフィールドに格納するまでの処理を後処理で行うツール
             
            v110 → v111 の更新内容
             ・メモリ対策を見直し
             ・進捗表示のメッセージを追加
             ・xml_genericAttributeSetの展開時、仕様上入ってこないはずのgen_FIDを除外する処理を追加
            v111 → v112 の更新内容
             ・展開するxml_genericAttributeSet に、gen_1/2500図郭 などがある場合の対応を追加
             ・例外発生時のtraceback を追加
             ・xml_genericAttributeSet の展開前に、AddField_management で追加したフィールド名の変更されていないか確認処理を追加
Author      :
Copyright   :
Created     :2021/03/24
Last Updated:2021/06/30
ArcGIS Version: ArcGIS Pro 2.6 以上
"""

import os
import arcpy
import xml.etree.ElementTree as et
import pandas as pd
import traceback #v112

XMLFIELDNAME = "xml_genericAttributeSet"

#適用するフィーチャークラス名 の一覧を定義
#FGDB内での対象フィーチャクラスを追加する場合、ここにフィーチャクラス名を追加すると処理対象になります。
FCNAMES = ["lod0_Building", "lod1_Building", "lod2_Building", "lod0_LandUse", "lod0_GenericCityObject", "lod1_WaterBody"] #"lod0_WaterBody", 

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

def sanitize_field_name(field_name):
    '''
    v112: gen_1/2500図郭 などの場合があるみたいなので、念のため汎用的に対応できるようにチェック関数を追加
    '''
    field_name = field_name.strip()
    new_field_name = field_name.replace("/", "_").replace(":", "_").replace(".", "_").replace("-", "_")
    return new_field_name

def createRowFromXmlfield(field_value):
    '''
    xml_genericAttributeSet に格納されたXMLから'name:type' をキーにしたディクショナリを作成
    v111:メモリ対策の見直し
        :仕様上入ってこないはず展開を除外するフィールド["gen_FID:TEXT"]
    '''
    root = et.fromstring(field_value)
    names = [c.attrib['name'] for c in root]
    new_names = fieldChecker(names)
    row_dict = {}
    i = 0
    for c in root:
        #key = new_names[i] + ":{0}".format(c.attrib["type"]) # key を name:type の形式にする
        key = sanitize_field_name(new_names[i]) + ":{0}".format(c.attrib["type"]) # v112:gen_1/2500図郭などへの対応
        if new_names[i] != "gen_FID" :
            row_dict[key] = c.text
        i += 1
        c.clear()
    root.clear()
    del names, new_names
    return row_dict

def check_added_field_names(new_field_names, update_field_names):
    '''
    v112: DataFrameのcolumns と、arcpy.AddField　で追加されたフィールド名が全て一致しているかをチェック
    （arcpy.AddField_management ではWarningでフィールド名をリネームして処理が継続されるため）
    '''
    blResult = True
    for update_field_name in update_field_names:
        if update_field_name not in new_field_names:
            blResult = False
            break
    return blResult

def convertXmlfieldToFields(fc):
    '''
    指定フィーチャクラス の xml_genericAttributeSet をフラットに展開する処理
    v111:メモリ対策の見直し、進捗表示のメッセージを追加
    '''
    blResult = True
    try:
        arcpy.AddMessage(u"{0} の xml_genericAttributeSet  展開処理を開始します".format(fc))
        
        # v111: 進捗表示のメッセージ用に追加
        cnt = 0
        num = int(arcpy.GetCount_management(fc).getOutput(0))
        
        # v111: 全レコードの xml_genericAttributeSet　を展開したものをDataFrame に格納(メモリ対策を見直し)
        rows = []
        with arcpy.da.SearchCursor(fc, XMLFIELDNAME) as scur:
            for r in scur:
                cnt += 1
                if (cnt == 1) or (cnt == num) or (cnt % 10000 == 1):
                    s = u"{0}/{1}の xml_genericAttributeSet  読込処理中・・・".format(cnt, num)
                    arcpy.AddMessage(s)                
                xmlvalue = r[0]
                row = createRowFromXmlfield(xmlvalue)
                rows.append(row)
        df = pd.DataFrame(data=rows)
        # 後始末
        del rows
        
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
        #v112:（AddField_management　ではWarningでフィールド名をリネームして処理が継続されるため）フィールド名が変更されたものがないかの確認
        new_lstFields = arcpy.ListFields(fc)
        new_field_names = [f.name for f in new_lstFields]
        blFieldsCheck = check_added_field_names(new_field_names, update_fields)
        if blFieldsCheck:
            if len(update_fields) > 0:
                arcpy.AddMessage(u"{0}: のフィールドに値を展開します".format(update_fields))
                i = 0
                cnt = 0
                with arcpy.da.UpdateCursor(fc, update_fields) as cur:
                    for r in cur:
                        cnt += 1
                        if (cnt == 1) or (cnt == num) or (cnt % 10000 == 1):
                            s = u"{0}/{1}の xml_genericAttributeSet  展開処理中・・・".format(cnt, num)
                            arcpy.AddMessage(s)
                        r = df.values[i] # 1行を取得
                        cur.updateRow(r) # update_fieldsに指定したものが DataFrame のカラムの並び順なのでそのまま渡す
                        i += 1
            else:
                arcpy.AddWarning(u"対象フィールド が存在しないため、xml_genericAttributeSet  展開処理はスキップしました")        
        else:
            arcpy.AddWarning(u"AddField_management の処理でフィールド名が変更されたものがあるため、xml_genericAttributeSet の展開処理はスキップしました")

        
        # 後始末
        del df

        arcpy.AddMessage(u"xml_genericAttributeSet  展開処理を終了しました")
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

        input_gdb = arcpy.GetParameterAsText(0)
        
        # v111: 入力値のチェックを追加
        if os.path.splitext(input_gdb)[1].upper() != ".GDB":
            arcpy.AddError(u"{0} は3D都市モデルの変換先ファイル ジオデータベースを選択する必要があります".format(input_gdb))
            return 
 
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
        err = e.args[0]
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(err)
        arcpy.AddError(pymsg)


if __name__ == '__main__':
    main()
