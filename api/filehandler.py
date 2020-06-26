import logging
import os


class MakeFileHandler(logging.FileHandler):
    """https://stackoverflow.com/questions/20666764/python-logging-how-to-ensure-logfile-directory-is-created"""

    def __init__(self, filename, mode='a', encoding=None, delay=0):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        logging.FileHandler.__init__(self, filename, mode, encoding, delay)
