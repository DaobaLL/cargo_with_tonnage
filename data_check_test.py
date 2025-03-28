
from pymongo import MongoClient
import pandas as pd

# 读取 mongodb 数据，检查数据是否正确
# 数据库名称是 cargo_with_tonnage
# 只读取数据库下个集合前五个数据

# MongoDB 连接设置
client = MongoClient('mongodb://localhost:27017/')
db = client['cargo_with_tonnage']

# 读取 cargo 集合前五个数据
cargo_collection = db['cargo']
cargo_data = list(cargo_collection.find().limit(5))
cargo_df = pd.DataFrame(cargo_data)
print("Cargo Data:")
print(cargo_df)

# 读取 ship 集合前五个数据
ship_collection = db['ship']
ship_data = list(ship_collection.find().limit(5))
ship_df = pd.DataFrame(ship_data)
print("\nShip Data:")
print(ship_df)

# 读取 result 集合前五个数据
result_collection = db['result']
result_data = list(result_collection.find().limit(5))
result_df = pd.DataFrame(result_data)
print("\nResult Data:")
print(result_df)

# 打印各表存储了多少数据
cargo_count = cargo_collection.count_documents({})
ship_count = ship_collection.count_documents({})
result_count = result_collection.count_documents({})
print(f"Cargo collection contains {cargo_count} documents.")
print(f"Ship collection contains {ship_count} documents.")
print(f"Result collection contains {result_count} documents.")
