from config import Config
from config_key import ConfigKey, get_config_key_by_name

import os

class DefaultConfig(Config):

    def __init__(self):
        pass

    def __getenv_clean(self, env_name : str, env_default : any = None) -> any:
        value : any = os.getenv(env_name)
        if not value: value = env_default
        if isinstance(value, str) and len(value) == 0: value = env_default
        return value
    
    def get_value(self, var_name : str) -> str:
        return self.__getenv_clean(
            env_name = var_name, 
            env_default = get_config_key_by_name(var_name).default_value)

    def get_max_resolution(self) -> str: 
        return self.get_value(ConfigKey.MAX_RESOLUTION.key_name)
    
    def get_output_format(self) -> str:
        return self.get_value(ConfigKey.OUTPUT_FORMAT.key_name)

    def get_file_name_template(self) -> str:
        return self.get_value(ConfigKey.FILE_NAME_TEMPLATE.key_name)

    def get_output_path(self) -> str:
        return self.get_value(ConfigKey.OUTPUT_PATH.key_name)

    def get_enable_loop(self) -> bool:
        return self.get_value(ConfigKey.ENABLE_LOOP.key_name) == "1"

    def get_loop_wait_sec(self) -> int:
        return int(self.get_value(ConfigKey.LOOP_WAIT_SEC.key_name))

    def get_slugify(self) -> bool:
        return self.get_value(ConfigKey.SLUGIFY.key_name) == "1"

    def get_directory_per_channel(self) -> bool:
        return self.get_value(ConfigKey.DIRECTORY_PER_CHANNEL.key_name) == "1"
    
    def get_full_date_format(self) -> bool:
        return self.get_value(ConfigKey.FULL_DATE_FORMAT.key_name) == "1"
