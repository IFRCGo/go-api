from uuid import uuid4

from django.db.models.fields.files import FileField


class SecureFileField(FileField):
    def generate_filename(self, instance, filename):
        """
        Overwrites https://github.com/django/django/blob/main/django/db/models/fields/files.py#L345
        """
        # Append uuid4 path to the filename
        filename = f"{uuid4().hex}/{filename}"
        return super().generate_filename(instance, filename)  # return self.storage.generate_filename(filename)
