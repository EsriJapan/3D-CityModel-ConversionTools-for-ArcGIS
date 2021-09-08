# coding:utf-8
"""
Name        :assign_extendedAttributes_v112.py
Purpose     :3D都市モデルで拡張属性の定義が標準対応、および自治体拡張が可能な形式で定義されてているため、
            [codelists] - [extendedAttribute_key.xml] の中身を見て、各拡張属性のコード値ドメインの定義とフィールドへの適用を後処理で行うツール
            後処理といってもテンプレートGDB  ： Standard_XXX.gdb に適用した後に実行でも構わない
            
            v110 → v111 の更新内容
             ・メモリ対策を見直し
             ・extendedAttribute_keyX.xml ファイル内の <gml:name>ExtendedAttribute_keyX</gml:name> との整合チェックを追加
             ・空の<gml:dictionaryEntry>要素への対応
            v111 → v112 の更新内容
             ・コード値に対応する説明がない不正なデータはスキップするよう処理を追加
             ・例外発生時のtraceback を追加            
            v112  → v113 の更新内容
             ・フィールド名のエイリアスに、ドメインの説明を適用する処理を追加
Author      :
Copyright   :
Created     :2021/03/24
Last Updated:2021/09/08
ArcGIS Version: ArcGIS Pro 2.6 以上
"""
import arcpy
import os
import xml.etree.ElementTree as et
import traceback #v112

#拡張属性を定義しているファイル名
EXTATTR_KEYFILE = "extendedAttribute_key.xml"

#コード値ドメインを適用するフィーチャクラス名
FCNAMES = ["lod0_Building", "lod1_Building", "lod2_Building", "lod1_BuildingPart", "lod2_BuildingPart"]

def createFileName(orgFilename, keyVal):
    """
    extendedAttribute_key.xml のファイルと keyVal を使って、
    extendedAttribute_key2.xml ～ extendedAttribute_key10.xml
    extendedAttribute_key100.xml～ extendedAttribute_key120.xml のファイル名を作成する
    """
    fileName = os.path.basename(orgFilename)
    splitFilename = os.path.splitext(fileName)
    return "{0}{1}{2}".format(splitFilename[0], keyVal, splitFilename[1])

def createDomainNameFromFilename(orgFilename):
    """
    extendedAttribute_key2.xml のファイル名から ExtendedAttribute_key2 のドメイン名を作成
    """
    fileName = os.path.basename(orgFilename)
    splitFilename = os.path.splitext(fileName)
    return "{0}{1}".format("E", splitFilename[0][1::])

def createFieldNameFromFilename(orgFilename):
    """
    extendedAttribute_key2.xml のファイル名から uro_extendedAttribute_key2 のドメインを適用するフィールド名を作成
    """
    fileName = os.path.basename(orgFilename)
    splitFilename = os.path.splitext(fileName)
    return "{0}{1}".format("uro_", splitFilename[0])

def createExtendedAttributeFiles(xmlfile):
    """
    extendedAttribute_key.xml から開くxmlファイル名とドメインの説明を作成
    v111:メモリ対策の見直し, 空の<gml:dictionaryEntry>要素への対応
    """
    fileDict = dict()
    tree = et.parse(xmlfile)
    root = tree.getroot()
    ns = {'gml':"http://www.opengis.net/gml"}
    # gml:Definition/gml:name はファイル名に利用
    # gml:Definition/gml:description はドメインの説明に利用
    dicts = root.findall('gml:dictionaryEntry', ns)
    for dic in dicts:
        if (dic.find('gml:Definition/gml:description', ns) != None) and (dic.find('gml:Definition/gml:name', ns) != None):
            desc = dic.find('gml:Definition/gml:description', ns).text
            name = dic.find('gml:Definition/gml:name', ns).text
            fileName = createFileName(os.path.basename(xmlfile), name)
            fileDict[fileName] = desc
        dic.clear()
    dicts.clear()
    root.clear()
    return fileDict

def createDomainValues(xmlfile):
    """
    extendedAttribute_keyXX.xml からコード値ドメインの定義に必要な情報を作成
    v111:メモリ対策の見直し, 空の<gml:dictionaryEntry>要素への対応   
    """
    domainDict = dict()
    tree = et.parse(xmlfile)
    root = tree.getroot()       
    ns = {'gml':"http://www.opengis.net/gml"}
    # gml:name を ドメイン名として利用
    domainName = root.find('gml:name', ns).text
    # gml:Definition/gml:name と gml:Definition/gml:description をコード値ドメインの値として利用
    dicts = root.findall('gml:dictionaryEntry', ns)
    for dic in dicts:
        if (dic.find('gml:Definition/gml:description', ns) != None) and (dic.find('gml:Definition/gml:name', ns) != None):
            desc = dic.find('gml:Definition/gml:description', ns).text
            name = dic.find('gml:Definition/gml:name', ns).text
            domainDict[name] = desc
        dic.clear()
    dicts.clear()
    root.clear()    
    return domainName, domainDict

def main():
    try:
        arcpy.AddMessage(u"処理開始：")

        extendedAttribute_xml = arcpy.GetParameterAsText(0)
        gdb = arcpy.GetParameterAsText(1)
        folder = os.path.dirname(extendedAttribute_xml)
        filename = os.path.basename(extendedAttribute_xml)
        # 入力値のチェック
        if filename != EXTATTR_KEYFILE:
            arcpy.AddError(u"{0} というファイルを選択する必要があります(大文字小文字を含め同一である必要があります)".format(EXTATTR_KEYFILE)) #v111:メッセージ変更
            return
        if os.path.splitext(gdb)[1].upper() != ".GDB":
            arcpy.AddError(u"{0} は3D都市モデルの変換先ファイル ジオデータベースを選択する必要があります".format(gdb))
            return
        
        # extendedAttribute_key.xml の情報をもとに、拡張属性ファイル名とコード値ドメインの説明を作成
        xmlfiles = createExtendedAttributeFiles(extendedAttribute_xml)
        # 既存ドメインを取得
        domains = arcpy.Describe(gdb).domains
        
        arcpy.env.workspace = gdb
        # extendedAttribute_keyXX.xml を開いてコード値ドメインを設定
        for xmlfile in xmlfiles:
            extendedAttribute_key_xml = os.path.join(folder, xmlfile)
            if os.path.exists(extendedAttribute_key_xml):
                domainName, domainDict = createDomainValues(extendedAttribute_key_xml)
                # v111: extendedAttribute_keyX.xml と、<gml:name>ExtendedAttribute_keyX</gml:name> の整合チェックを追加。
                # （<gml:name>ExtendedAttribute_key</gml:name>  で番号が入っていないケースがあるため）
                fname = os.path.splitext(xmlfile)[0]
                if domainName.upper() != fname.upper():
                    arcpy.AddError(u"{0} ファイル内の <gml:name>{1}</gml:name>  の定義が正しくないため、このファイルで定義されている拡張属性のコード値ドメイン定義とフィールドへの適用は実行できません".format(xmlfile, domainName))
                else:
                    domainDesc = xmlfiles[xmlfile]
                    # ドメインの作成（既存ドメインが存在する場合は処理しない）
                    if domainName not in domains:
                        #print("Creating domain " + domainName)
                        arcpy.AddMessage(u"{0}: ドメイン を作成します".format(domainName))
                        arcpy.CreateDomain_management(gdb, domainName, domainDesc, "TEXT", "CODED")
                        # 作成したドメインにコードと説明を追加
                        for code in domainDict:
                            codeDesc = domainDict[code]
                            if (codeDesc != None): #v112: codeDesc  が空文字の場合への対応                            
                                arcpy.AddMessage(u"{0}: ドメイン に{1} , {2} のコードを追加します".format(domainName,code,codeDesc))
                                arcpy.AddCodedValueToDomain_management(gdb, domainName, code, codeDesc)
                            else:
                                arcpy.AddWarning(u"{0}: ドメイン に追加する{1} のコードの説明がないので処理をスキップします".format(domainName,code))
                        #print("Add code " code)
                    else:
                        arcpy.AddWarning(u"{0}: ドメイン はすでに存在しているので、ドメイン 作成の処理はスキップします".format(domainName))
                    #ドメインを指定フィーチャクラスに適用
                    # lod0_Building, lod1_Building, lod2_Building, lod1_BuildingPart, lod2_BuildingPart
                    fieldName = createFieldNameFromFilename(xmlfile) #例) uro_extendedAttribute_key2
                    for fc in FCNAMES:
                        if arcpy.Exists(fc):
                            fieldNames = [f.name for f in arcpy.ListFields(fc)]
                            if fieldName in fieldNames:
                                arcpy.AddMessage(u"{0} の{1} フィールドに{2} ドメインを適用します".format(fc, fieldName, domainName))
                                arcpy.AssignDomainToField_management(fc, fieldName, domainName)
                                arcpy.AlterField_management(fc, fieldName, new_field_alias=domainDesc) #v113: フィールドエイリアスをドメインの説明にする
                            else:
                                arcpy.AddWarning(u"{0} に{1} フィールドが定義されていないため、ドメインの適用をスキップします".format(fc, fieldName))

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

