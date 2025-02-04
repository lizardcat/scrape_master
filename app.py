import os
import requests
import sqlite3
import pandas as pd
from flask import Flask, render_template, request, send_file
from bs4 import BeautifulSoup
from flask_apscheduler import APScheduler
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)

# Ensure required directories exist
for directory in ["data", "static/images", "static/videos"]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Flask-APScheduler configuration
class Config:
    SCHEDULER_API_ENABLED = True

app.config.from_object(Config)
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

# Set maximum storage size (500MB per media type)
MAX_STORAGE_SIZE = 500 * 1024 * 1024  # 500MB

# Function to calculate total folder size
def get_folder_size(folder_path):
    total_size = sum(
        os.path.getsize(os.path.join(folder_path, f)) for f in os.listdir(folder_path)
    ) if os.path.exists(folder_path) else 0
    return total_size

# Function to clean up oldest files if storage exceeds limit
def clean_storage(folder_path):
    while get_folder_size(folder_path) > MAX_STORAGE_SIZE:
        files = sorted(
            [os.path.join(folder_path, f) for f in os.listdir(folder_path)],
            key=os.path.getctime  # Sort by creation time (oldest first)
        )
        if files:
            os.remove(files[0])  # Delete the oldest file

# Set up Selenium WebDriver
def get_selenium_driver():
    options = Options()
    options.add_argument("--headless")  # Run in headless mode (no GUI)
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

# Function to scrape website using Selenium (for blocked sites)
def selenium_scrape(url):
    driver = get_selenium_driver()
    driver.get(url)
    html = driver.page_source
    driver.quit()
    return BeautifulSoup(html, "html.parser")

# Function to scrape website
def scrape_website(url, data_type, keyword=None, download_images=False, download_videos=False):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
    except requests.exceptions.RequestException:
        # If blocked, switch to Selenium
        soup = selenium_scrape(url)

    extracted_data = []

    if data_type == "Text":
        elements = soup.find_all("p")
    elif data_type == "Links":
        elements = soup.find_all("a", href=True)
    elif data_type == "Images":
        elements = soup.find_all("img", src=True)
    elif data_type == "Videos":
        elements = soup.find_all(["video", "iframe"])
    else:
        return ["Invalid Data Type"]

    for element in elements:
        data = None
        if data_type == "Text":
            data = element.text.strip()
        elif data_type == "Links":
            data = element.get("href")
        elif data_type == "Images":
            data = element.get("src")
            if download_images:
                local_path = download_image(data)
                data = local_path if local_path else data
        elif data_type == "Videos":
            if element.name == "video":
                data = element.get("src")
                if download_videos:
                    local_path = download_video(data)
                    data = local_path if local_path else data
            elif element.name == "iframe":
                data = element.get("src")  # Embedded YouTube videos

        if data:
            if keyword and keyword.lower() in data.lower():
                extracted_data.append(data)
            elif not keyword:
                extracted_data.append(data)

    # Save results to CSV
    df = pd.DataFrame(extracted_data, columns=["Extracted Data"])
    csv_path = "data/scraped_data.csv"
    df.to_csv(csv_path, index=False)

    # Save results to database
    save_to_db(url, data_type, extracted_data)

    return [{"type": data_type, "content": item} for item in extracted_data]

# Function to save scraped data to database
def save_to_db(url, data_type, extracted_data):
    conn = sqlite3.connect("scraper.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT,
            data_type TEXT,
            extracted_data TEXT
        )
    """)
    for data in extracted_data:
        cursor.execute("INSERT INTO results (url, data_type, extracted_data) VALUES (?, ?, ?)",
                       (url, data_type, data))
    conn.commit()
    conn.close()

# Homepage with form & inline results display
@app.route("/", methods=["GET", "POST"])
def index():
    data = []
    keyword = ""  # ✅ Ensure keyword is always defined

    if request.method == "POST":
        url = request.form["url"]
        data_type = request.form["data_type"]
        keyword = request.form.get("keyword", "").strip()  # ✅ Safe to use now
        download_images = "download_images" in request.form
        download_videos = "download_videos" in request.form

        scraped_data = scrape_website(url, data_type, keyword, download_images, download_videos)
        data = scraped_data  # ✅ Pass scraped data to the template

    return render_template("index.html", data=data, keyword=keyword)

# Route to download CSV file
@app.route("/download")
def download_csv():
    csv_path = "data/scraped_data.csv"
    if os.path.exists(csv_path):
        return send_file(csv_path, as_attachment=True)
    return "No data available", 404

# Route to clear all scraped data
@app.route("/clear_data")
def clear_data():
    conn = sqlite3.connect("scraper.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM results")  # Delete all records
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# Scheduled scraping task (runs every hour)
@scheduler.task("interval", id="scheduled_scrape", hours=1)
def scheduled_scrape():
    scrape_website("https://example.com", "Text")

# Scheduled cleanup task (runs every hour)
@scheduler.task("interval", id="storage_cleanup", hours=1)
def scheduled_cleanup():
    clean_storage("static/images")
    clean_storage("static/videos")

if __name__ == "__main__":
    app.run(debug=True)
