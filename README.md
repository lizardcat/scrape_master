# ScrapeMaster 🕷️

ScrapeMaster is a **web scraping tool** built using **Flask and Selenium** that allows users to extract **text, links, images, and videos** from websites. It includes an intuitive web UI, supports scheduled scraping, and enables downloading scraped content.

## **🔹 Features**
✅ **Extracts Text, Links, Images, and Videos** from any website
✅ **Uses Selenium** to scrape JavaScript-heavy sites with automatic fallback
✅ **Scheduled Storage Cleanup** to manage disk space
✅ **Download Images & Videos** with deduplication
✅ **SQLite Database Storage** for organizing scraped results with timestamps
✅ **Keyword Filtering** to find relevant data
✅ **Material Design Dark UI** for a modern look
✅ **Error Handling & Logging** for debugging
✅ **URL Normalization** for handling relative URLs

---

## **📋 Requirements**

- Python 3.8+
- Chrome/Chromium browser (for Selenium)

---

## **🚀 Installation**

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd scrape_master
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```

4. **Open your browser:**
   Navigate to `http://localhost:5000`

---

## **💻 Usage**

1. **Enter a website URL** (e.g., `https://example.com`)
2. **Select data type** to extract:
   - Text (all paragraph content)
   - Links (all hyperlinks)
   - Images (all image URLs)
   - Videos (video elements and embedded content)
3. **Optional: Add a keyword** to filter results
4. **Optional: Enable downloads** for images/videos
5. Click **Start Scraping**
6. **Download CSV** of results when complete

---

## **🔧 Configuration**

### Storage Limits
Edit `MAX_STORAGE_SIZE` in `app.py` to change storage limits (default: 500MB per media type)

### Scheduled Scraping
Uncomment the `scheduled_scrape` function in `app.py` and configure the URL to enable automatic scraping

### Secret Key
Set the `SECRET_KEY` environment variable for production:
```bash
export SECRET_KEY="your-secure-random-key"
```

---

## **📁 Project Structure**

```
scrape_master/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── scraper.db            # SQLite database
├── scraper.log           # Application logs
├── data/                 # CSV export storage
├── static/
│   ├── style.css         # UI styling
│   ├── images/           # Downloaded images
│   └── videos/           # Downloaded videos
└── templates/
    └── index.html        # Main UI template
```

---

## **🐛 Troubleshooting**

**Selenium/ChromeDriver issues:**
- Make sure Chrome/Chromium is installed
- ChromeDriver is auto-installed via webdriver-manager

**Permission errors:**
- Ensure write permissions for `data/`, `static/images/`, `static/videos/`

**Import errors:**
- Run `pip install -r requirements.txt` again

**Check logs:**
- View `scraper.log` for detailed error information

---

## **⚠️ Legal Notice**

Always respect website terms of service and robots.txt. Use responsibly and ethically. This tool is for educational purposes.

---