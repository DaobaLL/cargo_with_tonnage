# Description: 匹配货物和吨位
# This script matches cargo with tonnage based on the lay date, canceling date, minimum quantity, and maximum quantity.
import pymongo
from datetime import datetime, timedelta

# 连接到MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["cargo_with_tonnage"]
ship_collection = db["ship"]
cargo_collection = db["cargo"]
result_collection = db["tonnage_result"]

def match_cargo_tonnage():
    today = datetime.now()
    matched_results = []

    print("正在匹配...")
    cargos = cargo_collection.find({"lay_date": {"$gte": today}})
    for cargo in cargos:
        lay_date = cargo["lay_date"]
        canceling_date = cargo["canceling_date"]
        min_quantity = cargo["min_quantity"]
        max_quantity = cargo["max_quantity"]

        ships = ship_collection.find({
            "open_date": {
                "$gte": lay_date - timedelta(days=2),
                "$lte": canceling_date + timedelta(days=2)
            },
            "dwcc": {
                "$gt": min_quantity,
                "$lte": max_quantity * 1.05
            }
        })
        # 遍历所有符合条件的船舶
        for ship in ships:
            print("已经发现一个配对")
            matched_results.append({
                "ship_id": ship["_id"],
                "vessel_name": ship["vessel_name"],
                "cargo_id": cargo["_id"],
                "cargo_name": cargo["cargo_name"],
                "open_date": ship["open_date"],
                "open_date_format": ship["open_date"].strftime("%Y-%m-%d"),  # Add formatted date
                "lay_date": lay_date,
                "lay_date_format": lay_date.strftime("%Y-%m-%d"),  # Add formatted date
                "canceling_date": canceling_date,
                "canceling_date_format": canceling_date.strftime("%Y-%m-%d"),  # Add formatted date
                "dwcc": ship["dwcc"],
                "min_quantity": cargo["min_quantity"],
                "max_quantity": cargo["max_quantity"],
                "loading_port": cargo["loading_port"],
                "loading_country": cargo["loading_country"],
                "open_port": ship["open_port"],
                "open_country": ship["open_country"]
            })

    if matched_results:
        result_collection.insert_many(matched_results)
        print("匹配完成，结果已存储")

if __name__ == "__main__":
    match_cargo_tonnage()
