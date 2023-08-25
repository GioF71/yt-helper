from enum import Enum

class ConfigKey(Enum):
    
    MAX_RESOLUTION = 0, "MAX_RESOLUTION", "1080"
    OUTPUT_FORMAT = 1, "OUTPUT_FORMAT", "mkv"
    FILE_NAME_TEMPLATE = 2, "FILE_NAME_TEMPLATE", '%(uploader)s - %(upload_date>%Y-%m-%d)s - %(title)s [%(id)s].%(ext)s'
    OUTPUT_PATH = 3, "OUTPUT_PATH", "."
    ENABLE_LOOP = 4, "ENABLE_LOOP", "1"
    LOOP_WAIT_SEC = 5, "LOOP_WAIT_SEC", "300"
    SLUGIFY = 6, "SLUGIFY", "0"
    DIRECTORY_PER_CHANNEL = 7, "DIRECTORY_PER_CHANNEL", "0"
        
    def __init__(self, 
            num : int, 
            key_name : str,
            default_value : str):
        self.num : int = num
        self.__key_name : str = key_name
        self.__default_value : str = default_value
    
    @property
    def key_name(self) -> str:
        return self.__key_name

    @property
    def default_value(self) -> str:
        return self.__default_value

def get_config_key_by_name(key_name : str) -> ConfigKey:
    for _, member in ConfigKey.__members__.items():
        if key_name == member.key_name:
            return member
    raise Exception(f"get_config_key_by_name with {key_name} NOT found")


# duplicate check
name_checker_set : set[str] = set()
id_checker_set : set[int] = set()
for v in ConfigKey:
    if v.key_name in name_checker_set:
        raise Exception(f"Duplicated name [{v.key_name}]")
    if v.value[0] in id_checker_set:
        raise Exception(f"Duplicated id [{v.value[0]}]")
    name_checker_set.add(v.key_name)
    id_checker_set.add(v.value[0])