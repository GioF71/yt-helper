import os
import sqlite3
import datetime

from playlist import Playlist

def __get_db_filename() -> str: return os.getenv("DB_FILE")

def __get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(
        __get_db_filename(),
        detect_types = 
            sqlite3.PARSE_DECLTYPES |
            sqlite3.PARSE_COLNAMES)
    return connection

def __prepare_table_downloads():
    cursor_obj = __connection.cursor()
    # Creating table
    create_table : str = """
        CREATE TABLE IF NOT EXISTS downloads (
        download_url VARCHAR(255) PRIMARY KEY,
        download_date TIMESTAMP)
    """
    cursor_obj.execute(create_table)
    cursor_obj.close()

def __prepare_table_playlists():
    cursor_obj = __connection.cursor()
    # Creating table
    create_table : str = """
        CREATE TABLE IF NOT EXISTS playlists (
        playlist_id VARCHAR(255) PRIMARY KEY,
        date_limit VARCHAR(32))
    """
    cursor_obj.execute(create_table)
    cursor_obj.close()

__connection : sqlite3.Connection = __get_connection()
__prepare_table_downloads()
__prepare_table_playlists()
    
def __get_downloads_by_url(url : str):
    cursor = __connection.cursor()
    cursor.execute("SELECT * FROM downloads WHERE download_url = ?", (url,))
    rows = cursor.fetchall()
    cursor.close()
    return rows

def __get_playlist_by_id(id : str):
    cursor = __connection.cursor()
    cursor.execute("SELECT * FROM playlists WHERE playlist_id = ?", (id,))
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

def store_playlist(playlist : Playlist):
    existing = __get_playlist_by_id(playlist.playlist_id)
    start : str = playlist.subscription_start.strftime('%Y-%m-%d') if playlist.subscription_start else None
    if len(existing) == 0:
        tuple = (playlist.playlist_id, start)
        cursor = __connection.cursor()
        cursor.execute("INSERT INTO playlists(playlist_id, date_limit) VALUES(?, ?)", tuple)
        cursor.close()
        __connection.commit()
    else:
        tuple = (start, playlist.playlist_id)
        cursor = __connection.cursor()
        cursor.execute("UPDATE playlists SET date_limit = ? WHERE playlist_id = ?", tuple)
        cursor.close()
        __connection.commit()
