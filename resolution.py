class Resolution:

    def __init__(self, res : str):
        self.__mode : str = res[len(res) - 1]
        self.__height : int = int(res[0:len(res) - 1])

    def get_mode(self): return self.__mode
    def get_height(self): return self.__height

