# coding : utf-8
"""
2021/05/30 以前の、変換ツールで変換作業を行った3D都市モデルFGDB内のフィーチャクラスの
鉛直座標系の定義を変更するツール

対象:
XY座標　GCS_JGD_2011 （WKID:6668）, Z座標 JGD_2011 （WKID:115741）が定義されているフィーチャクラス

を次のように更新する
XY座標　GCS_JGD_2011 （WKID:6668）, Z座標 JGD2011_vertical_height （WKID:6695）
"""

import os
import arcpy

def updateVerticalSpref(ws):
    arcpy.env.workspace = ws
    new_spref = arcpy.SpatialReference(6668, 6695)
    fcs = arcpy.ListFeatureClasses("*")
    i = 0
    for fc in fcs:
        spref = arcpy.Describe(fc).spatialReference
        if spref.factoryCode == 6668:
            if spref.VCS is not None:
                if spref.VCS.factoryCode == 115741:
                    i += 1
                    arcpy.AddMessage(u"{0} の 鉛直座標系を{1} に更新します".format(fc, "JGD2011_vertical_height （WKID:6695）"))
                    arcpy.management.DefineProjection(fc, new_spref)
    if i == 0:
        arcpy.AddWarning(u"{0} には鉛直座標系の更新対象のフィーチャクラスが存在しませんでした".format(os.path.split(ws)[1]))
    else:
        arcpy.AddMessage(u"{0} の {1} 件のフィーチャクラスの鉛直座標系を更新しました".format(os.path.split(ws)[1], i))
    

def main():
    try:
        arcpy.AddMessage(u"鉛直座標系の更新処理開始：")

        input_gdb = arcpy.GetParameterAsText(0)

        updateVerticalSpref(input_gdb)

        arcpy.AddMessage(u"処理終了：")
    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
    except Exception as e:
        arcpy.AddError(e.args[0])

if __name__ == '__main__':
    main()