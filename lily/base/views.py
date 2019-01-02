
import hashlib
import hmac
from datetime import datetime

from django.http import HttpResponse
from django.views.generic import View as DjangoGenericView
from django.conf import settings
from .input import Input
from .meta import Meta, Domain
from .command import command
from . import name, parsers


class command_override:  # noqa

    def __init__(
            self,
            name,
            meta=None,
            access=None,
            input=None,
            output=None,
            is_atomic=None):

        self.name = name
        self.meta = meta
        self.access = access
        self.input = input
        self.output = output
        self.is_atomic = is_atomic


class View(DjangoGenericView):

    @classmethod
    def overwrite(cls, get=None, post=None, put=None, delete=None):

        class cls_copy(cls):  # noqa
            pass

        for method_name, verb in [
                ('get', get),
                ('post', post),
                ('put', put),
                ('delete', delete)]:

            method = getattr(cls_copy, method_name, None)
            if method and verb:
                conf = method.command_conf

                setattr(
                    cls_copy,
                    method_name,
                    command(
                        name=verb.name,
                        meta=verb.meta or conf['meta'],
                        access=verb.access or conf['access'],
                        input=verb.input or conf['input'],
                        output=verb.output or conf['output'],
                        is_atomic=(
                            verb.is_atomic is not None and verb.is_atomic or
                            conf['is_atomic']),
                    )(conf['fn']))

        return cls_copy


class S3UploadSignView(View):

    class QueryParser(parsers.QueryParser):

        to_sign = parsers.CharField()

        datetime = parsers.CharField()

        def validate_datetime(self, value):
            try:
                return datetime.strptime(
                    value, r'%Y%m%dT%H%M%SZ').strftime(r'%Y%m%d')

            except ValueError:
                raise parsers.ValidationError(
                    'invalid datetime format accepted is YYYYMMDDThhmmssZ')

    @command(
        name=name.Execute('SIGN', 'S3_UPLOAD'),

        meta=Meta(
            title='Sign S3 File Upload',
            domain=Domain(id='utils', name='utils')),

        input=Input(query_parser=QueryParser),
    )
    def get(self, request):

        to_sign = request.input.query['to_sign']
        dt = request.input.query['datetime']

        signing_key = self.get_signature_key(
            settings.AWS_S3_ACCESS_KEY,
            dt,
            settings.AWS_S3_REGION,
            service='s3')

        return HttpResponse(self.get_signature(signing_key, to_sign))

    def get_signature_key(self, key, date_stamp, region, service):
        k_date = self.sign(('AWS4' + key).encode('utf-8'), date_stamp)
        k_region = self.sign(k_date, region)
        k_service = self.sign(k_region, service)
        k_signing = self.sign(k_service, 'aws4_request')

        return k_signing

    def sign(self, key, msg):

        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    def get_signature(self, signing_key, to_sign):

        return hmac.new(
            signing_key,
            to_sign.encode("utf-8"),
            hashlib.sha256).hexdigest()
