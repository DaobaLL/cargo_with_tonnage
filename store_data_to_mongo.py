# Function: Store data from Excel files to MongoDB.
# Usage: Run this script to store data from Excel files to MongoDB.
import pandas as pd
from datetime import datetime
try:
    from pymongo import MongoClient
except ImportError:
    print("pymongo 模块未找到，请运行 'pip install pymongo' 进行安装")
    exit()

# MongoDB 连接设置
client = MongoClient('mongodb://localhost:27017/')
db = client['cargo_with_tonnage']

# 读取货物数据
cargo_df = pd.read_excel('【吉安航】智能船货盘提取助手_货盘.xlsx')
cargo_collection = db['cargo']

# 数据清洗函数
def clean_date(value):
    try:
        date_value = datetime.strptime(str(value), '%Y-%m-%d')
        return date_value if pd.notna(date_value) else None
    except (ValueError, TypeError):
        return None

def clean_numeric(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

# 数据清洗
cargo_df['装运开始日期-LAY-DATE'] = cargo_df['装运开始日期-LAY-DATE'].apply(clean_date)
cargo_df['装运结束日期-CANCELING-DATE'] = cargo_df['装运结束日期-CANCELING-DATE'].apply(clean_date)
cargo_df['最小货量-QUANTITY'] = cargo_df['最小货量-QUANTITY'].apply(clean_numeric)
cargo_df['最大货量-QUANTITY'] = cargo_df['最大货量-QUANTITY'].apply(clean_numeric)

# 清空集合
cargo_collection.delete_many({})

# 插入货物数据
for _, row in cargo_df.iterrows():
    cargo_document = {
        'cargo_name': row['货物名称-CARGO-NAME'],
        'cargo_name_unified': row['CARGO NAME 统一'],
        'loading_port': row['统一装货港口'],
        'loading_country': row['装港国家-L-PORT-COUNTRY'],
        'discharge_port': row['统一卸货港口'],
        'discharge_country': row['卸港国家-D-PORT-COUNTRY'],
        'sf_package': row['积载包装-SF-PACKAGE'],
        'min_quantity': row['最小货量-QUANTITY'],
        'max_quantity': row['最大货量-QUANTITY'],
        'lay_date': row['装运开始日期-LAY-DATE'] if pd.notna(row['装运开始日期-LAY-DATE']) else None,
        'canceling_date': row['装运结束日期-CANCELING-DATE'] if pd.notna(row['装运结束日期-CANCELING-DATE']) else None
    }
    cargo_collection.insert_one(cargo_document)

# 读取船舶数据
ship_df = pd.read_excel('【吉安航】智能船货盘提取助手_船盘.xlsx')
ship_collection = db['ship']

# 数据清洗
ship_df['空船日期-OPEN-DATE'] = ship_df['空船日期-OPEN-DATE'].apply(clean_date)
ship_df['载重吨-DWT'] = ship_df['载重吨-DWT'].apply(clean_numeric)
ship_df['散装舱容-GRAIN-CAPACITY'] = ship_df['散装舱容-GRAIN-CAPACITY'].apply(clean_numeric)
ship_df['包装舱容-BALE-CAPACITY'] = ship_df['包装舱容-BALE-CAPACITY'].apply(clean_numeric)
ship_df['船长-LOA'] = ship_df['船长-LOA'].apply(clean_numeric)
ship_df['总吨位-GRT'] = ship_df['总吨位-GRT'].apply(clean_numeric)
ship_df['夏季海水吃水-DRAFT'] = ship_df['夏季海水吃水-DRAFT'].apply(clean_numeric)
ship_df['建造年份-BUILT-YEAR'] = ship_df['建造年份-BUILT-YEAR'].apply(clean_numeric)
ship_df['载货吨-DWCC'] = ship_df['载货吨-DWCC'].apply(clean_numeric)

# 清空集合
ship_collection.delete_many({})

# 插入船舶数据
for _, row in ship_df.iterrows():
    ship_document = {
        'vessel_name': row['船舶代码-ID'],
        'dwt': row['载重吨-DWT'],
        'open_date': row['空船日期-OPEN-DATE'] if pd.notna(row['空船日期-OPEN-DATE']) else None,
        'open_port': row['统一空船港口'],
        'open_country': row['国家-OPEN-COUNTRY'],
        'grain_capacity': row['散装舱容-GRAIN-CAPACITY'],
        'bale_capacity': row['包装舱容-BALE-CAPACITY'],
        'loa': row['船长-LOA'],
        'grt': row['总吨位-GRT'],
        'draft': row['夏季海水吃水-DRAFT'],
        'built_year': row['建造年份-BUILT-YEAR'],
        'gear': row['吊机-GEAR'],
        'dwcc': row['载货吨-DWCC'],
        'deck': row['甲板数-DECK'],
        'p_and_i': row['P&I']
    }
    ship_collection.insert_one(ship_document)

# 更新货物集合中的坐标和船舶集合中的坐标逻辑已移至 update_coordinates.py

cargo_count = cargo_collection.count_documents({})
ship_count = ship_collection.count_documents({})
print(f"Cargo collection contains {cargo_count} documents.")
print(f"Ship collection contains {ship_count} documents.")
