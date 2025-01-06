import os
import json
import uuid
import requests
import logging
from datetime import timedelta

from django.utils.deconstruct import deconstructible
from django.conf import settings

from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError

logger = logging.getLogger('django.server')

@deconstructible
class PreprocessUploadPath(object):
    def __init__(self, path_getter, filename_prefix='', use_uuid_name=False):
        self.path_getter = path_getter
        self.filename_prefix = filename_prefix
        self.use_uuid_name = use_uuid_name

    def __call__(self, instance, filename):
        prefix = None
        _filename = filename

        if isinstance(self.filename_prefix, str):
            prefix = f'{ self.filename_prefix }_'
        elif callable(self.filename_prefix):
            prefix = f'{ self.filename_prefix(instance) }_'

        if self.use_uuid_name:
            _, extension = os.path.splitext(_filename)

            _filename = f'{ uuid.uuid4() }{ extension }'

        return f'{ os.path.join(self.path_getter(instance)) }/{ prefix }{ _filename }'


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    if isinstance(exc, ValidationError):
        non_field_errors = exc.detail.get('non_field_errors', None)

        if non_field_errors:
            response.data['detail'] = non_field_errors[0]
            del response.data['non_field_errors']

            logger.error(response.data['detail'])
        else:
            response.data = dict()
            error_fields = dict()

            for [ key, value ] in exc.detail.items():
                error_fields[key] = value

            response.data['detail'] = 'INVALID_PARAMETERS'
            response.data['fields'] = error_fields

            logger.error(response.data['fields'])

    return response

def get_week_no(date):
    first_day = date.replace(day=1)

    if first_day.weekday() == 6:
        origin = first_day
    elif first_day.weekday() < 3:
        origin = first_day - timedelta(days=first_day.weekday() + 1)
    else:
        origin = first_day + timedelta(days=6-first_day.weekday())

    return ((date - origin).days // 7) + 1
