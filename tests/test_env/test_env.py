
import os
from unittest import TestCase

from lily.env import env
from lily.base.events import EventFactory


class EnvParserTestCase(TestCase):

    def setUp(self):

        try:
            del os.environ['SECRET_KEY']
            del os.environ['IS_IMPORTANT']
            del os.environ['AWS_URL']
            del os.environ['NUMBER_OF_WORKERS']

        except KeyError:
            pass

    def test_parse(self):

        class MyEnvParser(env.EnvParser):

            secret_key = env.CharField()

            is_important = env.BooleanField()

            aws_url = env.URLField()

            number_of_workers = env.IntegerField()

        os.environ['SECRET_KEY'] = 'secret.whatever'
        os.environ['IS_IMPORTANT'] = 'true'
        os.environ['AWS_URL'] = 'http://hello.word.org'
        os.environ['NUMBER_OF_WORKERS'] = '113'

        e = MyEnvParser().parse()

        assert e.secret_key == 'secret.whatever'
        assert e.is_important is True
        assert e.aws_url == 'http://hello.word.org'
        assert e.number_of_workers == 113

    def test_parse__optional_with_defaults(self):

        class MyEnvParser(env.EnvParser):

            secret_key = env.CharField(required=False, default='hello')

            is_important = env.BooleanField(required=False, default=False)

            aws_url = env.URLField(required=False, default='http://hi.pl')

            number_of_workers = env.IntegerField(required=False, default=12)

        e = MyEnvParser().parse()

        assert e.secret_key == 'hello'
        assert e.is_important is False
        assert e.aws_url == 'http://hi.pl'
        assert e.number_of_workers == 12

    def test_parse__optional_without_defaults(self):

        class MyEnvParser(env.EnvParser):

            secret_key = env.CharField(required=False, allow_null=True)

            is_important = env.NullBooleanField(required=False)

            aws_url = env.URLField(required=False, allow_null=True)

            number_of_workers = env.IntegerField(
                required=False, allow_null=True)

        e = MyEnvParser().parse()

        assert e.secret_key is None
        assert e.is_important is None
        assert e.aws_url is None
        assert e.number_of_workers is None

    def test_parse__validation_errors(self):

        class MyEnvParser(env.EnvParser):

            secret_key = env.CharField(max_length=12)

            is_important = env.BooleanField()

            aws_url = env.URLField()

            number_of_workers = env.IntegerField()

        os.environ['SECRET_KEY'] = 'secret.whatever'
        os.environ['IS_IMPORTANT'] = 'whatever'
        os.environ['AWS_URL'] = 'not.url'
        os.environ['NUMBER_OF_WORKERS'] = 'not.number'

        try:
            MyEnvParser().parse()

        except EventFactory.BrokenRequest as e:
            assert e.data == {
                '@event': 'ENV_DID_NOT_VALIDATE',
                '@type': 'error',
                'user_id': None,
                'errors': {
                    'secret_key': [
                        'Ensure this field has no more than 12 characters.'],
                    'is_important': ['"whatever" is not a valid boolean.'],
                    'aws_url': ['Enter a valid URL.'],
                    'number_of_workers': ['A valid integer is required.']
                },
            }

        else:
            raise AssertionError('should raise exception')
