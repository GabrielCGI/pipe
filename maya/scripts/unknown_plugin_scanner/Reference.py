class Reference:
    def __init__(self, reference=None, data=None):
        self.__name = None
        self.__filepath = None
        self.__unknown_node_names = []
        if reference is not None:
            self.__name = reference.name()
            self.__filepath = reference.fileName(False, False, False)
        elif data is not None:
            self.__name = data["name"]
            self.__filepath = data["filepath"]
            self.__unknown_node_names = data["unknown_plugin_names"]

    def get_name(self):
        return self.__name

    def get_filepath(self):
        return self.__filepath

    def get_unknown_plugin_names(self):
        return self.__unknown_node_names
