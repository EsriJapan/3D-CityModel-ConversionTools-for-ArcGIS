# coding:utf-8
"""
Name        :assign_landuseAttributes_v111.py
Purpose     :3D都市モデルで土地利用（luse）は、自治体拡張が可能な形式で定義されてているため、
             汎用属性セット(gen:genericAttributeSet) を、xml_genericAttributeSet フィールドに入れる処理をワークベンチで行い、、
             そのXMLを展開して、フィールドを作成し、値をフィールドに格納するまでの処理を後処理で行うためのツール。
             
             元のXMLファイルでは gen:genericAttributeSet name = "土地利用区分（都道府県分）" or name = "土地利用区分（市区町村分）" だが、
             そのままではフィールド名にはできないので、"土地利用区分_都道府県分" "土地利用区分_市区町村分" としてワークベンチ内で変換を行ってある。
             
             また、XMLを展開してフィールドに値を展開後、[codelists] - [LandUse_genUsage.xml] の中身を見て、コード値ドメインの定義とフィールドへの適用をこのツールで行う
             
            v110 → v111 の更新内容
             ・メモリ対策を見直し
             ・進捗表示のメッセージを追加
Author      :
Copyright   :
Created     :2021/03/25
Last Updated:2021/06/09
ArcGIS Version: ArcGIS Pro 2.6 以上
"""
import arcpy
import os
import xml.etree.ElementTree as et
import pandas as pd

# 使いまわし可能な関数がそれぞれをimport 
import calculate_genericAttributeSet_field_v111 as calgen
import assign_extendedAttributes_v111 as exattr

#ワークベンチで処理した結果を格納してあるフィールド名
XMLFIELDNAME = "xml_genericAttributeSet"

#土地利用のコードと説明を定義しているファイル名
LANDUSE_USAGE_FILE = "LandUse_genUsage.xml"

#コード値ドメインを適用するフィーチャクラス名
FCNAMES = ["lod1_LandUse"]


def convertXmlfieldToFields(fc):
    '''
    指定フィーチャクラス の xml_genericAttributeSet をフラットに展開する処理
    (calculate_genericAttributeSet_field_v10x.py からコピーしてきてdataframe も返却するようにした）
    v111:進捗表示のメッセージを追加
    '''
    blResult = True
    try:
        arcpy.AddMessage(u"{0} の xml_genericAttributeSet　展開処理を開始します".format(fc))
        
        # v111: 進捗表示のメッセージ用に追加
        cnt = 0
        num = int(arcpy.GetCount_management(fc).getOutput(0))
        
        # v111: 全レコードの xml_genericAttributeSet　を展開したものをDataFrame に格納(メモリ対策を見直し)
        rows = []
        with arcpy.da.SearchCursor(fc, XMLFIELDNAME) as scur:
            for r in scur:
                cnt += 1
                if (cnt == 1) or (cnt == num) or (cnt % 10000 == 1):
                    s = u"{0}/{1}の xml_genericAttributeSet　読込処理中・・・".format(cnt, num)
                    arcpy.AddMessage(s)                
                xmlvalue = r[0]
                row = calgen.createRowFromXmlfield(xmlvalue)
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
        if len(update_fields) > 0:           
            arcpy.AddMessage(u"{0}: のフィールドに値を展開します".format(update_fields))
            i = 0
            cnt = 0
            with arcpy.da.UpdateCursor(fc, update_fields) as cur:
                for r in cur:
                    cnt += 1
                    if (cnt == 1) or (cnt == num) or (cnt % 10000 == 1):
                        s = u"{0}/{1}の xml_genericAttributeSet　展開処理中・・・".format(cnt, num)
                        arcpy.AddMessage(s)
                    r = df.values[i] # 1行を取得
                    cur.updateRow(r) # update_fieldsに指定したものが DataFrame のカラムの並び順なのでそのまま渡す
                    i += 1
        else:
            arcpy.AddWarning(u"対象フィールド が存在しないため、xml_genericAttributeSet　展開処理はスキップしました")
        
        # 後始末-不要になったので削除

        arcpy.AddMessage(u"xml_genericAttributeSet　展開処理を終了しました")
    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
        blResult = False
    except Exception as e:
        arcpy.AddError(e.args[0])
        blResult = False
    
    return blResult, df


def main():
    try:
        arcpy.AddMessage(u"処理開始：")
        
        landUse_genUsage_xml = arcpy.GetParameterAsText(0)
        gdb = arcpy.GetParameterAsText(1)
        folder = os.path.dirname(landUse_genUsage_xml)
        filename = os.path.basename(landUse_genUsage_xml)

        # 入力値のチェック
        if filename != LANDUSE_USAGE_FILE:
            arcpy.AddError(u"{0} というファイルを選択する必要があります(大文字小文字を含め同一である必要があります)".format(LANDUSE_USAGE_FILE)) #v111:メッセージ変更
            return
        if os.path.splitext(gdb)[1].upper() != ".GDB":
            arcpy.AddError(u"{0} は3D都市モデルの変換先ファイル ジオデータベースを選択する必要があります".format(gdb))
            return

        arcpy.env.workspace = gdb

        # 1) LandUse_genUsage.xml をもとに、コード値ドメインと説明を作成する
        domainName, domainDict = exattr.createDomainValues(landUse_genUsage_xml) #createDomainValues(landUse_genUsage_xml)
        
        # 既存のドメイン
        domains = arcpy.Describe(gdb).domains
        
        # ドメインの説明は固定
        domainDesc = r"土地利用区分" 
        # ドメインの作成（既存ドメインが存在する場合は処理しない）
        if domainName not in domains:
            #print("Creating domain " + domainName)
            arcpy.AddMessage(u"{0}: ドメイン を作成します".format(domainName))
            arcpy.CreateDomain_management(gdb, domainName, domainDesc, "TEXT", "CODED")
            # 作成したドメインにコードと説明を追加
            for code in domainDict:
                codeDesc = domainDict[code]
                arcpy.AddMessage(u"{0}: ドメイン に{1} , {2} のコードを追加します".format(domainName,code, codeDesc))
                arcpy.AddCodedValueToDomain_management(gdb, domainName, code, codeDesc)
                #print("Add code " code)
        else:
            arcpy.AddWarning(u"{0}: ドメイン はすでに存在しているので、ドメイン 作成の処理はスキップします".format(domainName))

        # 2) フィールドの展開
        for fc in FCNAMES:
            if arcpy.Exists(fc):
                # 1) xml_genericAttributeSet をフィールドに展開する
                if int(arcpy.GetCount_management(fc)[0]) > 0:
                    bl, df = convertXmlfieldToFields(fc)
                    
                    # 3) ドメインを lod0_LandUse フィーチャクラスのフィールドに適用（上記で追加したフィールド）
                    fieldNames = [f.name for f in arcpy.ListFields(fc)]
                    for column in df.columns:
                        fieldName, fieldType = column.split(":")
                        if fieldName in fieldNames:
                            arcpy.AddMessage(u"{0} の{1} フィールドに{2} ドメインを適用します".format(fc, fieldName, domainName))
                            arcpy.AssignDomainToField_management(fc, fieldName, domainName)
                        else:
                            arcpy.AddWarning(u"{0} に{1} フィールドが定義されていないため、ドメインの適用をスキップします".format(fc, fieldName))
                    
                    #　後始末
                    del df
                else:
                    arcpy.AddWarning(u"{0} の レコードがないため処理をスキップします".format(fc))

        arcpy.AddMessage(u"処理終了：")
    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
    except Exception as e:
        arcpy.AddError(e.args[0])

if __name__ == '__main__':
    main()

