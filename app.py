from flask import Flask, jsonify
from pymongo import MongoClient
import os

# Initialize Flask app
app = Flask(__name__)

# MongoDB connection setup
mongo_uri = os.getenv("MONGO_URI")  # MongoDB URI from environment variable
if not mongo_uri:
    raise Exception("MongoDB URI not set in environment variables.")

# Establish connection with MongoDB
client = MongoClient(mongo_uri)
db = client["icai-db"]  # Replace with your actual database name
collection = db["papers-data"]  # Replace with your actual collection name

# Route to get all data from the collection
@app.route("/get-data", methods=["GET"])
def get_data():
    try:
        # Fetch all documents from the collection
        data_cursor = collection.find({})
        data_list = list(data_cursor)
        
        # Check if data exists and return it
        if data_list:
            return jsonify(data_list), 200
        else:
            return jsonify({"error": "No data found"}), 404
    except Exception as e:
        # Handle database connection errors or other issues
        return jsonify({"error": str(e)}), 500

# Route to get data by playlist index
@app.route("/get-data/<int:playlist_index>", methods=["GET"])
def get_data_by_playlist(playlist_index):
    try:
        # Fetch data based on playlist index
        data_cursor = collection.find({"playlist_index": playlist_index})
        data_list = list(data_cursor)
        
        # Check if data exists for the given index
        if data_list:
            return jsonify(data_list), 200
        else:
            return jsonify({"error": f"No data found for playlist index {playlist_index}"}), 404
    except Exception as e:
        # Handle database connection errors or other issues
        return jsonify({"error": str(e)}), 500

# Main entry point for the Flask application
if __name__ == "__main__":
    # Render sets the port via environment variables, use 5000 as default
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
