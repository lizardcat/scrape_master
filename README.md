# ScrapeMaster 🕷️

**Enterprise-grade web scraping platform** with multi-site scheduling, data cleaning pipeline, and real-time analytics dashboard. Built with Flask, React, and Chart.js.

## **🔹 Features**

### Core Scraping
✅ **Multi-Data Type Extraction** - Text, links, images, and videos
✅ **Selenium Fallback** - Automatic fallback for JavaScript-heavy sites
✅ **URL Normalization** - Handles relative URLs automatically
✅ **Keyword Filtering** - Filter results by keywords
✅ **Media Downloads** - Download images and videos locally

### Data Management
✅ **Data Cleaning Pipeline** - Automated data cleaning and validation
✅ **Duplicate Removal** - Smart deduplication with configurable options
✅ **Text Processing** - HTML decoding, whitespace normalization, and more
✅ **URL Cleaning** - Parameter removal, fragment handling, normalization
✅ **Dual Database Support** - SQLite (default) or PostgreSQL

### Job Scheduling
✅ **Multi-Site Jobs** - Manage multiple scraping targets
✅ **Flexible Scheduling** - Hourly, daily, weekly, or manual execution
✅ **Job Management UI** - Create, edit, activate/deactivate jobs
✅ **Automatic Execution** - Background task processing
✅ **Run History** - Track last run times and execution stats

### Analytics & Visualization
✅ **React Dashboard** - Modern, responsive analytics interface
✅ **Real-time Charts** - Chart.js powered visualizations
✅ **Performance Metrics** - Success rates, execution times, item counts
✅ **Activity Trends** - 7-day activity graphs
✅ **Top Sites Tracking** - Most frequently scraped domains
✅ **Data Distribution** - Data type breakdown charts

### System Features
✅ **REST API** - JSON endpoints for all data
✅ **Error Handling & Logging** - Comprehensive error tracking
✅ **Storage Management** - Automatic cleanup of old files
✅ **Flash Messages** - User-friendly feedback
✅ **Material Design UI** - Dark theme interface

---

## **📋 Requirements**

- Python 3.8+
- Chrome/Chromium browser (for Selenium)
- Optional: PostgreSQL 12+ (for production)

---

## **🚀 Installation**

### 1. Clone the repository
```bash
git clone <repository-url>
cd scrape_master
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Optional: Configure PostgreSQL
```bash
# Edit .env or set environment variables
export DB_TYPE=postgres
export PG_HOST=localhost
export PG_PORT=5432
export PG_USER=postgres
export PG_PASSWORD=your_password
export PG_DATABASE=scrapemaster
```

### 4. Run the application
```bash
python app.py
```

### 5. Open your browser
Navigate to `http://localhost:5000`

---

## **💻 Usage**

### Quick Start (One-time Scraping)
1. Go to **Home** page
2. Enter website URL
3. Select data type to extract
4. Click **Start Scraping**
5. Download results as CSV

### Creating Scheduled Jobs
1. Navigate to **Jobs** page
2. Click **Create New Job**
3. Configure job settings:
   - **Name**: Descriptive job name
   - **URL**: Target website
   - **Data Type**: What to extract
   - **Schedule**: Manual, Hourly, Daily, or Weekly
4. Click **Create Job**

### Managing Jobs
- **View**: See job details and run history
- **Run Now**: Execute job manually
- **Activate/Deactivate**: Enable/disable automatic execution
- **Delete**: Remove job and its data

### Viewing Analytics
1. Go to **Dashboard** page
2. View key metrics:
   - Total and active jobs
   - Items scraped
   - Success rates
   - Average execution time
3. Analyze charts:
   - Data type distribution
   - Recent activity trends
   - Top scraped sites

---

## **🔧 Configuration**

### Environment Variables

```bash
# Application
SECRET_KEY=your-secret-key-here

# Database (SQLite by default)
DB_TYPE=sqlite  # or 'postgres'
DB_NAME=scraper.db

# PostgreSQL (if using)
PG_HOST=localhost
PG_PORT=5432
PG_USER=postgres
PG_PASSWORD=password
PG_DATABASE=scrapemaster

# Storage
MAX_STORAGE_SIZE=524288000  # 500MB in bytes
```

### Data Cleaning Options

The data cleaning pipeline supports:

**Text Cleaning:**
- Strip whitespace
- Decode HTML entities
- Remove newlines
- Convert to lowercase
- Remove punctuation/numbers
- Remove URLs from text

**URL Cleaning:**
- Remove query parameters
- Remove fragments
- Lowercase normalization
- Trailing slash removal

**Filtering:**
- Length constraints (min/max)
- Regex pattern matching
- Duplicate removal (case-sensitive/insensitive)

### Scheduling Options

**Hourly**: Run every N hours
```python
schedule_type = "hourly"
schedule_value = "6"  # Every 6 hours
```

**Daily**: Run at specific time
```python
schedule_type = "daily"
schedule_value = "14:30"  # 2:30 PM daily
```

**Weekly**: Run on specific day
```python
schedule_type = "weekly"
schedule_value = "mon"  # Every Monday
```

---

## **📁 Project Structure**

```
scrape_master/
├── app.py                    # Main Flask application with routes
├── database.py               # Database management (SQLite/PostgreSQL)
├── data_cleaning.py          # Data cleaning pipeline
├── requirements.txt          # Python dependencies
├── scraper.db               # SQLite database (auto-created)
├── scraper.log              # Application logs
├── .env                     # Environment variables (create this)
├── data/
│   └── scraped_data.csv     # Latest CSV export
├── static/
│   ├── style.css            # UI styling
│   ├── images/              # Downloaded images
│   └── videos/              # Downloaded videos
└── templates/
    ├── index.html           # Home/quick scrape page
    ├── jobs.html            # Jobs list page
    ├── create_job.html      # Create job form
    ├── view_job.html        # Job details page
    └── dashboard.html       # Analytics dashboard (React)
```

---

## **🔌 API Endpoints**

### Get Dashboard Statistics
```
GET /api/stats
```
Returns: Total jobs, active jobs, items scraped, success rate, etc.

### Get All Jobs
```
GET /api/jobs
```
Returns: List of all scraping jobs

### Get Job Details
```
GET /api/jobs/<job_id>
```
Returns: Specific job configuration and metadata

---

## **🐛 Troubleshooting**

### Selenium/ChromeDriver Issues
- Ensure Chrome/Chromium is installed
- ChromeDriver auto-installs via webdriver-manager
- Check logs: `tail -f scraper.log`

### Database Errors
- SQLite: Check file permissions for `scraper.db`
- PostgreSQL: Verify connection settings in environment variables

### Scheduling Not Working
- Check logs for scheduler errors
- Ensure jobs are marked as "Active"
- Verify schedule_type and schedule_value are valid

### Import Errors
```bash
pip install -r requirements.txt --upgrade
```

### Dashboard Not Loading
- Check browser console for JavaScript errors
- Verify `/api/stats` endpoint returns data
- Ensure React and Chart.js CDNs are accessible

---

## **🚀 Advanced Usage**

### Custom Data Cleaning Pipeline

```python
from data_cleaning import DataCleaningPipeline

pipeline = DataCleaningPipeline()
pipeline.add_step('clean_text', {
    'strip_whitespace': True,
    'lowercase': True,
    'remove_urls': True
})
pipeline.add_step('filter_by_length', {
    'min_length': 10,
    'max_length': 500
})
pipeline.add_step('remove_duplicates', {
    'case_sensitive': False
})

cleaned_data = pipeline.clean(raw_data, 'Text')
```

### Programmatic Job Creation

```python
import database as db

job_id = db.create_scraping_job(
    name="Daily News Scraper",
    url="https://news.example.com",
    data_type="Text",
    keyword="technology",
    schedule_type="daily",
    schedule_value="09:00"
)
```

### Export Data Programmatically

```python
import pandas as pd
from database import get_connection

conn = get_connection()
df = pd.read_sql_query("SELECT * FROM results", conn)
df.to_excel("export.xlsx", index=False)
conn.close()
```

---

## **📊 Database Schema**

### scraping_jobs
- id, name, url, data_type
- keyword, download_images, download_videos
- schedule_type, schedule_value
- is_active, last_run, next_run
- created_at, updated_at

### results
- id, job_id, url, data_type
- extracted_data, cleaned_data, metadata
- created_at

### scraping_stats
- id, job_id, url, data_type
- items_scraped, items_cleaned
- success, error_message, execution_time
- created_at

---

## **⚠️ Legal Notice**

Always respect:
- Website terms of service
- robots.txt files
- Rate limiting and polite scraping practices
- Copyright and data usage rights

This tool is for educational and authorized use only.

---

## **🤝 Contributing**

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

---

## **📝 License**

Educational and personal use only. See LICENSE file for details.

---

## **🆘 Support**

- Issues: Create an issue on GitHub
- Documentation: Check this README and inline code comments
- Logs: Review `scraper.log` for detailed error information

---

**Built with ❤️ using Flask, Selenium, React, and Chart.js**
