from common.utils import *


class Preset:

    @classmethod
    def create_from_existant(cls, preset_dict):
        """
        Create a preset from a preset_dict retrieved
        :param preset_dict
        :return: preset
        """
        name = preset_dict["name"]
        del preset_dict["name"]
        if "active" in preset_dict:
            active = preset_dict["active"]
            del preset_dict["active"]
        else:
            active = False
        return cls(name, preset_dict, active)

    def __init__(self, name, fields=None, fields_saved = None, active=False):
        """
        Constructor
        :param name
        :param fields
        :param fields_saved
        :param active
        """
        self.__name = name.replace(" ", "_")
        self.__fields = {} if fields is None or type(fields) is not dict else fields
        self.__fields_saved = {} if fields_saved is None or type(fields_saved) is not dict else fields_saved
        self.__active = active

    # ###################################################### dict ######################################################

    def set(self, part_name, key, value):
        """
        Set an attribute
        :param part_name
        :param key
        :param value
        :return:
        """
        if part_name not in self.__fields:
            self.__fields[part_name] = {}
        self.__fields[part_name][key] = value

    def get(self, part_name, key):
        """
        Get an attribute
        :param part_name
        :param key
        :return: attribute value
        """
        return self.__fields[part_name][key]

    def contains(self, part_name, key):
        """
        Check if preset has a field
        :param part_name
        :param key
        :return: contains
        """
        return part_name in self.__fields and key in self.__fields[part_name]

    def keys(self):
        """
        Getter of the keys
        :return: keys
        """
        return self.__fields.keys()

    def values(self):
        """
        Getter of the values
        :return: values
        """
        return self.__fields.values()

    def items(self):
        """
        Getter of the items
        :return: items
        """
        return self.__fields.items()

    # ###################################################### dict ######################################################

    def __eq__(self, other):
        """
        Equals function
        :param other
        :return: equals
        """
        return other.__name == self.__name

    def set_active(self, active):
        """
        Setter of the active state
        :param active
        :return:
        """
        self.__active = active

    def is_active(self):
        """
        Getter of the active state
        :return: active state
        """
        return self.__active

    def get_name(self):
        """
        Getter of the name
        :return: name
        """
        return self.__name

    def set_name(self, name):
        """
        Setter of the name
        :param name
        :return:
        """
        self.__name = name

    def to_preset_array(self):
        """
        Generate an array from the preset
        :return: array preset
        """
        preset_dict = self.__fields.copy()
        preset_dict["name"] = self.__name
        preset_dict["active"] = self.__active
        return preset_dict

    def filter(self, filter_dict):
        """
        Filter the preset
        :param filter_dict
        :return:
        """
        to_pop = []
        for part, fields in self.__fields.items():
            for field in fields.keys():
                item = {"part":part, "field": field}
                if item not in filter_dict:
                    to_pop.append(item)
        for item in to_pop:
            self.__fields[item["part"]].pop(item["field"])