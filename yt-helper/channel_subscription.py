import datetime
import util

from channel_identifier_type import ChannelIdentifierType

class ChannelSubscription:
    
    # identifier_type: name or id
    # identifier_value: the name or the id of the channel
    # subscription_start: a date, format is YYYY-MM-DD

    __key_name : str = "name"
    __key_subscription_start : str = "subscription_start"

    def build_by_name(channel_dict : dict[str, str]):
        # keys
        #   id mandatory
        #   subscription_start optional
        if not ChannelSubscription.__key_name in channel_dict: raise Exception(f"Missing mandatory key {ChannelSubscription.__key_name}")
        channel_name : str = channel_dict[ChannelSubscription.__key_name]
        subscription_start : str = (channel_dict[ChannelSubscription.__key_subscription_start] 
            if ChannelSubscription.__key_subscription_start in channel_dict 
            else None)
        subscription_start_cnv = util.convert_date(subscription_start)
        return ChannelSubscription(ChannelIdentifierType.CHANNEL_NAME, channel_name, subscription_start_cnv)
    
    def build_by_name_str(channel_name : str):
        identifier_type : ChannelIdentifierType = ChannelIdentifierType.CHANNEL_NAME
        identifier_value : str = None
        subscription_start : str = None
        if ":" in channel_name:
            identifier_value, subscription_start = channel_name.split(":")
        else:
            identifier_value = channel_name
        subscription_start_cnv = util.convert_date(subscription_start)
        return ChannelSubscription(identifier_type, identifier_value, subscription_start_cnv)

    def __init__(self, 
            identifier_type : ChannelIdentifierType,
            identifier_value : str,
            subscription_start : str):
        self.__identifierType : ChannelIdentifierType = identifier_type
        self.__identifier_value : str = identifier_value
        self.__subscription_start : str = subscription_start
        
    @property
    def identifier_type(self) -> ChannelIdentifierType: return self.__identifierType
    
    @property   
    def identifier_value(self) -> str: return self.__identifier_value
    
    @property   
    def subscription_start(self) -> str: return self.__subscription_start
    
    def build_url(self):
        if self.identifier_type == ChannelIdentifierType.CHANNEL_NAME:
            return f"https://www.youtube.com/c/{self.identifier_value}"
        elif self.identifier_type == ChannelIdentifierType.CHANNEL_ID:
            return f"https://www.youtube.com/channel/{self.identifier_value}"
        else:
            raise Exception(f"Invalid identifier type: [{self.identifier_type}]")
