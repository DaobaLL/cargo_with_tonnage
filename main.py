from read_distance_result import app, distance_result_collection
from flask import Flask, jsonify, request, render_template

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
