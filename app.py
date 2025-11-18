import os
import requests
import sqlite3
import pandas as pd
import logging
import hashlib
from datetime import datetime
from urllib.parse import urljoin, urlparse
from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from bs4 import BeautifulSoup
from flask_apscheduler import APScheduler
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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
    """Calculate total size of files in a folder (excludes subdirectories)"""
    if not os.path.exists(folder_path):
        return 0

    total_size = 0
    try:
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isfile(item_path):
                total_size += os.path.getsize(item_path)
    except Exception as e:
        logger.error(f"Error calculating folder size for {folder_path}: {e}")

    return total_size

# Function to clean up oldest files if storage exceeds limit
def clean_storage(folder_path):
    """Remove oldest files when storage limit is exceeded"""
    if not os.path.exists(folder_path):
        return

    try:
        while get_folder_size(folder_path) > MAX_STORAGE_SIZE:
            files = [
                os.path.join(folder_path, f)
                for f in os.listdir(folder_path)
                if os.path.isfile(os.path.join(folder_path, f))
            ]

            if not files:
                break

            files.sort(key=os.path.getctime)
            oldest_file = files[0]

            try:
                os.remove(oldest_file)
                logger.info(f"Removed old file: {oldest_file}")
            except Exception as e:
                logger.error(f"Error removing file {oldest_file}: {e}")
                break
    except Exception as e:
        logger.error(f"Error during storage cleanup for {folder_path}: {e}")

# Function to validate URL
def validate_url(url):
    """Validate URL format and scheme"""
    try:
        result = urlparse(url)
        # Only allow http and https schemes
        if result.scheme not in ['http', 'https']:
            return False
        if not result.netloc:
            return False
        return True
    except Exception:
        return False

# Function to normalize URL (handle relative URLs)
def normalize_url(url, base_url):
    """Convert relative URLs to absolute URLs"""
    if not url:
        return None

    # Skip data URLs and javascript
    if url.startswith(('data:', 'javascript:', 'mailto:')):
        return None

    try:
        return urljoin(base_url, url)
    except Exception as e:
        logger.error(f"Error normalizing URL {url}: {e}")
        return None

# Function to download an image
def download_image(img_url, base_url=None):
    """Download an image and save it locally"""
    if not img_url:
        return None

    # Normalize the URL
    if base_url:
        img_url = normalize_url(img_url, base_url)

    if not img_url or not validate_url(img_url):
        logger.warning(f"Invalid image URL: {img_url}")
        return None

    try:
        # Create a unique filename using URL hash
        url_hash = hashlib.md5(img_url.encode()).hexdigest()
        ext = os.path.splitext(urlparse(img_url).path)[1] or '.jpg'
        filename = f"{url_hash}{ext}"
        filepath = os.path.join("static/images", filename)

        # Check if already downloaded
        if os.path.exists(filepath):
            logger.info(f"Image already exists: {filename}")
            return f"/static/images/{filename}"

        # Download the image
        response = requests.get(img_url, timeout=10, stream=True)
        response.raise_for_status()

        # Check content type
        content_type = response.headers.get('content-type', '')
        if 'image' not in content_type:
            logger.warning(f"URL does not point to an image: {img_url}")
            return None

        # Save the image
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.info(f"Downloaded image: {filename}")

        # Clean storage if needed
        clean_storage("static/images")

        return f"/static/images/{filename}"

    except Exception as e:
        logger.error(f"Error downloading image {img_url}: {e}")
        return None

# Function to download a video
def download_video(video_url, base_url=None):
    """Download a video and save it locally"""
    if not video_url:
        return None

    # Normalize the URL
    if base_url:
        video_url = normalize_url(video_url, base_url)

    if not video_url or not validate_url(video_url):
        logger.warning(f"Invalid video URL: {video_url}")
        return None

    # Skip embedded videos (YouTube, Vimeo, etc.)
    if any(domain in video_url for domain in ['youtube.com', 'youtu.be', 'vimeo.com']):
        logger.info(f"Skipping embedded video: {video_url}")
        return video_url

    try:
        # Create a unique filename using URL hash
        url_hash = hashlib.md5(video_url.encode()).hexdigest()
        ext = os.path.splitext(urlparse(video_url).path)[1] or '.mp4'
        filename = f"{url_hash}{ext}"
        filepath = os.path.join("static/videos", filename)

        # Check if already downloaded
        if os.path.exists(filepath):
            logger.info(f"Video already exists: {filename}")
            return f"/static/videos/{filename}"

        # Download the video
        response = requests.get(video_url, timeout=30, stream=True)
        response.raise_for_status()

        # Check content type
        content_type = response.headers.get('content-type', '')
        if 'video' not in content_type:
            logger.warning(f"URL does not point to a video: {video_url}")
            return None

        # Save the video
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.info(f"Downloaded video: {filename}")

        # Clean storage if needed
        clean_storage("static/videos")

        return f"/static/videos/{filename}"

    except Exception as e:
        logger.error(f"Error downloading video {video_url}: {e}")
        return None

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
    """Scrape website using Selenium for JavaScript-heavy or blocking sites"""
    driver = None
    try:
        driver = get_selenium_driver()
        driver.get(url)
        html = driver.page_source
        return BeautifulSoup(html, "html.parser")
    except Exception as e:
        logger.error(f"Error in Selenium scraping for {url}: {e}")
        raise
    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logger.error(f"Error closing Selenium driver: {e}")

# Function to scrape website
def scrape_website(url, data_type, keyword=None, download_images=False, download_videos=False):
    """Main scraping function with fallback to Selenium"""

    # Validate URL
    if not validate_url(url):
        logger.error(f"Invalid URL: {url}")
        return [{"type": "error", "content": f"Invalid URL: {url}"}]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    soup = None
    try:
        logger.info(f"Attempting to scrape {url} for {data_type}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
    except requests.exceptions.RequestException as e:
        # If blocked or error, switch to Selenium
        logger.warning(f"Requests failed for {url}, trying Selenium: {e}")
        try:
            soup = selenium_scrape(url)
        except Exception as selenium_error:
            logger.error(f"Selenium scraping also failed for {url}: {selenium_error}")
            return [{"type": "error", "content": f"Failed to scrape website: {str(selenium_error)}"}]

    if not soup:
        return [{"type": "error", "content": "Failed to parse website"}]

    extracted_data = []

    # Select elements based on data type
    if data_type == "Text":
        elements = soup.find_all("p")
    elif data_type == "Links":
        elements = soup.find_all("a", href=True)
    elif data_type == "Images":
        elements = soup.find_all("img", src=True)
    elif data_type == "Videos":
        elements = soup.find_all(["video", "iframe"])
    else:
        return [{"type": "error", "content": "Invalid Data Type"}]

    logger.info(f"Found {len(elements)} elements of type {data_type}")

    # Extract data from elements
    for element in elements:
        data = None

        if data_type == "Text":
            data = element.text.strip()
            if not data:  # Skip empty text
                continue

        elif data_type == "Links":
            href = element.get("href")
            data = normalize_url(href, url)
            if not data:
                continue

        elif data_type == "Images":
            src = element.get("src")
            if download_images:
                local_path = download_image(src, url)
                data = local_path if local_path else normalize_url(src, url)
            else:
                data = normalize_url(src, url)

        elif data_type == "Videos":
            if element.name == "video":
                src = element.get("src")
                if download_videos:
                    local_path = download_video(src, url)
                    data = local_path if local_path else normalize_url(src, url)
                else:
                    data = normalize_url(src, url)
            elif element.name == "iframe":
                data = element.get("src")  # Embedded YouTube videos
                data = normalize_url(data, url) if data else None

        # Apply keyword filter
        if data:
            if keyword and keyword.lower() in str(data).lower():
                extracted_data.append(data)
            elif not keyword:
                extracted_data.append(data)

    logger.info(f"Extracted {len(extracted_data)} items after filtering")

    # Remove duplicates while preserving order
    seen = set()
    unique_data = []
    for item in extracted_data:
        if item not in seen:
            seen.add(item)
            unique_data.append(item)

    # Save results to CSV
    try:
        df = pd.DataFrame(unique_data, columns=["Extracted Data"])
        csv_path = "data/scraped_data.csv"
        df.to_csv(csv_path, index=False)
        logger.info(f"Saved {len(unique_data)} items to CSV")
    except Exception as e:
        logger.error(f"Error saving CSV: {e}")

    # Save results to database
    try:
        save_to_db(url, data_type, unique_data)
    except Exception as e:
        logger.error(f"Error saving to database: {e}")

    return [{"type": data_type, "content": item} for item in unique_data]

# Function to save scraped data to database
def save_to_db(url, data_type, extracted_data):
    """Save scraped data to SQLite database with timestamps"""
    conn = None
    try:
        conn = sqlite3.connect("scraper.db")
        cursor = conn.cursor()

        # Create table with timestamp field
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                data_type TEXT NOT NULL,
                extracted_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Insert data with timestamp
        timestamp = datetime.now().isoformat()
        for data in extracted_data:
            cursor.execute(
                "INSERT INTO results (url, data_type, extracted_data, created_at) VALUES (?, ?, ?, ?)",
                (url, data_type, str(data), timestamp)
            )

        conn.commit()
        logger.info(f"Saved {len(extracted_data)} records to database")

    except Exception as e:
        logger.error(f"Database error: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

# Homepage with form & inline results display
@app.route("/", methods=["GET", "POST"])
def index():
    """Main route for scraping interface"""
    data = []
    keyword = ""

    if request.method == "POST":
        try:
            url = request.form.get("url", "").strip()
            data_type = request.form.get("data_type", "Text")
            keyword = request.form.get("keyword", "").strip()
            download_images = "download_images" in request.form
            download_videos = "download_videos" in request.form

            if not url:
                flash("Please enter a URL", "error")
                return render_template("index.html", data=data, keyword=keyword)

            logger.info(f"Scraping request - URL: {url}, Type: {data_type}, Keyword: {keyword}")

            scraped_data = scrape_website(url, data_type, keyword, download_images, download_videos)
            data = scraped_data

            if data and len(data) > 0:
                if data[0].get("type") == "error":
                    flash(data[0].get("content"), "error")
                else:
                    flash(f"Successfully scraped {len(data)} items!", "success")
            else:
                flash("No data found matching your criteria", "warning")

        except Exception as e:
            logger.error(f"Error in index route: {e}")
            flash(f"An error occurred: {str(e)}", "error")

    return render_template("index.html", data=data, keyword=keyword)

# Route to download CSV file
@app.route("/download")
def download_csv():
    """Download scraped data as CSV"""
    csv_path = "data/scraped_data.csv"
    try:
        if os.path.exists(csv_path):
            return send_file(csv_path, as_attachment=True, download_name="scraped_data.csv")
        else:
            flash("No data available to download", "warning")
            return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error downloading CSV: {e}")
        flash(f"Error downloading file: {str(e)}", "error")
        return redirect(url_for('index'))

# Route to clear all scraped data
@app.route("/clear_data")
def clear_data():
    """Clear all scraped data from database"""
    conn = None
    try:
        conn = sqlite3.connect("scraper.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM results")
        conn.commit()
        logger.info("Cleared all data from database")
        flash("All scraped data has been cleared", "success")
    except Exception as e:
        logger.error(f"Error clearing data: {e}")
        flash(f"Error clearing data: {str(e)}", "error")
    finally:
        if conn:
            conn.close()

    return redirect(url_for('index'))

# Scheduled scraping task (runs every hour)
# NOTE: Disabled by default. Uncomment and configure URL to enable
# @scheduler.task("interval", id="scheduled_scrape", hours=1)
# def scheduled_scrape():
#     """Automatically scrape a website on schedule"""
#     try:
#         logger.info("Running scheduled scrape task")
#         scrape_website("https://example.com", "Text")
#     except Exception as e:
#         logger.error(f"Scheduled scrape failed: {e}")

# Scheduled cleanup task (runs every hour)
@scheduler.task("interval", id="storage_cleanup", hours=1)
def scheduled_cleanup():
    """Automatically clean up old media files"""
    try:
        logger.info("Running scheduled cleanup task")
        clean_storage("static/images")
        clean_storage("static/videos")
    except Exception as e:
        logger.error(f"Scheduled cleanup failed: {e}")

if __name__ == "__main__":
    app.run(debug=True)
