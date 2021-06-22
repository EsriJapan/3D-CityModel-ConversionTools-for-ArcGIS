# 3D-CityModel-ConversionTools-for-ArcGIS
# 概要
「3D 都市モデルデータ変換ツール for ArcGIS」 は、[PLATEAU](https://www.mlit.go.jp/plateau/) で整備し、G空間情報センターで公開している[3D都市モデル](https://www.geospatial.jp/ckan/dataset/plateau)（CityGML）のデータを、ArcGIS で利用可能な[ファイル ジオデータベース](https://pro.arcgis.com/ja/pro-app/latest/help/data/geodatabases/manage-file-gdb/file-geodatabases.htm) へ変換するツールです。  
本ツールで変換可能なデータは、[3D 都市モデル標準製品仕様書 series No.01（2021/03/26　1.0.0版）](https://www.mlit.go.jp/plateau/file/libraries/doc/plateau_doc_0001_ver01.pdf) に対応した 3D都市モデル（東京 23 区、および全国55都市）です。  
本ツールは、国土交通省の[Project PLATEAU](https://www.mlit.go.jp/plateau/) で、国土交通省都市局、国際航業株式会社、ESRIジャパン株式会社が共同で作成・開発したものです。
  
### 更新履歴
* 2021/05/18 ： 「3D 都市モデルデータ変換ツール for ArcGIS」バージョン1.1.1 を公開
* 2021/05/31 ： 「3D 都市モデルデータ変換ツール for ArcGIS」バージョン1.1.2 を公開
* 2021/06/22 ： 「3D 都市モデルデータ変換ツール for ArcGIS」バージョン1.1.3 を公開
  ※ バージョン1.1.1 をご利用頂いていた方は、1.1.2へ更新いただくことを推奨いたします。
  
  
## 対応データの一覧

3D都市モデル（CityGML）の対応している地物と、変換されるファイル ジオデータベース内のフィーチャクラスの関係は、次の通りです。

|地物||対応状況|変換先のフィーチャクラス名|
|:---|:---|:---:|:---|
|建築物||〇（LOD0、1、2ごと分解して変換）|lod0_Building, lod1_Building, lod2_Building|
||建築物部分|〇（LOD1、2ごとに分解して変換）|lod1_BuildingPart, lod2_BuildingPart|
||屋根|〇|lod2_RoofSurface|
||外壁|〇|lod2_WallSurface|
||接地面|〇|lod2_GroundSurface|
||外部天井|〇|lod2_OuterCeilingSurface|
||外部床面|〇|lod2_OuterFloorSurface|
||閉鎖面|〇|lod2_ClosureSurface|
||建築物付属物|〇|lod2_BuildingInstallation|
|道路||〇|lod1_Road|
|地形（起伏）|TIN|〇|lod1_TinRelief|
|都市計画区域||〇|lod0_UrbanPlan|
|区域区分||〇|lod0_AreaClassification|
|地域地区||〇|lod0_DistrictAndZones|
|土地利用||〇|lod1_LandUse|
|洪水浸水想定区域、津波浸水想定区域||〇|lod1_WaterBody|
|災害リスク||〇|lod0_GenericCityObject|

※ 変換されるファイル ジオデータベースの詳細な定義は、[3D 都市モデルデータ変換ツール for ArcGIS 操作マニュアルの付属資料](https://github.com/EsriJapan/3D-CityModel-ConversionTools-for-ArcGIS/blob/main/Doc/3D%E9%83%BD%E5%B8%82%E3%83%A2%E3%83%87%E3%83%AB%E3%83%87%E3%83%BC%E3%82%BF%E5%A4%89%E6%8F%9B%E3%83%84%E3%83%BC%E3%83%AB%20for%20ArcGIS%E6%93%8D%E4%BD%9C%E3%83%9E%E3%83%8B%E3%83%A5%E3%82%A2%E3%83%AB%201.1.3%E7%89%88%EF%BC%88%E6%9D%B1%E4%BA%AC23%E5%8C%BA%E3%83%BB55%E9%83%BD%E5%B8%82%E7%89%88%EF%BC%89_%E4%BB%98%E5%B1%9E%E8%B3%87%E6%96%99.xlsx)をご参照ください。

## 動作環境
本ツールを実行するには、バージョン 2.6 以上のArcGIS Pro とData Interoperability エクステンション をインストールし、ライセンスを有効化している必要があります。  
詳細な動作環境、およびData Interoperability エクステンション のインストール方法は、以下をご参照ください。
* [ArcGIS Pro の動作環境](https://www.esrij.com/products/arcgis-desktop/environments/arcgis-pro/)
* [Data Interoperability エクステンションのインストール](https://pro.arcgis.com/ja/pro-app/latest/help/data/data-interoperability/install-the-data-interoperability-extension.htm)

### 利用方法
本ツールを使って変換するまでには、大まかに次のステップが必要です。操作方法の詳細は[3D 都市モデルデータ変換ツール for ArcGIS 操作マニュアル](https://github.com/EsriJapan/3D-CityModel-ConversionTools-for-ArcGIS/blob/main/Doc/3D%E9%83%BD%E5%B8%82%E3%83%A2%E3%83%87%E3%83%AB%E3%83%87%E3%83%BC%E3%82%BF%E5%A4%89%E6%8F%9B%E3%83%84%E3%83%BC%E3%83%AB%20for%20ArcGIS%E6%93%8D%E4%BD%9C%E3%83%9E%E3%83%8B%E3%83%A5%E3%82%A2%E3%83%AB%201.1.3%E7%89%88%EF%BC%88%E6%9D%B1%E4%BA%AC23%E5%8C%BA%E3%83%BB55%E9%83%BD%E5%B8%82%E7%89%88%EF%BC%89.pdf) をご参照ください。
* [3D 都市モデルデータ変換ツール for ArcGIS をダウンロード](https://github.com/EsriJapan/3D-CityModel-ConversionTools-for-ArcGIS/releases/download/v1.1.3/3DCityModel_convert_v113.zip)します。
* ダウンロードしたZIP ファイルを、任意の場所に解凍します。
* ArcGIS Pro を起動し、フォルダー接続の追加 で、解凍したフォルダを指定します。
* G空間情報センターから、必要な3D都市モデル（CityGML）のデータをダウンロードし、解凍しておきます。
* 操作マニュアルの「2.4 3D都市モデルデータ変換ツールの実行方法」を参照しながら、それぞれの地物を変換します。
* 必要に応じて、拡張属性にコード値ドメインの割り当てするスクリプトツールや、汎用属性セットをフィールドに展開するスクリプトツールを実行します。

### 免責事項
* 本ツールに含まれるカスタムツールは、サンプルとして提供しているものであり、動作に関する保証、および製品ライフサイクルに従った Esri 製品サポート サービスは提供しておりません。
* 本ツールに含まれるツールによって生じた損失及び損害等について、一切の責任を負いかねますのでご了承ください。
* 弊社で提供しているEsri 製品サポートサービスでは、本ツールに関しての Ｑ＆Ａ サポートの受付を行っておりませんので、予めご了承の上、ご利用ください。詳細は[
ESRIジャパン GitHub アカウントにおけるオープンソースへの貢献について](https://github.com/EsriJapan/contributing)をご参照ください。

## ライセンス
Copyright 2021 Esri Japan Corporation.

Apache License Version 2.0（「本ライセンス」）に基づいてライセンスされます。あなたがこのファイルを使用するためには、本ライセンスに従わなければなりません。
本ライセンスのコピーは下記の場所から入手できます。

> http://www.apache.org/licenses/LICENSE-2.0

適用される法律または書面での同意によって命じられない限り、本ライセンスに基づいて頒布されるソフトウェアは、明示黙示を問わず、いかなる保証も条件もなしに「現状のまま」頒布されます。本ライセンスでの権利と制限を規定した文言については、本ライセンスを参照してください。

ライセンスのコピーは本リポジトリの[ライセンス ファイル](./LICENSE)で利用可能です。
