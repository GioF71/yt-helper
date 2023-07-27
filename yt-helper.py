import os
import sys
import string
import time
import copy

import persistence

from resolution import Resolution

import yt_dlp
from pytube import YouTube, Playlist, StreamQuery, Stream
from pytube.exceptions import AgeRestrictedError
from mutagen.mp4 import MP4, MP4MetadataError, MP4StreamInfoError

from functools import cmp_to_key

def get_max_resolution() -> str: return os.getenv("MAX_RESOLUTION", "1080")
def get_output_format() -> str: return os.getenv("OUTPUT_FORMAT", "mp4")

def get_file_name_template() -> str:
    return os.getenv("FILE_NAME_TEMPLATE", "$title.$subtype")

def get_subtype() -> str: return os.getenv("SUBTYPE", "mp4")

def get_output_path() -> str: return os.getenv("OUTPUT_PATH", ".")

def is_loop_enabled() -> bool: return os.gentenv("ENABLE_LOOP", "1") == "1"

def compare_str(left : str, right : str) -> int:
    if not left and not right: return 0
    if not left: return -1
    if not right: return 1
    if left == right: return 0
    if left < right: return -1
    return 1

def store_tags(ytdlp : yt_dlp.YoutubeDL, info_dict : dict[str, any]):
    if get_output_format() == "mp4":
        file_name : str = info_dict["filename"]
        try: 
            tags = MP4(file_name)
        except (MP4MetadataError, MP4StreamInfoError) as e:
            print("Adding MP4Tags header")
            tags = MP4()
        tags["titl"] = info_dict["title"]
        tags["auth"] = info_dict["uploader"]
        tags["aART"] = info_dict["uploader"]
        tags["\xa9ART"] = info_dict["uploader"]
        #tags["\\xa9day"] = str(yt.publish_date.year) #TODO use upload_date which is for example 20230510
        tags.save(file_name)

filename_info_dict : dict[str, dict[str, any]] = {}

def yt_dlp_monitor(d):
    status = d["status"]
    if status == "finished":
        file_name : str = d["filename"]
        print(f"Status [{status}] FileName [{file_name}]")

class MyCustomPP(yt_dlp.postprocessor.PostProcessor):
    def run(self, info):
        self.to_screen(f"File name is [{info['filename']}]")
        filename_info_dict[info["webpage_url"]] = copy.deepcopy(info)
        return [], info

def process_url(url : str):
    if not persistence.has_been_downloaded(url):
        #full_filename_path : str = os.path.join(get_output_path(), video_filename)
        ydl_opts = {
            "outtmpl": os.path.join(get_output_path(), "%(uploader)s - %(upload_date>%Y-%m-%d)s - %(title)s.%(ext)s"),
            "format": f"bv*[height<={get_max_resolution()}]+ba",
            "merge_output_format": get_output_format(),
            'writethumbnail': True,
            'embedthumbnail': True,
            "progress_hooks": [yt_dlp_monitor]
        }        
        ytdlp : yt_dlp.YoutubeDL = yt_dlp.YoutubeDL(ydl_opts)
        ytdlp.add_post_processor(MyCustomPP(), when='after_move')
        ytdlp.download(url)
        # TODO add tags
        info_dict : dict[str, any] = filename_info_dict[url]
        # TODO does not work ### store_tags(ytdlp, info_dict)
        persistence.store_download_url(url)
        del filename_info_dict[url]
        
        #yt : YouTube = YouTube(url)
        #title = yt.title
        #author = yt.author
        #publish_date = yt.publish_date
        #age_restricted : bool = yt.age_restricted
        #if age_restricted:
        #    print(f"Video is age restricted, skipping")
        #    return
        #print(f"Downloading [{title}] by [{author}] on [{publish_date}]...")
        #stream : Stream = select_stream(yt)
        #if stream:
        #    print(f"Selected format: res:{stream.resolution} subtype:{stream.subtype} video_codec:{stream.video_codec} audio_codec:{stream.audio_codec}")
        #    # Download if not exists
        #    publish_date : str = f"{yt.publish_date.year:04d}-{yt.publish_date.month:02d}-{yt.publish_date.day:02d}"
        #    video_filename : str = string.Template(get_file_name_template()).substitute(
        #        title = yt.title,
        #        author = yt.author,
        #        publish_date = publish_date,
        #        subtype = stream.subtype)
        #    full_filename_path : str = os.path.join(get_output_path(), video_filename)
        #    file_path : str = None
        #    if os.path.exists(full_filename_path):
        #        print(f"File already exists [{full_filename_path}] for url [{url}]")
        #    else:
        #        file_path : str = stream.download(
        #            output_path = get_output_path(), 
        #            filename = video_filename)
        #        full_filename_path = file_path
        #    # store tags
        #    store_tags(yt, stream, full_filename_path)
        #    # save url to db
        #    persistence.store_download_url(url)
        #else:
        #    print(f"ERROR: Could not find a matching stream for [{url}]")
    else:
        print(f"Already downloaded [{url}]")

def build_playlist_url(playlist_id : str) -> str:
    return f"https://www.youtube.com/playlist?list={playlist_id}"

def main():
    playlist_list : list[str] = os.getenv("PLAYLIST").split(",")
    while True:
        if not playlist_list or len(playlist_list) == 0:
            print("No playlist specified")
            sys.exit(1)
        current_playlist : str
        for current_playlist in playlist_list:
            playlist_url : str = build_playlist_url(current_playlist)
            print(f"Playlist id: {playlist_url}")
            playlist : Playlist = Playlist(playlist_url)
            print(f"Playlist title: {playlist.title}")
            url_list : list[str] = playlist.video_urls
            url : str
            for url in url_list:
                print(f"Found url [{url}]")
                process_url(url)
        if is_loop_enabled:
            print(f"Sleeping ...")     
            time.sleep(60)
        else:
            break

if __name__ == '__main__':
    main()
