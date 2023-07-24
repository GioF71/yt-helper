import os
import sys
from pytube import YouTube,Playlist, StreamQuery,Stream
import sqlite3
import datetime
from resolution import Resolution

def get_db_filename() -> str: return os.getenv("DB_FILE")

def get_max_resolution() -> Resolution:
    env_max_resolution : str = os.getenv("MAX_RESOLUTION")
    return Resolution(env_max_resolution) if env_max_resolution else None

def get_output_path() -> str: return os.getenv("OUTPUT_PATH")

def compare_resolution(left : Resolution, right : Resolution) -> int:
    cmp : int = -1 if left.get_height() < right.get_height() else 0 if left.get_height() == right.get_height() else 1
    if cmp == 0:
        cmp = -1 if left.get_mode() < right.get_mode() else 0 if left.get_mode() == right.get_mode() else 1
    return cmp

def select_best(yt : YouTube) -> Stream:
    sq : StreamQuery = yt.streams.order_by("resolution")
    max_resolution : Resolution = get_max_resolution()
    stream : Stream
    select_stream : Stream = None
    stream : Stream
    for stream in sq:
        current_res : Resolution = Resolution(stream.resolution)
        if compare_resolution(current_res, max_resolution) > 0:
            # exceeding max resolution
            break
        select_stream = stream
    return select_stream

connection = sqlite3.connect(get_db_filename(),
                detect_types=sqlite3.PARSE_DECLTYPES |
                sqlite3.PARSE_COLNAMES)

# cursor object
cursor_obj = connection.cursor()
 
# Creating table
create_downloads_table : str = """
    CREATE TABLE IF NOT EXISTS downloads (
    download_url VARCHAR(255) PRIMARY KEY,
    download_date TIMESTAMP)
"""
 
cursor_obj.execute(create_downloads_table)

def get_download(url : str):
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM downloads WHERE download_url = ?", (url,))
    rows = cursor.fetchall()
    cursor.close()
    return rows

def store(url : str):
    tuple = (url, datetime.datetime.now())
    cursor = connection.cursor()
    cursor.execute("INSERT INTO downloads(download_url, download_date) VALUES(?,?)", tuple)
    connection.commit()
    cursor.close()

def main():
    for row in cursor_obj.execute('SELECT * FROM downloads'):
        print(row)

    playlist_url : str = os.getenv("PLAYLIST_URL")
    max_resolution : Resolution = get_max_resolution()
    if not playlist_url:
        print("No playlist specified")
        sys.exit(1)
    print(f"Playlist id: {playlist_url}")
    playlist : Playlist = Playlist(playlist_url)
    print(f"Playlist title: {playlist.title}")
    url_list : list[str] = playlist.video_urls
    url : str
    for url in url_list:
        print(f"Found url [{url}]")

        rows = get_download(url)
        if not rows:
            yt : YouTube = YouTube(url)
            sq : StreamQuery = yt.streams.order_by("resolution")
            stream : Stream = sq.last if not max_resolution else select_best(yt)
            print(f"  Selected format: res = {stream.resolution} video_codec = {stream.video_codec} audio_codec = {stream.audio_codec}")
            # TODO check if already downloaded
            # Download!
            stream.download(output_path = get_output_path())
            # save to db
            store(url)

if __name__ == '__main__':
    main()
