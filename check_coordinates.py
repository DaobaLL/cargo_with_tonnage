from pymongo import MongoClient
import math

# MongoDB 连接设置
client = MongoClient('mongodb://localhost:27017/')
db = client['cargo_with_tonnage']
cargo_collection = db['cargo']
ship_collection = db['ship']
city_coordinates_collection = db['city_coordinates']

# 检查并更新集合中的坐标信息
def check_and_update_coordinates(collection, port_fields):
    """
    遍历集合中的指定字段，检查并更新坐标信息。
    如果城市名称为 NaN，则删除对应的坐标字段。
    如果坐标有效，则更新所有匹配的文档。
    """
    for port_field, coordinates_field in port_fields.items():
        print(f"开始检查集合中的字段: {port_field} -> {coordinates_field}")
        for document in collection.find({coordinates_field: {"$exists": True}}):
            if is_nan_city_name(document, port_field):
                remove_coordinates(collection, document, coordinates_field)
                continue
            update_coordinates_if_valid(collection, document, port_field, coordinates_field)

# 检查城市名称是否为 NaN
def is_nan_city_name(document, port_field):
    """
    判断文档中的城市名称是否为 NaN。
    """
    return isinstance(document[port_field], float) and math.isnan(document[port_field])

# 删除无效的坐标字段
def remove_coordinates(collection, document, coordinates_field):
    """
    删除文档中无效的坐标字段。
    """
    print(f"文档 ID: {document['_id']} 的城市名称为 NaN，删除 {coordinates_field}")
    collection.update_one(
        {"_id": document["_id"]},
        {"$unset": {coordinates_field: ""}}
    )

# 更新有效的坐标信息
def update_coordinates_if_valid(collection, document, port_field, coordinates_field):
    """
    如果坐标有效，则更新所有匹配的文档为相同的坐标信息。
    """
    coordinates = document[coordinates_field]
    if isinstance(coordinates, dict) and coordinates.get('latitude') and coordinates.get('longitude') and coordinates.get('osm_id'):
        try:
            coordinates['latitude'] = float(coordinates['latitude']) if isinstance(coordinates['latitude'], str) else coordinates['latitude']
            coordinates['longitude'] = float(coordinates['longitude']) if isinstance(coordinates['longitude'], str) else coordinates['longitude']
        except ValueError as e:
            print(f"文档 ID: {document['_id']} 的 {coordinates_field} 包含无效的经纬度值: {coordinates}, 错误: {e}")
            return
        print(f"文档 ID: {document['_id']} 的 {coordinates_field} 存在有效数据: {coordinates}")
        collection.update_many(
            {port_field: document[port_field]},
            {"$set": {coordinates_field: coordinates}}
        )
        print(f"已更新所有匹配 {port_field}: {document[port_field]} 的文档为相同的经纬度和 osm_id")
    else:
        print(f"文档 ID: {document['_id']} 的 {coordinates_field} 数据无效，跳过")

# 删除港口名称为 NIL 的数据
def delete_nil_port_data(collection, port_fields):
    """
    删除集合中港口名称为 NIL 的所有文档。
    """
    for port_field in port_fields.keys():
        result = collection.delete_many({port_field: "NIL"})
        print(f"已删除 {result.deleted_count} 条港口名称为 NIL 的记录 (字段: {port_field})")

# 统计集合中的坐标信息
def count_coordinates(collection, port_fields):
    """
    统计集合中有坐标、无坐标、城市名称为 NaN、有效记录和非 NaN 但无坐标的记录数量。
    """
    with_coordinates = 0
    without_coordinates = 0
    with_nan = 0
    valid_records = 0
    non_nan_without_coordinates = 0
    for port_field, coordinates_field in port_fields.items():
        with_coordinates += collection.count_documents({coordinates_field: {"$exists": True}})
        without_coordinates += collection.count_documents({coordinates_field: {"$exists": False}})
        with_nan += collection.count_documents({port_field: {"$type": "double", "$eq": float('nan')}})
        valid_records += collection.count_documents({
            coordinates_field: {"$exists": True},
            f"{coordinates_field}.latitude": {"$type": "double"},
            f"{coordinates_field}.longitude": {"$type": "double"}
        })
        non_nan_without_coordinates += collection.count_documents({
            port_field: {"$not": {"$type": "double", "$eq": float('nan')}},
            coordinates_field: {"$exists": False}
        })
    return with_coordinates, without_coordinates, with_nan, valid_records, non_nan_without_coordinates

# 总结城市的经纬度信息
def summarize_city_coordinates():
    """
    从 cargo 和 ship 集合中提取城市及其坐标信息，并存储到 city_coordinates 集合中。
    """
    city_coordinates = {}
    collect_city_coordinates(cargo_collection, "loading_port", "loading_port_coordinates", city_coordinates)
    collect_city_coordinates(ship_collection, "open_port", "open_port_coordinates", city_coordinates)
    store_city_coordinates(city_coordinates)

# 收集城市的经纬度信息
def collect_city_coordinates(collection, port_field, coordinates_field, city_coordinates):
    """
    遍历集合，收集城市名称及其对应的经纬度信息。
    """
    for document in collection.find({coordinates_field: {"$exists": True}}):
        city = document.get(port_field)
        coordinates = document.get(coordinates_field)
        if city and isinstance(coordinates, dict) and coordinates.get("latitude") and coordinates.get("longitude"):
            city_coordinates[city] = {
                "latitude": float(coordinates["latitude"]),
                "longitude": float(coordinates["longitude"]),
                "source": coordinates.get("source", "unknown")
            }

# 存储城市的经纬度信息到集合
def store_city_coordinates(city_coordinates):
    """
    将收集到的城市及其坐标信息存储到 city_coordinates 集合中。
    即使没有经纬度信息的城市也存储，并在存储后去重。
    """
    for city, coordinates in city_coordinates.items():
        city_coordinates_collection.update_one(
            {"city": city},
            {"$set": {"coordinates": coordinates}},
            upsert=True
        )
    print(f"已总结并存储 {len(city_coordinates)} 个城市的经纬度信息到 city_coordinates 集合")

    # 去重操作
    unique_cities = {}
    for document in city_coordinates_collection.find():
        city = document.get("city")
        if city not in unique_cities:
            unique_cities[city] = document
        else:
            # 删除重复的文档
            city_coordinates_collection.delete_one({"_id": document["_id"]})
    print("已完成 city_coordinates 集合的去重操作")

# 主函数
def all_action():
    """
    主函数，执行检查、更新和总结操作。
    """
    cargo_port_fields = {
        'loading_port': 'loading_port_coordinates',
        'discharge_port': 'discharge_port_coordinates'
    }
    ship_port_fields = {
        'open_port': 'open_port_coordinates'
    }

    # 删除港口名称为 NIL 的数据
    delete_nil_port_data(cargo_collection, cargo_port_fields)
    delete_nil_port_data(ship_collection, ship_port_fields)

    check_and_update_coordinates(cargo_collection, cargo_port_fields)
    check_and_update_coordinates(ship_collection, ship_port_fields)

    cargo_with, cargo_without, cargo_nan, cargo_valid, cargo_non_nan_without = count_coordinates(cargo_collection, cargo_port_fields)
    print(f"货物集合: {cargo_with} 条记录有坐标信息, {cargo_without} 条记录没有坐标信息, {cargo_nan} 条记录城市名称为 NaN, {cargo_valid} 条记录有效, {cargo_non_nan_without} 条记录非 NaN 但没有坐标信息")

    ship_with, ship_without, ship_nan, ship_valid, ship_non_nan_without = count_coordinates(ship_collection, ship_port_fields)
    print(f"船舶集合: {ship_with} 条记录有坐标信息, {ship_without} 条记录没有坐标信息, {ship_nan} 条记录城市名称为 NaN, {ship_valid} 条记录有效, {ship_non_nan_without} 条记录非 NaN 但没有坐标信息")

    summarize_city_coordinates()
    print("检查并更新完成")

def main():
    """
    主函数入口，执行所有操作。
    """
    all_action()

if __name__ == "__main__":
    main()
