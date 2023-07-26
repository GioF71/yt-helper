import os
import sys

import persistence

from resolution import Resolution
from pytube import YouTube, Playlist, StreamQuery, Stream
from mutagen.mp4 import MP4, MP4MetadataError

from functools import cmp_to_key

def get_max_resolution() -> Resolution:
    env_max_resolution : str = os.getenv("MAX_RESOLUTION")
    return Resolution(env_max_resolution) if env_max_resolution else None

def get_subtype() -> str: return os.getenv("SUBTYPE", "mp4")

def get_output_path() -> str: return os.getenv("OUTPUT_PATH")

def compare_resolution(left : Resolution, right : Resolution) -> int:
    cmp : int = -1 if left.get_height() < right.get_height() else 0 if left.get_height() == right.get_height() else 1
    if cmp == 0:
        cmp = -1 if left.get_mode() < right.get_mode() else 0 if left.get_mode() == right.get_mode() else 1
    return cmp

def compare_str(left : str, right : str) -> int:
    if not left and not right: return 0
    if not left: return -1
    if not right: return 1
    if left == right: return 0
    if left < right: return -1
    return 1

def compare_stream(left : Stream, right : Stream) -> int:
    left_res : Resolution = Resolution(left.resolution)
    right_res : Resolution = Resolution(right.resolution)
    cmp : int = compare_resolution(left_res, right_res)
    if cmp == 0:
        left_fps : int = left.fps
        right_fps : int = right.fps
        cmp = left_fps - right_fps
    if cmp == 0:
        left_vcodec : str = left.video_codec
        right_vcodec : str = right.video_codec
        cmp = compare_str(left_vcodec, right_vcodec)
    if cmp == 0:
        left_is_hdr : bool = left.is_hdr
        right_is_hdr : bool = right.is_hdr
        cmp = 0 if left_is_hdr == right_is_hdr else 1 if left_is_hdr else -1
    if cmp == 0:
        left_acodec : str = left.audio_codec
        right_acodec : str = right.audio_codec
        cmp = compare_str(left_acodec, right_acodec)
    if cmp == 0:
        left_bitrate : int = left.bitrate
        right_bitrate : int = right.bitrate
        cmp = left_bitrate - right_bitrate
    if cmp == 0:
        left_fs : int = left.filesize
        right_fs : int = right.filesize
        cmp = left_fs - right_fs
    return cmp

def list_streams(yt : YouTube) -> list[Stream]:
    stream_list : list[Stream] = list()
    sq : StreamQuery = yt.streams.order_by("resolution")
    current : Stream
    for current in sq:
        stream_list.append(current)
    stream_list.sort(key = cmp_to_key(compare_stream), reverse = True)
    return stream_list

def stream_res_filter(stream_list_desc : list[Stream], max_resolution : Resolution) -> list[Stream]:
    filtered : list[Stream] = list()
    current : Stream
    match_res : Resolution = None
    for current in stream_list_desc:
        current_res : Resolution = Resolution(current.resolution)
        if compare_resolution(current_res, max_resolution) <= 0:
            # allowed
            if not match_res: match_res = current_res
            if match_res and compare_resolution(current_res, match_res) < 0: break
            filtered.append(current)
    return filtered

def stream_format_filter(stream_list_desc : list[Stream], subtype : str) -> list[Stream]:
    filtered : list[Stream] = list()
    current : Stream
    for current in stream_list_desc:
        if current.subtype == subtype:
            filtered.append(current)
    return filtered

def select_best(yt : YouTube) -> Stream:
    stream_list : list[Stream] = list_streams(yt)
    stream_list = stream_res_filter(stream_list, get_max_resolution())
    stream_list = stream_format_filter(stream_list, get_subtype())
    return stream_list[0] if len(stream_list) > 0 else None

def store_tags(yt : YouTube, stream : Stream, file_path : str):
    if stream.subtype == "mp4":
        try: 
            tags = MP4(file_path)
        except MP4MetadataError as e:
            print("Adding MP4Tags header")
            tags = MP4()
        tags["titl"] = yt.title
        tags["auth"] = yt.author
        tags["aART"] = yt.author
        tags["\xa9ART"] = yt.author
        tags["\\xa9day"] = str(yt.publish_date.year)
        tags.save(file_path)

def main():
    persistence.prepare_table()
    playlist_url : str = os.getenv("PLAYLIST_URL")
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
        rows = persistence.get_downloads_by_url(url)
        if not rows:
            yt : YouTube = YouTube(url)
            #sq : StreamQuery = yt.streams.order_by("resolution")
            #stream : Stream = sq.last if not max_resolution else select_best(yt)
            stream : Stream = select_best(yt)
            if stream:
                print(f"Selected format: res:{stream.resolution} subtype:{stream.subtype} video_codec:{stream.video_codec} audio_codec:{stream.audio_codec}")
                # Download if not exists
                default_filename : str = stream.default_filename
                full_filename_path : str = os.path.join(get_output_path(), default_filename)
                file_path : str = None
                if os.path.exists(full_filename_path):
                    print("File already exists [{full_filename_path}] for url [{url}]")
                else:
                    file_path : str = stream.download(output_path = get_output_path())
                    full_filename_path = file_path
                # store tags
                store_tags(yt, stream, full_filename_path)
                # save url to db
                persistence.store_download_url(url)
            else:
                print(f"ERROR: Could not find a matching stream for [{url}]")

if __name__ == '__main__':
    main()
