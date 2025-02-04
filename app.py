import os
import requests
import sqlite3
import pandas as pd
from flask import Flask, render_template, request, send_file, redirect, url_for
from bs4 import BeautifulSoup
from flask_apscheduler import APScheduler
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urljoin

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

def get_selenium_driver():
    options = Options()
    options.add_argument("--headless")  
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def selenium_scrape(url):
    driver = get_selenium_driver()
    driver.get(url)
    html = driver.page_source
    driver.quit()
    return BeautifulSoup(html, "html.parser")

def scrape_website(url, data_type, keyword=None, download_images=False, download_videos=False):
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
    except requests.exceptions.RequestException:
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
        return []

    for element in elements:
        data = None

        if data_type == "Text":
            data = element.text.strip()
        elif data_type == "Links":
            data = element.get("href")
        elif data_type == "Images":
            img_url = urljoin(url, element.get("src"))
            data = img_url
        elif data_type == "Videos":
            video_url = urljoin(url, element.get("src"))
            data = video_url

        if data:
            if keyword and keyword.lower() in data.lower():
                extracted_data.append({"type": data_type, "content": data})
            elif not keyword:
                extracted_data.append({"type": data_type, "content": data})

    return extracted_data

@app.route("/", methods=["GET", "POST"])
def index():
    data = []
    error_message = None

    if request.method == "POST":
        try:
            url = request.form["url"]
            data_type = request.form["data_type"]
            keyword = request.form.get("keyword", "").strip()

            scraped_data = scrape_website(url, data_type, keyword)

            if not scraped_data:
                error_message = "No data found."

            data = scraped_data
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"

    return render_template("index.html", data=data, error_message=error_message)

if __name__ == "__main__":
    app.run(debug=True)
