#import dateutil
import datetime

class Playlist:
    
    # playlist_id: the name or the id of the channel
    # subscription_start: a date, format is YYYY-MM-DD
    __format : str = "%d-%m-%Y"
    
    def build(playlist_str : str):
        playlist_id : str = None
        subscription_start : str = None
        subscription_start_cnv : datetime = None
        if ":" in playlist_str:
            playlist_id, subscription_start = playlist_str.split(":")
        else:
            playlist_id = playlist_str
        subscription_start_cnv = Playlist.__convert_date(subscription_start)
        return Playlist(playlist_id, subscription_start_cnv)

    def __init__(self, 
            playlist_id : str,
            subscription_start : datetime = None):
        self.__playlist_id : str = playlist_id
        self.__subscription_start : datetime = subscription_start

    def __convert_date(in_date : str) -> datetime:
        if not in_date: return None
        try:
            y : str
            m : str
            d : str
            y, m, d = in_date.split("-")
            return datetime.datetime(int(y),int(m),int(d))
        except ValueError:
            raise Exception(f"Invalid date string [{in_date}], format must be YYYY-mm-dd")


    @property   
    def playlist_id(self) -> str: return self.__playlist_id
    
    @property   
    def subscription_start(self) -> datetime: return self.__subscription_start
    
    def build_url(self) -> str:
        return f"https://www.youtube.com/playlist?list={self.__playlist_id}"

    def is_publish_date_allowed(self, publish_date : datetime) -> bool:
        if not self.__subscription_start or not publish_date: return True
        return publish_date >= self.__subscription_start
