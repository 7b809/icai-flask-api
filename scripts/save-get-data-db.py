import re
import json
import time
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from pymongo import MongoClient

# MongoDB Atlas connection setup
mongo_uri = os.getenv("MONGO_URI")  # MongoDB URI from environment variable

client = MongoClient(mongo_uri)
db = client["icai-db"]  # Database name
original_collection = db["papers-data"]  # Original collection
temp_collection = db["papers-data-temp"]  # Temporary collection

# Step 1: Copy data from original to temp collection before deletion
if temp_collection.count_documents({}) > 0:
    temp_collection.drop()  # Clear temp collection if it exists

# Copy data from original collection to temp collection
for doc in original_collection.find():
    temp_collection.insert_one(doc)

# Clear original collection after copying
original_collection.delete_many({})

# Set up Chrome options and path to chromedriver
chrome_driver_path = r"chromedriver"  # Path to chromedriver executable
chrome_options = ChromeOptions()
chrome_options.add_argument('--headless')  # Run Chrome in headless mode

# Set up Chrome service
chrome_service = ChromeService(executable_path=chrome_driver_path)

# Create a new instance of the Chrome webdriver
browser = webdriver.Chrome(service=chrome_service, options=chrome_options)

# List of YouTube playlist URLs
url_list = [
    'https://www.youtube.com/watch?v=YXD3AJNcX4o&list=PLP0oTm4FOBFKqJnztWgr5Ed6wdqEF_GU4',
    'https://www.youtube.com/watch?v=BvyMBlX4oZI&list=PLP0oTm4FOBFID7suAsk0kpwVgJUhIyT5g'
]

# Load each webpage and extract data
for index, url in enumerate(url_list):
    browser.get(url)
    time.sleep(2)  # Wait for the page to load completely

    soup = BeautifulSoup(browser.page_source, 'html.parser')

    # Dictionary to store videos grouped by paper_name
    videos_by_paper = {}
    video_renderers = soup.find_all('ytd-playlist-panel-video-renderer')

    total_sessions = 0

    for video_renderer in video_renderers:
        # Extract full text content
        full_text = video_renderer.get_text().strip().split('\n')
        parts = [part.strip() for part in full_text if part.strip()]

        try:
            # Store the entire original title
            original_titles = parts[4] if len(parts) > 4 else "No Title"

            # Split the title for further subdivision
            paper_and_topic = original_titles.split('|')
            paper_name = paper_and_topic[0].strip() if len(paper_and_topic) > 0 else "No Paper Name"
            topic_name = paper_and_topic[1].strip() if len(paper_and_topic) > 1 else "No Topic"
            session = paper_and_topic[2].strip() if len(paper_and_topic) > 2 and 'Session' in paper_and_topic[2] else "No Session"

            duration = parts[1] if len(parts) > 1 else "No Duration"

            if session != "No Session":
                total_sessions += 1

            video_url = video_renderer.find('a', id='wc-endpoint')
            full_url = f"https://www.youtube.com{video_url['href']}" if video_url else "No URL"
            upcoming_status = video_renderer.find('span', string='UPCOMING')

            video_data = {
                "original_titles": original_titles,  # Add original title to the video data
                "paper_name": paper_name,
                "topic_name": topic_name,
                "session": session,
                "duration": duration,
                "url": full_url,
                "status": "UPCOMING" if upcoming_status else "completed"
            }

            # Group videos by paper_name
            if paper_name not in videos_by_paper:
                videos_by_paper[paper_name] = []  # Create new list for each paper_name

            videos_by_paper[paper_name].append(video_data)

        except (IndexError, AttributeError) as e:
            video_data = {
                "error": f"Data format doesn't match expected structure: {str(e)}",
                "raw_parts": parts
            }

            # Add to a special group for ungrouped or errored items
            if "Ungrouped" not in videos_by_paper:
                videos_by_paper["Ungrouped"] = []
            videos_by_paper["Ungrouped"].append(video_data)

    playlist_summary = {
        "playlist_links": url_list,  # Correct the reference for playlist links
        "total_sessions": total_sessions,
        "videos": videos_by_paper  # Save grouped videos by paper_name
    }

    # Insert the extracted data into the original MongoDB collection
    original_collection.insert_one({
        "playlist_index": index,
        "data": playlist_summary
    })

    print(f"Data extracted and saved to MongoDB for playlist {index}.")

# Close the browser after processing
browser.quit()

print("All playlists processed and saved.")
