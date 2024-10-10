from flask import Flask, jsonify
from pymongo import MongoClient
import os

app = Flask(__name__)

# MongoDB connection setup
mongo_uri = os.getenv("MONGO_URI")  # MongoDB URI from environment variable
client = MongoClient(mongo_uri)
db = client["icai-db"]  # Replace with your actual database name
collection = db["papers-data"]  # Replace with your actual collection name

@app.route("/get-data", methods=["GET"])
def get_data():
    data_cursor = collection.find({})
    data_list = list(data_cursor)
    if data_list:
        return jsonify(data_list), 200
    else:
        return jsonify({"error": "No data found"}), 404

@app.route("/get-data/<int:playlist_index>", methods=["GET"])
def get_data_by_playlist(playlist_index):
    data_cursor = collection.find({"playlist_index": playlist_index})
    data_list = list(data_cursor)
    if data_list:
        return jsonify(data_list), 200
    else:
        return jsonify({"error": f"No data found for playlist index {playlist_index}"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
