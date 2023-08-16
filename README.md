# yt-helper

Welcome to `yt-helper`, a simple YouTube helper tool for downloading from playlists and channels.  
The main purpose is make the videos I want to watch available to network shares, media servers, etc, as seamlessly as possible.  

## Links

DESCRIPTION|LINK
:---|:---
Source Code|[GitHub Repo](https://github.com/GioF71/yt-helper)
Docker Images|[Docker Hub](https://hub.docker.com/repository/docker/giof71/yt-helper)

To be completed.

## References

This project relies on the following projects:

PROJECT|LINK
:---|:---
yt-dlp|[GitHub Repo](https://github.com/yt-dlp/yt-dlp)
pytube|[GitHub Repo](https://github.com/pytube/pytube)
python-slugify|[GitHub Repo](https://github.com/un33k/python-slugify)

## Description

This portion of the documentation is still missing.

## Installation

This portion of the documentation is still missing.

## Configuration

This portion of the documentation is still missing.

### Environment Variables

VARIABLE|DESCRIPTION
:---|:---
PUID|User id of the user which will run the application, defaults to `1000`
PGID|Group id of the user which will run the application, defaults to `1000`
OUTPUT_PATH|Output directory
PLAYLIST_LIST|Comma separated list of the ids of the playlists (which must be public) to be monitored
CHANNEL_NAME_LIST|Comma separated list of the names of the channels to be monitored
MAX_RESOLUTION|Max resolution used for download, defaults to `1080`
FILE_NAME_TEMPLATE|Video file name naming template, defaults to `%(uploader)s - %(upload_date>%Y-%m-%d)s - %(title)s [%(id)s].%(ext)s`
ENABLE_LOOP|Enable loop instead of exiting after the first cycle, defaults to `1`
LOOP_WAIT_SEC|Loop wait time between iterations, in seconds, defaults to `300`
OUTPUT_FORMAT|Output format of the downloaded file, defaults to `mkv`
SLUGIFY|Transforms the file name to slugified version, defaults to `0`
PRINTABLE|Process the filename in order to strip some special characters and reduce potential issues with file name restrictions
DIRECTORY_PER_CHANNEL|If set to `1`, a directory will be created with the name of channel/uploader, defaults to `0`

Channels do not work (at least before the latest pytube update, which I have not tried yet), because the application always gets an empty list when trying to retrieve the list of video urls.

#### Playlist format

A playlist can be provided as is (just the id), or along with a start date which will be used to download videos published after the specified date. Example:

`PLAYLIST_LIST=PL12345,PL23456`

or

`PLAYLIST_LIST=PL12345:2023-08-01,PL23456`

When specifying the date, only videos published after (and including) August the 1st 2023 will be processed for playlist with id `PL12345`.

#### Channel name format

The considerations made for [Playlist Format](#playlist-format) apply, just replace the playlist id with the channel name.

### Volumes

VOLUME|DESCRIPTION
:---|:--
/db|Location for the sqlite database (will be named `yt.db`)
/downloads|Location for the downloaded files

### Examples

This portion of the documentation is still missing.
