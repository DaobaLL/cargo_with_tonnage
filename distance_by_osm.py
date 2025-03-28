# 这个脚本用于计算匹配记录的港口距离，并将结果存储到 MongoDB 的 distance_result 集合中。
# 该脚本使用 geopy 库来计算地理坐标之间的距离，并将结果存储到 MongoDB 中。

import pymongo
from datetime import datetime, timedelta
import numpy as np
from math import radians, sin, cos, sqrt, asin
import collections
import math  # Add this import for NaN checks
from geopy.distance import geodesic  # Import geopy's geodesic function

# 连接到MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["cargo_with_tonnage"]
ship_collection = db["ship"]
cargo_collection = db["cargo"]
result_collection = db["tonnage_result"]
distance_result_collection = db["distance_result"]
city_coordinates_collection = db["city_coordinates"]  # Add reference to city_coordinates collection

def haversine(lon1, lat1, lon2, lat2):
    """Haversine公式计算球面距离（单位：公里）"""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 6371 * 2 * asin(sqrt(a))

def batch_calculate():
    """批量计算所有匹配记录的港口距离"""
    records = list(result_collection.find({}, {
        "loading_port_coordinates": 1,
        "open_port_coordinates": 1
    }))
    
    # 将坐标转换为地理坐标格式
    for record in records:
        result_collection.update_one(
            {"_id": record["_id"]},
            {"$set": {
                "loading_port_coordinates_geo": {
                    "type": "Point",
                    "coordinates": [
                        record["loading_port_coordinates"]["longitude"],
                        record["loading_port_coordinates"]["latitude"]
                    ]
                },
                "open_port_coordinates_geo": {
                    "type": "Point",
                    "coordinates": [
                        record["open_port_coordinates"]["longitude"],
                        record["open_port_coordinates"]["latitude"]
                    ]
                }
            }}
        )
    
    # 矢量化计算优化（提升性能）
    lons1 = np.array([r["loading_port_coordinates"]["longitude"] for r in records])
    lats1 = np.array([r["loading_port_coordinates"]["latitude"] for r in records])
    lons2 = np.array([r["open_port_coordinates"]["longitude"] for r in records])
    lats2 = np.array([r["open_port_coordinates"]["latitude"] for r in records])
    
    distances_km = 6371 * 2 * np.arcsin(np.sqrt(
        np.sin(np.radians(lats2 - lats1)/2)**2 + 
        np.cos(np.radians(lats1)) * np.cos(np.radians(lats2)) * 
        np.sin(np.radians(lons2 - lons1)/2)**2
    ))
    
    # 更新数据库
    for i, doc in enumerate(records):
        result_collection.update_one(
            {"_id": doc["_id"]},
            {"$set": {
                "distance_km": round(float(distances_km[i]), 2),
                "distance_nm": round(float(distances_km[i] / 1.852), 2)
            }}
        )

def calculate_distances_for_matches():
    """计算匹配记录的港口距离并存储到 distance_result 集合中"""
    matched_records = result_collection.find({
        "loading_port": {"$ne": None},
        "open_port": {"$ne": None}
    })

    results_to_insert = []
    for record in matched_records:
        # Fetch coordinates for loading_port and open_port
        loading_city = city_coordinates_collection.find_one({"city": record["loading_port"]})
        open_city = city_coordinates_collection.find_one({"city": record["open_port"]})

        # Skip if coordinates are not found
        if not loading_city or not open_city:
            continue

        loading_coords = loading_city["coordinates"]
        open_coords = open_city["coordinates"]

        # Use geopy's geodesic function to calculate distance
        distance_km = geodesic(
            (loading_coords["latitude"], loading_coords["longitude"]),
            (open_coords["latitude"], open_coords["longitude"])
        ).kilometers
        
        # 仅处理小于1000公里的记录
        if distance_km < 1000:
            print(f"发现一个距离小于1000KM的配对，距离是 {round(distance_km, 2)} km")  # Add log statement
            distance_nm = distance_km / 1.852  # Convert kilometers to nautical miles

            results_to_insert.append({
                "match_id": record["_id"],
                "ship_id": record["ship_id"],
                "cargo_id": record["cargo_id"],
                "distance_km": round(distance_km, 2),
                "distance_nm": round(distance_nm, 2),
                "vessel_name": record["vessel_name"],
                "cargo_name": record["cargo_name"],
                "loading_port": record["loading_port"],
                "loading_country": record.get("loading_country"),
                "open_port": record["open_port"],
                "open_country": record.get("open_country"),
                "open_date": record.get("open_date"),
                "open_date_format": record.get("open_date").strftime("%Y-%m-%d") if record.get("open_date") else None,  # Add formatted date
                "lay_date": record.get("lay_date"),
                "lay_date_format": record.get("lay_date").strftime("%Y-%m-%d") if record.get("lay_date") else None,  # Add formatted date
                "canceling_date": record.get("canceling_date"),
                "canceling_date_format": record.get("canceling_date").strftime("%Y-%m-%d") if record.get("canceling_date") else None,  # Add formatted date
                "dwcc": record.get("dwcc"),
                "min_quantity": record.get("min_quantity"),
                "max_quantity": record.get("max_quantity"),
                "loading_port_coordinates_geo": {
                    "type": "Point",
                    "coordinates": [loading_coords["longitude"], loading_coords["latitude"]]
                },
                "open_port_coordinates_geo": {
                    "type": "Point",
                    "coordinates": [open_coords["longitude"], open_coords["latitude"]]
                }
            })

    if results_to_insert:
        distance_result_collection.insert_many(results_to_insert)
        print(f"已计算并存储 {len(results_to_insert)} 条匹配记录的距离")

if __name__ == "__main__":
    # 计算匹配记录的距离并存储到 distance_result 集合
    calculate_distances_for_matches()