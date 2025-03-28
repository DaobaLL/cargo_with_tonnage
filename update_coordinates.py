# -*- coding: utf-8 -*-
# 通过城市名称获取经纬度并存储到 MongoDB 中
# 该脚本使用 Nominatim 服务获取城市的经纬度，并将其存储到 MongoDB 中

import requests
import time
import math
from pymongo import MongoClient
from diskcache import Cache
from datetime import datetime

# MongoDB 连接设置
def connect_to_mongo():
    """连接到 MongoDB 数据库"""
    client = MongoClient('mongodb://localhost:27017/')
    db = client['cargo_with_tonnage']
    return db

# 缓存设置
def setup_cache():
    """设置磁盘缓存"""
    return Cache('./geo_cache')

# 智能请求间隔
def smart_delay(last_request_time):
    """智能延迟以避免频繁请求"""
    if last_request_time:
        elapsed = (datetime.now() - last_request_time).total_seconds()
        min_delay = 0.5  # 设置最小延迟为0.5秒
        if elapsed < min_delay:
            time.sleep(min_delay - elapsed)
    return datetime.now()

# 验证坐标数据
def validate_coordinates(data):
    """验证坐标数据是否有效"""
    if not data:
        return False
    try:
        lat = float(data['latitude'])
        lon = float(data['longitude'])
        return -90 <= lat <= 90 and -180 <= lon <= 180
    except:
        return False

# 获取坐标
def get_coordinates(location_name, cache, headers, last_request_time):
    """通过 Nominatim 服务获取地理坐标"""
    if location_name is None or (isinstance(location_name, float) and math.isnan(location_name)) or str(location_name).lower() == 'nan':
        return None
    try:
        last_request_time = smart_delay(last_request_time)
        params = {'format': 'jsonv2', 'addressdetails': 1, 'q': location_name}
        response = requests.get(
            'https://nominatim.openstreetmap.org/search',
            params=params,
            headers=headers,
            timeout=15
        )
        response.raise_for_status()
        response_data = response.json()
        if response_data:
            first_result = response_data[0]
            if 'lat' in first_result and 'lon' in first_result:
                result = {
                    'latitude': float(first_result['lat']),
                    'longitude': float(first_result['lon']),
                    'osm_id': first_result.get('osm_id'),
                    'source': 'nominatim'
                }
                if validate_coordinates(result):
                    return result
    except Exception as e:
        print(f"服务 nominatim 获取 {location_name} 数据时出错: {e}")
    return None

# 更新坐标
def update_coordinates(collection, port_fields, cache, headers):
    """更新 MongoDB 集合中的坐标字段"""
    for port_field, coordinates_field in port_fields.items():
        print(f"开始处理集合中的字段: {port_field} -> {coordinates_field}")
        total_documents = collection.count_documents({port_field: {"$exists": True}, coordinates_field: {"$exists": False}})
        for index, document in enumerate(collection.find({port_field: {"$exists": True}, coordinates_field: {"$exists": False}}), start=1):
            location_name = document[port_field]
            if coordinates_field in document and validate_coordinates(document[coordinates_field]):
                print(f"[正在处理第{index}/{total_documents}条数据][读取成功][{location_name}]已存在有效经纬度，跳过")
                continue
            try:
                coordinates = get_coordinates(location_name, cache, headers, None)
                if coordinates:
                    collection.update_many(
                        {port_field: location_name},
                        {"$set": {coordinates_field: coordinates}}
                    )
                    print(f"[正在处理第{index}/{total_documents}条数据][获取成功][{location_name}]更新为 {coordinates}")
                else:
                    print(f"[正在处理第{index}/{total_documents}条数据][失败][{location_name}]未能获取坐标")
            except Exception as e:
                print(f"[正在处理第{index}/{total_documents}条数据][失败][{location_name}]错误: {e}")

# 主函数
def main():
    """主函数，执行更新坐标逻辑"""
    db = connect_to_mongo()
    cache = setup_cache()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }
    cargo_port_fields = {
        'loading_port': 'loading_port_coordinates',
        'discharge_port': 'discharge_port_coordinates'
    }
    ship_port_fields = {
        'open_port': 'open_port_coordinates'
    }
    update_coordinates(db['cargo'], cargo_port_fields, cache, headers)
    update_coordinates(db['ship'], ship_port_fields, cache, headers)
    print("数据已成功存储到 MongoDB 中并更新了坐标")

if __name__ == "__main__":
    main()
