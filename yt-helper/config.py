class Config:
    
    def get_value(self, var_name : str) -> str: pass

    def get_max_resolution(self) -> str: pass
    def get_output_format(self) -> str: pass
    def get_file_name_template(self) -> str: pass
    def get_output_path(self) -> str: pass
    def get_enable_loop(self) -> bool: pass
    def get_loop_wait_sec(self) -> int: pass
    def get_slugify(self) -> bool: pass
    def get_directory_per_channel(self) -> bool: pass