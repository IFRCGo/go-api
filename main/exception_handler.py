import sentry_sdk

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


standard_error_string = (
    'Something unexpected has occured. '
    'Please contact an admin to fix this issue.'
)


def custom_exception_handler(exc, context):
    # Default exception handler
    response = exception_handler(exc, context)

    # For 500 errors, we create new response and add extra attributes to sentry
    if not response:
        request = context.get('request')
        if request and request.user and request.user.id:
            with sentry_sdk.configure_scope() as scope:
                scope.user = {
                    'id': request.user.id,
                    'email': request.user.email,
                }
                scope.set_extra('is_superuser', request.user.is_superuser)
        sentry_sdk.capture_exception()
        response_data = {
            'errors': {
                'non_field_errors': [standard_error_string]
            },
        }
        response = Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return response