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
# Replace <username>, <password>, and <cluster_name> with your actual Atlas cluster info
mongo_uri = os.getenv("MONGO_URI")  # MongoDB URI from environment variable

client = MongoClient(mongo_uri)

db = client["icai-db"]  # Database name
collection = db["papers-data"]  # Collection name

# Set the path to chromedriver.exe
chrome_driver_path = r"chromedriver"

# Set up Chrome options
chrome_options = ChromeOptions()
chrome_options.add_argument('--headless')  # Run Chrome in headless mode (no GUI)

# Set up Chrome service
chrome_service = ChromeService(executable_path=chrome_driver_path)

# Create a new instance of the Chrome webdriver
browser = webdriver.Chrome(service=chrome_service, options=chrome_options)

url_list = ['https://www.youtube.com/watch?v=YXD3AJNcX4o&list=PLP0oTm4FOBFKqJnztWgr5Ed6wdqEF_GU4',
            "https://www.youtube.com/watch?v=BvyMBlX4oZI&list=PLP0oTm4FOBFID7suAsk0kpwVgJUhIyT5g"
]

# Load the webpage
for index, url in enumerate(url_list):
    browser.get(url)

    # Wait for the page to load completely
    time.sleep(1)  # Adjust the sleep time if needed

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(browser.page_source, 'html.parser')

    # List to store the extracted video data
    playlist_data = []

    # Select all video renderer elements using BeautifulSoup
    video_renderers = soup.find_all('ytd-playlist-panel-video-renderer')

    # Variable to keep track of total sessions
    total_sessions = 0

    # Loop through each video and extract data
    for video_renderer in video_renderers:
        # Extract full text content
        full_text = video_renderer.get_text()

        # Assuming the text follows a consistent pattern, split the text by lines
        parts = full_text.strip().split('\n')
        parts = [part.strip() for part in parts if part.strip()]  # Remove empty lines

        try:
            # Paper name and topic are usually on the same line, separated by '|'
            paper_and_topic = parts[4].split('|')  # Adjusted to match data structure
            paper_name = paper_and_topic[0].strip() if len(paper_and_topic) > 0 else "No Paper Name"
            topic_name = paper_and_topic[1].strip() if len(paper_and_topic) > 1 else "No Topic"

            # Extract session and duration from fixed positions
            duration = parts[1] if len(parts) > 1 else "No Duration"
            session = parts[4].split('|')[2].strip() if 'Session' in parts[4] else "No Session"

            # Increment session count if session is found
            if session != "No Session":
                total_sessions += 1

            # Extract the video URL (href attribute of the link inside the element)
            video_url = video_renderer.find('a', id='wc-endpoint')
            full_url = f"https://www.youtube.com{video_url['href']}" if video_url else "No URL"

            # Extract upcoming/completed status
            upcoming_status = video_renderer.find('span', string='UPCOMING')

            # Collect the data
            video_data = {
                "paper_name": paper_name,
                "topic_name": topic_name,
                "session": session,
                "duration": duration,
                "url": full_url,
                "status": "UPCOMING" if upcoming_status else "completed"
            }

        except (IndexError, AttributeError) as e:
            video_data = {
                "error": f"Data format doesn't match expected structure: {str(e)}",
                "raw_parts": parts  # Log raw parts for debugging purposes
            }

        # Append to the list
        playlist_data.append(video_data)

    # Add the total sessions count to the final data
    playlist_summary = {
        "total_sessions": total_sessions,
        "videos": playlist_data
    }

    # Insert the extracted data into MongoDB
    collection.insert_one({
        "playlist_index": index,
        "data": playlist_summary
    })

    print(f"Data extracted and saved to MongoDB for playlist {index}.")

# Close the browser
browser.quit()
