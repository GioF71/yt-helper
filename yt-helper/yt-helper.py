import os
import string
import time
import shutil
import datetime

from channel_subscription import ChannelSubscription
from channel_identifier_type import ChannelIdentifierType
from playlist import Playlist

import persistence

import yt_dlp
import slugify
import pytube

from functools import cmp_to_key

def clean_list(input_list : list[str]) -> list[str]:
    result : list[str] = list()
    curr : str
    for curr in input_list if input_list and len(input_list) > 0 else []:
        if curr and len(curr) > 0:
            result.append(curr)
    return result

def getenv_clean(env_name : str, env_default : any) -> any:
    value : any = os.getenv(env_name)
    if not value: value = env_default
    if isinstance(value, str) and len(value) == 0: value = env_default
    return value

def get_playlists() -> list[str]: return clean_list(getenv_clean("PLAYLIST_LIST", "").split(","))
def get_channel_names() -> list[str]: return clean_list(getenv_clean("CHANNEL_NAME_LIST", "").split(","))

def get_max_resolution() -> str: return getenv_clean("MAX_RESOLUTION", "1080")
def get_output_format() -> str: return getenv_clean("OUTPUT_FORMAT", "mkv")

def get_file_name_template() -> str:
    return getenv_clean("FILE_NAME_TEMPLATE", "%(uploader)s - %(upload_date>%Y-%m-%d)s - %(title)s [%(id)s].%(ext)s")

def get_output_path() -> str: return getenv_clean("OUTPUT_PATH", ".")

def is_loop_enabled() -> bool: return os.gentenv("ENABLE_LOOP", "1") == "1"
def get_loop_wait_sec() -> int: return int(getenv_clean("LOOP_WAIT_SEC", "300"))
def is_slugify_enabled() -> bool: return getenv_clean("SLUGIFY", "0") == "1"
def is_printable_enabled() -> bool: return getenv_clean("PRINTABLE", "1") == "1"
def is_dir_per_channel_enabled() -> bool: return getenv_clean("DIRECTORY_PER_CHANNEL", "0") == "1"

def compare_str(left : str, right : str) -> int:
    if not left and not right: return 0
    if not left: return -1
    if not right: return 1
    if left == right: return 0
    if left < right: return -1
    return 1

file_name_by_url : dict[str, str] = dict()

def yt_dlp_monitor(d):
    status = d["status"]
    if status == "finished":
        file_name : str = d["filename"]
        print(f"Status [{status}] FileName [{file_name}]")

class PostProcessor(yt_dlp.postprocessor.PostProcessor):
    def run(self, info):
        file_name : str = info["filename"]
        url : str = info["webpage_url"]
        self.to_screen(f"File name is [{file_name}]")
        file_name_by_url[url] = file_name
        return [], info

def as_printable(s : str) -> str:
    return ''.join([str(char) for char in s if char in string.printable])

def process_url(url : str):
    if not persistence.has_been_downloaded(url):
        params : dict[str, any] = dict()
        params["outtmpl"] = os.path.join(get_output_path(), get_file_name_template())
        max_resolution : str = get_max_resolution()
        params["format"] = f"bv*[height<={max_resolution}]+ba" if max_resolution else f"bv+ba"
        if get_output_format(): params["merge_output_format"] = get_output_format()
        params["writethumbnail"] = False
        params["embedthumbnail"] = True
        params["embedmetadata"] = True
        params["progress_hooks"] = [yt_dlp_monitor]
        pytube_yt : pytube.YouTube = pytube.YouTube(url)
        skip_video : bool = False
        skip_reason : str = None
        is_upcoming : bool = (pytube_yt.vid_info["videoDetails"]["isUpcoming"] 
            if "videoDetails" in pytube_yt.vid_info and 
                "isUpcoming" in pytube_yt.vid_info["videoDetails"] 
            else False)
        if is_upcoming:
            skip_video = True
            skip_reason = "Video is marked as \"upcoming\""
        if not skip_video:
            yt : yt_dlp.YoutubeDL = yt_dlp.YoutubeDL(params = params)
            yt.add_post_processor(PostProcessor(), when='after_move')
            try:
                yt.download(url)
                # TODO add tags
                persistence.store_download_url(url)
                # TODO slugify filename
                downloaded_file_name : str = file_name_by_url[url] if url in file_name_by_url else None
                if downloaded_file_name:
                    do_rename : bool = False
                    splitted : tuple[str, str] = os.path.split(downloaded_file_name)
                    path_portion : str = splitted[0]
                    file_portion : str = splitted[1]
                    final_path : str = path_portion
                    final_file_name : str = file_portion
                    if is_slugify_enabled():
                        f : str
                        e : str 
                        f, e = os.path.splitext(file_portion)
                        s : str = slugify.slugify(f)
                        slugified : str = f"{s}{e}"
                        if slugified != file_portion:
                            final_file_name = slugified
                            do_rename = True
                    if not is_slugify_enabled() and is_printable_enabled():
                        final_file_name = as_printable(final_file_name)
                        do_rename = True
                    if do_rename:
                        candidate_final_full_path : str = os.path.join(final_path, final_file_name)
                        print(f"File {downloaded_file_name} to be renamed to {candidate_final_full_path}")
                        try:
                            os.rename(downloaded_file_name, candidate_final_full_path)
                            final_full_path = candidate_final_full_path
                        except Exception as e:
                            print(f"Cannot rename [{downloaded_file_name}] to [{candidate_final_full_path}], cause: [{e.message if hasattr(e, 'message') else e}]")
                    else:
                        final_full_path = downloaded_file_name
                    if is_dir_per_channel_enabled():
                        # Create dir if not exists
                        target_dir : str = os.path.join(get_output_path(), pytube_yt.author)
                        if not os.path.exists(target_dir):
                            os.mkdir(target_dir)
                        try:    
                            # Move file
                            shutil.move(final_full_path, target_dir)
                        except Exception as e:
                            print(f"Cannot move [{final_full_path}] to [{target_dir}], cause: [{e.message if hasattr(e, 'message') else e}]")
                    del file_name_by_url[url]
            except yt_dlp.utils.DownloadError as e:
                print(f"Cannot download URL [{url}] due to [{type(e).__name__}] [{e.message if hasattr(e, 'message') else e}]")
        else:
            print(f"Skipping video at url [{url}], reason: [{skip_reason}]")
    else:
        print(f"Video at URL: [{url}] has been downloaded already.")

def process_playlist(playlist : Playlist):
    playlist_url : str = playlist.build_url()
    print(f"Playlist Id: [{playlist.playlist_id}] URL: [{playlist_url}]")
    pytube_playlist : pytube.Playlist = pytube.Playlist(playlist_url)
    # we cannot even read title if playlist is empty
    # so we are checking here
    if pytube_playlist and len(pytube_playlist) > 0:
        print(f"Playlist title: [{pytube_playlist.title}]")
        url_list : list[str] = pytube_playlist.video_urls
        url : str
        for url in url_list if url_list else []:
            print(f"Found url [{url}]")
            current_yt : pytube.YouTube = pytube.YouTube(url)
            publish_date : datetime = current_yt.publish_date
            print(f"  Author: [{current_yt.author}]")
            print(f"  Title: [{current_yt.title}]")
            print(f"  Publish_date: [{publish_date.strftime('%Y-%m-%d') if publish_date else None}]")
            if not playlist.is_publish_date_allowed(publish_date):
                print(f"Video skipped, its date [{publish_date.strftime('%Y-%m-%d')}] is before the subscription start [{playlist.subscription_start.strftime('%Y-%m-%d')}]")
            process_url(url)
    else:
        # empty playlist
        print(f"Playlist is empty, nothing to do.")

def process_playlists():
    lst : list[str] = get_playlists()
    current : str
    for current in lst if lst else []:
        if current and len(current) > 0: 
            current_playlist : Playlist = Playlist.build(current)
            process_playlist(current_playlist)

def process_channel_subscription(channel : ChannelSubscription):
    channel_url : str = channel.build_url()
    print(f"Channel Identifier Type: [{channel.identifier_type.name}] Value: [{channel.identifier_value}]")
    channel : pytube.Channel = pytube.Channel(channel_url)
    print(f"Channel Name: [{channel.channel_name}] Id: [{channel.channel_id}] URL: [{channel_url}]")
    current_url : str
    for current_url in channel.video_urls:
        print(f"Found video at url [{current_url}]")
        
def process_channels_names():
    subscription_list : list[ChannelSubscription] = list()
    c_list : list[str] = get_channel_names()
    for ch_name in c_list if c_list else []:
        print(f"Processing channel [{ch_name}] ...")
        if ch_name and len(ch_name) > 0:
            identifier : str = None
            subscription_start : str = None
            if ":" in ch_name:
                identifier, subscription_start = ch_name.split(":")
            else:
                identifier = ch_name
            if not subscription_start:
                subscription_start = datetime.datetime.today().strftime('%Y-%m-%d')
            ch_subscription : ChannelSubscription = ChannelSubscription(
                ChannelIdentifierType.CHANNEL_NAME, 
                identifier, 
                subscription_start)
            subscription_list.append(ch_subscription)
    process_channel_subscription_list(subscription_list)
        
def process_channel_subscription_list(lst : list[ChannelSubscription]):
    current : str
    for current in lst if lst else []:
        process_channel_subscription(current)

def store_env_playlists():
    lst : list[str] = get_playlists()
    current : str
    for current in lst if lst else []:
        if current and len(current) > 0: 
            current : Playlist = Playlist.build(current)
            persistence.store_playlist(current)

def store_env_channels():
    lst : list[str] = get_channel_names()
    current : str
    for current in lst if lst else []:
        if current and len(current) > 0: 
            channel : ChannelSubscription = ChannelSubscription.build_by_name(current)
            persistence.store_channel(channel)

def main():
    store_env_channels()
    store_env_playlists()
    while True:
        process_channels_names()
        process_playlists()
        if is_loop_enabled:
            print(f"Sleeping for [{get_loop_wait_sec()}] seconds ...")     
            time.sleep(get_loop_wait_sec())
        else:
            break

if __name__ == '__main__':
    main()
