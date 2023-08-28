import os
import string
import time
import shutil
import datetime

from channel_subscription import ChannelSubscription
from channel_identifier_type import ChannelIdentifierType
from playlist import Playlist

import persistence
import variable_processor

import yt_dlp
import slugify
import pytube

from config import Config
from default_config import DefaultConfig
from config_key import ConfigKey

from functools import cmp_to_key

app_version : str = "0.0.1-alpha5"

app_config : Config = DefaultConfig()

list_separator : str = ","
pair_separator : str = ";"
pair_eq : str = "="

legacy_item_separator : str = ":"

playlist_single_value_key : str = "id"
playlist_legacy_item_list : list[str] = ["id", "subscription_start"]

channel_name_single_value_key : str = "name"
channel_name_legacy_item_list : list[str] = ["name", "subscription_start"]

def clean_list(input_list : list[str]) -> list[str]:
    result : list[str] = list()
    curr : str
    for curr in input_list if input_list and len(input_list) > 0 else []:
        if curr and len(curr) > 0:
            result.append(curr)
    return result

def getenv_clean(env_name : str, env_default : any = None) -> any:
    value : any = os.getenv(env_name)
    if not value: value = env_default
    if isinstance(value, str) and len(value) == 0: value = env_default
    return value

def get_playlists() -> list[dict[str, str]]:
    return variable_processor.process_variable(
        env_variable_name = "PLAYLIST_LIST",
        list_separator = list_separator,
        pair_separator = pair_separator,
        pair_eq = pair_eq,
        single_value_key = playlist_single_value_key,
        legacy_item_separator = legacy_item_separator,
        legacy_item_list = playlist_legacy_item_list)

def get_channel_names() -> list[dict[str, str]]:
    return variable_processor.process_variable(
        env_variable_name = "CHANNEL_NAME_LIST",
        list_separator = list_separator,
        pair_separator = pair_separator,
        pair_eq = pair_eq,
        single_value_key = channel_name_single_value_key,
        legacy_item_separator = legacy_item_separator,
        legacy_item_list = channel_name_legacy_item_list)

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

def get_config_from_options(config_key : ConfigKey, options : dict[str, str]) -> str:
    if config_key.key_name.lower() in options: return options[config_key.key_name.lower()]
    return app_config.get_value(config_key.key_name)

def process_url(url : str, options : dict[str, str] = {}):
    if not persistence.has_been_downloaded(url):
        params : dict[str, any] = dict()
        params["outtmpl"] = os.path.join(get_output_path(), get_file_name_template())
        max_resolution : str = app_config.get_max_resolution()
        params["format"] = f"bv*[height<={max_resolution}]+ba" if max_resolution else f"bv+ba"
        output_format : str = get_config_from_options(ConfigKey.OUTPUT_FORMAT, options)
        if output_format: params["merge_output_format"] = output_format
        params["writethumbnail"] = True
        params["embedthumbnail"] = True
        #params["addmetadata"] = True
        #params["embedmetadata"] = True
        #params["parse_metadata"] = [ "%(title)s:%(meta_title)s", "%(uploader)s:%(meta_artist)s" ]
        meta_date_format : str = '%(upload_date>%Y-%m-%d)s' if get_config_from_options(ConfigKey.FULL_DATE_FORMAT, options) == "1" else '%(upload_date>%Y)s'
        params["postprocessors"] = [
            {
                'key': 'FFmpegMetadata'
            }, 
            {       
                'key': 'MetadataParser',
                'when': 'pre_process',
                'actions': [
                    (yt_dlp.MetadataParserPP.Actions.INTERPRET, '%(uploader)s - %(upload_date>%Y-%m-%d)s - %(title)s', r'(?s)(?P<meta_title>.+)'),
                    (yt_dlp.MetadataParserPP.Actions.INTERPRET, 'artist', r'(?s)(?P<meta_uploader>.+)'),
                    (yt_dlp.MetadataParserPP.Actions.INTERPRET, 'description', r'(?s)(?P<meta_comment>.+)'),
                    (yt_dlp.MetadataParserPP.Actions.INTERPRET, meta_date_format, r'(?s)(?P<meta_date>.+)')
                ]
            },
            { 
                'key': 'EmbedThumbnail',
                'already_have_thumbnail': False
            }
        ]
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
            #yt.add_post_processor(PostProcessor(), when='after_move')
            try:
                yt.download(url)
                # TODO add tags
                persistence.store_download_url(url)
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
            process_url(url, playlist.dictionary)
    else:
        # empty playlist
        print(f"Playlist is empty, nothing to do.")

def process_playlists():
    all_playlists : list[dict[str, str]] = get_playlists()
    current_pl : dict[str, str]
    for current_pl in all_playlists if all_playlists else []:
        current_playlist : Playlist = Playlist.build(current_pl)
        process_playlist(current_playlist)

def process_channel_subscription(channel : ChannelSubscription):
    channel_url : str = channel.build_url()
    print(f"Channel Identifier Type: [{channel.identifier_type.name}] Value: [{channel.identifier_value}]")
    channel : pytube.Channel = pytube.Channel(channel_url)
    print(f"Channel Name: [{channel.channel_name}] Id: [{channel.channel_id}] URL: [{channel_url}]")
    current_url : str
    for current_url in channel.video_urls:
        print(f"Found video at url [{current_url}]")
        process_url(current_url)
        
def process_channels_names():
    subscription_list : list[ChannelSubscription] = list()
    all_channel_names : list[dict[str, str]] = get_channel_names()
    current : dict[str, str]
    for current in all_channel_names if all_channel_names else []:
        current_channel : ChannelSubscription = ChannelSubscription.build_by_name(current)
        subscription_list.append(current_channel)
    process_channel_subscription_list(subscription_list)
        
def process_channel_subscription_list(lst : list[ChannelSubscription]):
    current : str
    for current in lst if lst else []:
        process_channel_subscription(current)

def store_env_playlists():
    all_playlists : list[dict[str, str]] = get_playlists()
    current_pl : dict[str, str]
    for current_pl in all_playlists if all_playlists else []:
        current_playlist : Playlist = Playlist.build(current_pl)
        persistence.store_playlist(current_playlist)

def store_env_channels():
    all_channel_names : list[dict[str, str]] = get_channel_names()
    current : dict[str, str]
    for current in all_channel_names if all_channel_names else []:
        current_channel : ChannelSubscription = ChannelSubscription.build_by_name(current)
        persistence.store_channel(current_channel)

def main():
    print(f"yt-helper, version [{app_version}]")
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
