from django.core.exceptions import ValidationError
from magic import Magic


def validate_file_type(file, raise_exception=True) -> bool:
    """
    This function validates a file object based on a disallowed mimetype.
    Arg:
        file: The file object to validate.
    Raises:
        ValidationError: If the file type is disallowed.
    """
    if file:
        mime = Magic(mime=True)
        file_type = mime.from_buffer(file.read(1024))
        file.seek(0)  # Read a portion for analysis, then reset file pointer
        if file_type == "image/svg+xml":
            if raise_exception:
                raise ValidationError("SVG image upload is not allowed. Please use another image type.")
            return False
        return True
