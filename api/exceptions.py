from rest_framework.exceptions import APIException
from rest_framework.status import HTTP_400_BAD_REQUEST


class BadRequest(APIException):
    status_code = HTTP_400_BAD_REQUEST
    default_code = "Bad request"

    def __init__(self, detail):
        self.detail = detail
