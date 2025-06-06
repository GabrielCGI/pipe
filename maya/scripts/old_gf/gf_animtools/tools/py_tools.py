import math
import re
import time


def camelCaseSplit(value):
    matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', value)
    return [m.group(0) for m in matches]


def listToCamelCase(datas):
    return ''.join([v.capitalize() for v in datas if v != ''])