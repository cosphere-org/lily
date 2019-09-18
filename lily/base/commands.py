
import hashlib
import hmac
from datetime import datetime

from django.http import HttpResponse
from django.conf import settings
from .input import Input
from .meta import Meta, Domain
from .command import command, HTTPCommands
from . import name, parsers


# FIXME: to be removed!!!!!
# it's not needed any more!!!! --> to cosphere specific
# it's still used in the game-service
class S3UploadSignCommands(HTTPCommands):

    class QueryParser(parsers.Parser):

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
