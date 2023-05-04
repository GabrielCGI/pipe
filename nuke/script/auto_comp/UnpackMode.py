class UnpackMode:
    def __init__(self, name, shuffle_mode, merge_mode):
        self.__name = name
        self.__shuffle_mode = shuffle_mode
        self.__merge_mode = merge_mode

    def get_name(self):
        return self.__name

    def get_shuffle_mode(self):
        return self.__shuffle_mode

    def get_merge_mode(self):
        return self.__merge_mode
