"""
Database module for ScrapeMaster
Supports both SQLite and PostgreSQL
"""
import os
import sqlite3
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# Database configuration
DB_TYPE = os.environ.get('DB_TYPE', 'sqlite')  # 'sqlite' or 'postgres'
DB_NAME = os.environ.get('DB_NAME', 'scraper.db')

# PostgreSQL configuration (if using postgres)
PG_HOST = os.environ.get('PG_HOST', 'localhost')
PG_PORT = os.environ.get('PG_PORT', '5432')
PG_USER = os.environ.get('PG_USER', 'postgres')
PG_PASSWORD = os.environ.get('PG_PASSWORD', '')
PG_DATABASE = os.environ.get('PG_DATABASE', 'scrapemaster')


def get_connection():
    """Get database connection based on configuration"""
    if DB_TYPE == 'postgres':
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=PG_HOST,
                port=PG_PORT,
                user=PG_USER,
                password=PG_PASSWORD,
                database=PG_DATABASE
            )
            return conn
        except ImportError:
            logger.error("psycopg2 not installed. Falling back to SQLite.")
            return sqlite3.connect(DB_NAME)
        except Exception as e:
            logger.error(f"Error connecting to PostgreSQL: {e}. Falling back to SQLite.")
            return sqlite3.connect(DB_NAME)
    else:
        return sqlite3.connect(DB_NAME)


def init_database():
    """Initialize database schema"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Scraping jobs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scraping_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                data_type TEXT NOT NULL,
                keyword TEXT,
                download_images INTEGER DEFAULT 0,
                download_videos INTEGER DEFAULT 0,
                schedule_type TEXT,
                schedule_value TEXT,
                is_active INTEGER DEFAULT 1,
                last_run TIMESTAMP,
                next_run TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Scraping results table (enhanced)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER,
                url TEXT NOT NULL,
                data_type TEXT NOT NULL,
                extracted_data TEXT NOT NULL,
                cleaned_data TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES scraping_jobs (id)
            )
        """)

        # Scraping statistics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scraping_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER,
                url TEXT NOT NULL,
                data_type TEXT NOT NULL,
                items_scraped INTEGER DEFAULT 0,
                items_cleaned INTEGER DEFAULT 0,
                success INTEGER DEFAULT 1,
                error_message TEXT,
                execution_time REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES scraping_jobs (id)
            )
        """)

        # Storage usage tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS storage_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                media_type TEXT NOT NULL,
                file_count INTEGER DEFAULT 0,
                total_size_bytes INTEGER DEFAULT 0,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        logger.info("Database schema initialized successfully")

    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def create_scraping_job(name: str, url: str, data_type: str,
                       keyword: str = None, download_images: bool = False,
                       download_videos: bool = False, schedule_type: str = None,
                       schedule_value: str = None) -> Optional[int]:
    """Create a new scraping job"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO scraping_jobs
            (name, url, data_type, keyword, download_images, download_videos,
             schedule_type, schedule_value, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (name, url, data_type, keyword, int(download_images),
              int(download_videos), schedule_type, schedule_value))

        conn.commit()
        job_id = cursor.lastrowid
        logger.info(f"Created scraping job: {name} (ID: {job_id})")
        return job_id

    except Exception as e:
        logger.error(f"Error creating scraping job: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def get_scraping_jobs(active_only: bool = False) -> List[Dict[str, Any]]:
    """Get all scraping jobs"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        if active_only:
            cursor.execute("""
                SELECT * FROM scraping_jobs
                WHERE is_active = 1
                ORDER BY created_at DESC
            """)
        else:
            cursor.execute("""
                SELECT * FROM scraping_jobs
                ORDER BY created_at DESC
            """)

        columns = [desc[0] for desc in cursor.description]
        jobs = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return jobs

    except Exception as e:
        logger.error(f"Error fetching scraping jobs: {e}")
        return []
    finally:
        conn.close()


def get_scraping_job(job_id: int) -> Optional[Dict[str, Any]]:
    """Get a specific scraping job"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM scraping_jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()

        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None

    except Exception as e:
        logger.error(f"Error fetching scraping job {job_id}: {e}")
        return None
    finally:
        conn.close()


def update_scraping_job(job_id: int, **kwargs) -> bool:
    """Update a scraping job"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Build update query dynamically
        fields = []
        values = []
        for key, value in kwargs.items():
            if key in ['name', 'url', 'data_type', 'keyword', 'download_images',
                      'download_videos', 'schedule_type', 'schedule_value', 'is_active',
                      'last_run', 'next_run']:
                fields.append(f"{key} = ?")
                values.append(value)

        if not fields:
            return False

        fields.append("updated_at = ?")
        values.append(datetime.now().isoformat())
        values.append(job_id)

        query = f"UPDATE scraping_jobs SET {', '.join(fields)} WHERE id = ?"
        cursor.execute(query, values)
        conn.commit()

        logger.info(f"Updated scraping job {job_id}")
        return True

    except Exception as e:
        logger.error(f"Error updating scraping job {job_id}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def delete_scraping_job(job_id: int) -> bool:
    """Delete a scraping job and its results"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Delete associated results
        cursor.execute("DELETE FROM results WHERE job_id = ?", (job_id,))
        cursor.execute("DELETE FROM scraping_stats WHERE job_id = ?", (job_id,))
        cursor.execute("DELETE FROM scraping_jobs WHERE id = ?", (job_id,))

        conn.commit()
        logger.info(f"Deleted scraping job {job_id}")
        return True

    except Exception as e:
        logger.error(f"Error deleting scraping job {job_id}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def save_scraping_results(url: str, data_type: str, extracted_data: List[str],
                         cleaned_data: List[str] = None, job_id: int = None,
                         metadata: str = None) -> bool:
    """Save scraped data to database"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        timestamp = datetime.now().isoformat()
        for i, data in enumerate(extracted_data):
            cleaned = cleaned_data[i] if cleaned_data and i < len(cleaned_data) else None
            cursor.execute("""
                INSERT INTO results (job_id, url, data_type, extracted_data, cleaned_data, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (job_id, url, data_type, str(data), cleaned, metadata, timestamp))

        conn.commit()
        logger.info(f"Saved {len(extracted_data)} results to database")
        return True

    except Exception as e:
        logger.error(f"Error saving results: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def save_scraping_stats(url: str, data_type: str, items_scraped: int,
                       items_cleaned: int = 0, success: bool = True,
                       error_message: str = None, execution_time: float = 0,
                       job_id: int = None) -> bool:
    """Save scraping statistics"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO scraping_stats
            (job_id, url, data_type, items_scraped, items_cleaned, success,
             error_message, execution_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (job_id, url, data_type, items_scraped, items_cleaned,
              int(success), error_message, execution_time))

        conn.commit()
        return True

    except Exception as e:
        logger.error(f"Error saving stats: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def get_dashboard_stats() -> Dict[str, Any]:
    """Get statistics for dashboard"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        stats = {}

        # Total jobs
        cursor.execute("SELECT COUNT(*) FROM scraping_jobs")
        stats['total_jobs'] = cursor.fetchone()[0]

        # Active jobs
        cursor.execute("SELECT COUNT(*) FROM scraping_jobs WHERE is_active = 1")
        stats['active_jobs'] = cursor.fetchone()[0]

        # Total items scraped
        cursor.execute("SELECT COUNT(*) FROM results")
        stats['total_items'] = cursor.fetchone()[0]

        # Success rate (last 100 runs)
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(success) as successful
            FROM scraping_stats
            ORDER BY created_at DESC
            LIMIT 100
        """)
        row = cursor.fetchone()
        if row and row[0] > 0:
            stats['success_rate'] = (row[1] / row[0]) * 100
        else:
            stats['success_rate'] = 0

        # Average execution time
        cursor.execute("""
            SELECT AVG(execution_time)
            FROM scraping_stats
            WHERE success = 1
        """)
        avg_time = cursor.fetchone()[0]
        stats['avg_execution_time'] = round(avg_time, 2) if avg_time else 0

        # Data type distribution
        cursor.execute("""
            SELECT data_type, COUNT(*) as count
            FROM results
            GROUP BY data_type
        """)
        stats['data_type_distribution'] = dict(cursor.fetchall())

        # Recent activity (last 7 days)
        cursor.execute("""
            SELECT
                DATE(created_at) as date,
                COUNT(*) as count
            FROM scraping_stats
            WHERE created_at >= datetime('now', '-7 days')
            GROUP BY DATE(created_at)
            ORDER BY date
        """)
        stats['recent_activity'] = [
            {'date': row[0], 'count': row[1]}
            for row in cursor.fetchall()
        ]

        # Top scraped sites
        cursor.execute("""
            SELECT url, COUNT(*) as count
            FROM scraping_stats
            GROUP BY url
            ORDER BY count DESC
            LIMIT 10
        """)
        stats['top_sites'] = [
            {'url': row[0], 'count': row[1]}
            for row in cursor.fetchall()
        ]

        return stats

    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {e}")
        return {}
    finally:
        conn.close()


def clear_all_data() -> bool:
    """Clear all scraped data"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM results")
        cursor.execute("DELETE FROM scraping_stats")
        conn.commit()
        logger.info("Cleared all scraped data")
        return True

    except Exception as e:
        logger.error(f"Error clearing data: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


# Initialize database on module import
init_database()
