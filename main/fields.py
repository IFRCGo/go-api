import datetime
import posixpath
from uuid import uuid4

from django.core.files.utils import validate_file_name
from django.db.models.fields.files import FileField


class SecureFileField(FileField):
    def generate_filename(self, instance, filename):
        """
        Apply (if callable) or prepend (if a string) upload_to to the filename,
        then delegate further processing of the name to the storage backend.
        Until the storage layer, all file paths are expected to be Unix style
        (with forward slashes).
        Add random uuid in the file name.
        """
        extension = filename.split(".")[-1]
        old_file_name = filename.split(".")[0]
        # Create a unique filename using uuid4
        filename = f"{old_file_name}-{uuid4().hex}.{extension}"

        if callable(self.upload_to):
            filename = self.upload_to(instance, filename)
        else:
            dirname = datetime.datetime.now().strftime(str(self.upload_to))
            filename = posixpath.join(dirname, filename)
        filename = validate_file_name(filename, allow_relative_path=True)

        return self.storage.generate_filename(filename)
