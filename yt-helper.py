import os
import sys
import string
import time
import copy
import logging

from channel_subscription import ChannelSubscription
from channel_identifier_type import ChannelIdentifierType

import persistence

import yt_dlp
import exiftool
import pytube
from pytube import YouTube, Channel, Playlist, StreamQuery, Stream
from pytube.exceptions import AgeRestrictedError
from mutagen.mp4 import MP4, MP4MetadataError, MP4StreamInfoError

from functools import cmp_to_key


def get_playlists() -> list[str]: return os.getenv("PLAYLIST_LIST", "").split(",")
def get_channel_names() -> list[str]: return os.getenv("CHANNEL_NAME_LIST", "").split(",")

def get_max_resolution() -> str: return os.getenv("MAX_RESOLUTION", "1080")
def get_output_format() -> str: return os.getenv("OUTPUT_FORMAT", "mkv")

def get_file_name_template() -> str:
    return os.getenv("FILE_NAME_TEMPLATE", "%(uploader)s - %(upload_date>%Y-%m-%d)s - %(title)s.%(ext)s")

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

def store_tags(yt : yt_dlp.YoutubeDL, info_dict : dict[str, any]):
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

def yt_dlp_monitor(d):
    status = d["status"]
    if status == "finished":
        file_name : str = d["filename"]
        print(f"Status [{status}] FileName [{file_name}]")

class PostProcessor(yt_dlp.postprocessor.PostProcessor):
    def run(self, info):
        self.to_screen(f"File name is [{info['filename']}]")
        #file_name : str = info["filename"]
        #tool : exiftool.ExifToolHelper = exiftool.ExifToolHelper(file_name)
        #metadata = tool.get_metadata(file_name)
        return [], info

def process_url(url : str):
    if not persistence.has_been_downloaded(url):
        params : dict[str, any] = dict()
        params["outtmpl"] = os.path.join(get_output_path(), get_file_name_template())
        max_resolution : str = get_max_resolution()
        params["format"] = f"bv*[height<={max_resolution}]+ba" if max_resolution else f"bv+ba"
        if get_output_format(): params["merge_output_format"] = get_output_format()
        params["writethumbnail"] = True
        params["embedthumbnail"] = True
        params["progress_hooks"] = [yt_dlp_monitor]
        
        ydl_opts = {
            "outtmpl": os.path.join(get_output_path(), get_file_name_template()),
            "format": f"bv*[height<={get_max_resolution()}]+ba",
            "merge_output_format": get_output_format(),
            'writethumbnail': True,
            'embedthumbnail': True,
            "progress_hooks": [yt_dlp_monitor],
            #'postprocessors': [{
            #    'key': 'MetadataParser',
            #    'when': 'pre_process',
            #    'actions': [
            #        (yt_dlp.MetadataParserPP.Actions.INTERPRET, 'author', r'(?s)(?P<meta_comment>.+)'),
            #        (yt_dlp.MetadataParserPP.Actions.INTERPRET, 'artist', r'(?s)(?P<meta_comment>.+)'),
            #        (yt_dlp.MetadataParserPP.Actions.INTERPRET, 'aART', r'(?s)(?P<meta_comment>.+)')
            #        
            #    ]
            #},
            #]
        }
        pytube_yt : pytube.YouTube = pytube.YouTube(url)
        skip_video : bool = False
        skip_reason : str = None
     
        is_upcoming : bool = pytube_yt.vid_info["videoDetails"]["isUpcoming"] if "videoDetails" in pytube_yt.vid_info and "isUpcoming" in pytube_yt.vid_info["videoDetails"] else False
        if is_upcoming:
            skip_video = True
            skip_reason = "Video is marked as \"upcoming\""
        #playability : dict[str, any] = pytube_yt.vid_info["playabilityStatus"]
        #print(f"Playability status for url:[{url}] Author:[{pytube_yt.author}] Title:[{pytube_yt.title}] is: [{playability['status']}]")
        if not skip_video:
            yt : yt_dlp.YoutubeDL = yt_dlp.YoutubeDL(params = params)
            yt.add_post_processor(PostProcessor(), when='after_move')
            try:
                yt.download(url)
                # TODO add tags
                persistence.store_download_url(url)
            except yt_dlp.utils.DownloadError as e:
                print(f"Cannot download URL [{url}] due to [{type(e).__name__}] [{e.message if hasattr(e, 'message') else e}]")
        else:
            print(f"Skipping video at url [{url}], reason: [{skip_reason}]")
    else:
        print(f"Already downloaded [{url}]")

def build_playlist_url(playlist_id : str) -> str:
    return f"https://www.youtube.com/playlist?list={playlist_id}"

def process_playlist(playlist : str):
    playlist_url : str = build_playlist_url(playlist)
    print(f"Playlist id: {playlist_url}")
    playlist : Playlist = Playlist(playlist_url)
    if playlist and len(playlist) > 0:
        print(f"Playlist title: {playlist.title}")
        url_list : list[str] = playlist.video_urls
        url : str
        for url in url_list if url_list else []:
            print(f"Found url [{url}]")
            process_url(url)

def process_playlists():
    lst : list[str] = get_playlists()
    current : str
    for current in lst if lst else []:
        process_playlist(current)

def process_channel_subscription(channel : ChannelSubscription):
    channel_url : str = channel.build_url()
    print(f"Channel Identifier: {channel.identifier_type} {channel.identifier_value}")
    channel : Channel = Channel(channel_url)
    print(f"Channel Name:[{channel.channel_name}] Id:[{channel.channel_id}] URL:[{channel_url}]")
    current_url : str
    for current_url in channel.video_urls:
        print(f"Found video at url [{current_url}]")
        
def process_channels_names():
    lst : list[ChannelSubscription] = list()
    c_list : list[str] = get_channel_names()
    for ch_name in c_list if c_list else []:
        identifier : str
        subscription_start : str
        identifier, subscription_start = ch_name.split(":")
        # TODO validate
        ch_subscription : ChannelSubscription = ChannelSubscription(
            ChannelIdentifierType.CHANNEL_NAME, 
            identifier, 
            subscription_start)
        lst.append(ch_subscription)
    process_channel_subscription_list(lst)
        
def process_channel_subscription_list(lst : list[ChannelSubscription]):
    current : str
    for current in lst if lst else []:
        process_channel_subscription(current)

def main():
    while True:
        process_channels_names()
        process_playlists()
        if is_loop_enabled:
            print(f"Sleeping ...")     
            time.sleep(60)
        else:
            break

if __name__ == '__main__':
    main()
