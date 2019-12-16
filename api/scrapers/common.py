import json
from datetime import timedelta


class DataNotFoundException(Exception):
    def __init__(self, sector):
        message = 'Data not found for {}'.format(sector)
        super().__init__(message)


def print_error(error):
    print('*' * 11, error, '*' * 11)


def text_to_file(file, text):
    with open(file, 'w') as fp:
        fp.write(text)


def json_preety(object):
    return json.dumps(object, sort_keys=True, indent=4, separators=(',', ': '))


def clean_value(value):
    _value = value.strip()
    if _value in ['Not', 'Not available', '']:
        return None
    """
    try:
        return int(_value)
    except ValueError:
        pass
    """
    return _value


def seconds_to_human_readable(seconds):
    sec = timedelta(seconds=seconds)
    return str(sec)
