import requests

from tempfile import NamedTemporaryFile, _TemporaryFileWrapper
from collections import defaultdict


def is_tableau(request):
    """ Checking the request for the 'tableau' parameter
        (used mostly for switching to the *TableauSerializers)
    """
    return request.GET.get('tableau', 'false').lower() == 'true'


def get_merged_items_by_fields(items, fields, seperator=', '):
    """
    For given array and fields:
    input: [{'name': 'name 1', 'age': 2}, {'name': 'name 2', 'height': 32}], ['name', 'age']
    output: {'name': 'name 1, name 2', 'age': '2, '}
    """
    data = defaultdict(list)
    for item in items:
        for field in fields:
            value = getattr(item, field, None)
            if value is not None:
                data[field].append(str(value))
    return {
        field: seperator.join(data[field])
        for field in fields
    }


class DownloadFileManager():
    """
    Convert Appeal API datetime into django datetime
    Parameters
    ----------
      url : str
    Return: TemporaryFile
    On close: Close and Delete the file
    """
    def __init__(self, url, dir='/tmp/', **kwargs):
        self.url = url
        self.downloaded_file = None
        # NamedTemporaryFile attributes
        self.named_temporary_file_args = {
            'dir': dir,
            **kwargs,
        }

    def __enter__(self) -> _TemporaryFileWrapper:
        file = NamedTemporaryFile(delete=True, **self.named_temporary_file_args)
        with requests.get(self.url, stream=True) as r:
            r.raise_for_status()
            for chunk in r.iter_content(chunk_size=8192):
                file.write(chunk)
        file.flush()
        self.downloaded_file = file
        return self.downloaded_file

    def __exit__(self, *_):
        if self.downloaded_file:
            self.downloaded_file.close()
