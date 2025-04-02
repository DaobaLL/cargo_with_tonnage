import os
import requests
from flask import Flask, request, jsonify, render_template
import pymongo

# Initialize Flask application
app = Flask(__name__)

# Connect to MongoDB
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
try:
    client = pymongo.MongoClient(mongo_uri)
    db = client["cargo_with_tonnage"]
    distance_result_collection = db["distance_result"]
    print("MongoDB connected successfully!")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")

@app.route("/")
def index():
    """Render the main page"""
    return render_template("index.html")


GOOGLE_MAPS_API_KEY = "AIzaSyBS4hLP9ST1uvT3vxT-vR_3bZJ-BXCUoQo"

@app.route("/maps-api", methods=["GET"])
def maps_api():
    # 获取前端传递的参数
    params = request.args.to_dict()
    params["key"] = GOOGLE_MAPS_API_KEY

    # 转发请求到 Google Maps API
    response = requests.get("https://maps.googleapis.com/maps/api/js", params=params)
    return response.content, response.status_code, response.headers.items()

@app.route("/query", methods=["GET"])
def query_distances():
    """Query distance data from the MongoDB collection with pagination and filtering"""
    # Get query parameters
    vessel_name = request.args.get("vessel_name")
    cargo_name = request.args.get("cargo_name")
    loading_port = request.args.get("loading_port")
    open_port = request.args.get("open_port")
    page = int(request.args.get("page", 1))  # Current page number, default is 1
    limit = int(request.args.get("limit", 20))  # Number of records per page, default is 20

    # Build query filter
    query_filter = {}
    if vessel_name:
        query_filter["vessel_name"] = {"$regex": vessel_name, "$options": "i"}
    if cargo_name:
        query_filter["cargo_name"] = {"$regex": cargo_name, "$options": "i"}
    if loading_port:
        query_filter["loading_port"] = {"$regex": loading_port, "$options": "i"}
    if open_port:
        query_filter["open_port"] = {"$regex": open_port, "$options": "i"}

    # Query database and paginate
    total_records = distance_result_collection.count_documents(query_filter)  # Total number of records
    results = list(distance_result_collection.find(query_filter, {
        "_id": 0,  # Exclude MongoDB ID field
        "vessel_name": 1,
        "cargo_name": 1,
        "loading_port": 1,
        "loading_country": 1,
        "open_port": 1,
        "open_country": 1,
        "open_date_format": 1,  # Read formatted open_date
        "lay_date_format": 1,  # Read formatted lay_date
        "canceling_date_format": 1,  # Read formatted canceling_date
        "dwcc": 1,
        "min_quantity": 1,
        "max_quantity": 1,
        "distance_km": 1,
        "distance_nm": 1,
        "loading_port_coordinates_geo": 1,  # Include loading port coordinates
        "open_port_coordinates_geo": 1  # Include open port coordinates
    }).skip((page - 1) * limit).limit(limit))  # Ensure skip and limit parameters are correct

    return jsonify({
        "total_records": total_records,
        "page": page,
        "limit": limit,
        "results": results
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
