import os
import sqlite3
import datetime

def __get_db_filename() -> str: return os.getenv("DB_FILE")

def __get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(
        __get_db_filename(),
        detect_types = 
            sqlite3.PARSE_DECLTYPES |
            sqlite3.PARSE_COLNAMES)
    return connection

def __prepare_table():
    cursor_obj = __connection.cursor()
    # Creating table
    create_downloads_table : str = """
        CREATE TABLE IF NOT EXISTS downloads (
        download_url VARCHAR(255) PRIMARY KEY,
        download_date TIMESTAMP)
    """
    cursor_obj.execute(create_downloads_table)
    cursor_obj.close()

__connection : sqlite3.Connection = __get_connection()
__prepare_table()
    
def __get_downloads_by_url(url : str):
    cursor = __connection.cursor()
    cursor.execute("SELECT * FROM downloads WHERE download_url = ?", (url,))
    rows = cursor.fetchall()
    cursor.close()
    return rows

def has_been_downloaded(url : str) -> bool:
    return len(__get_downloads_by_url(url)) > 0

def store_download_url(url : str):
    tuple = (url, datetime.datetime.now())
    cursor = __connection.cursor()
    cursor.execute("INSERT INTO downloads(download_url, download_date) VALUES(?, ?)", tuple)
    cursor.close()
    __connection.commit()
