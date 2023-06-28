import logging
import sentry_sdk
import logging

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django_read_only import DjangoReadOnlyError

logger = logging.getLogger(__name__)

logger = logging.getLogger('api')

standard_error_string = (
    'Something unexpected has occured. '
    'Please contact an admin to fix this issue.'
)

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    # Default exception handler
    response = exception_handler(exc, context)

    # For 500 errors, we create new response and add extra attributes to sentry
    if not response:
        # Expected ReadOnlyError
        if type(exc) == DjangoReadOnlyError:
            response_data = {
                'errors': {
                    'non_field_errors': ['We are in maintenance mode, come back a bit later – site is in read only mode']
                },
            }
        else:
            # Other 500 errors
            request = context.get('request')
            if request and request.user and request.user.id:
                with sentry_sdk.configure_scope() as scope:
                    scope.user = {
                        'id': request.user.id,
                        'email': request.user.email,
                    }
                    scope.set_extra('is_superuser', request.user.is_superuser)
            sentry_sdk.capture_exception()
            logger.error('500 error', exc_info=True)
            response_data = {
                'errors': {
                    'non_field_errors': [standard_error_string]
                },
            }
            logger.error(
                '{}.{}'.format(type(exc).__module__, type(exc).__name__),
                exc_info=True,
                extra={'request': context.get('request')},
            )
        response = Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return response
