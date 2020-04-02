
from unittest import TestCase
from unittest.mock import Mock

from django.urls import re_path, include
import pytest

from lily.entrypoint.base import BaseRenderer
from lily.base.command import HTTPCommands
from lily.base.events import EventFactory


class BaseRendererTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initfixtures(self, mocker):
        self.mocker = mocker

    #
    # RENDER
    #
    def test_render__simple_flat_url_patterns(self):

        class HiCommands(HTTPCommands):
            def post(self):
                pass

            post.command_conf = {
                'name': 'Hi',
                'some': 'hi.conf',
            }

        class HelloCommands(HTTPCommands):
            def delete(self):
                pass

            delete.command_conf = {
                'name': 'Hello',
                'some': 'hello.conf',
            }

        hi_cmds, hello_cmds = HiCommands.as_view(), HelloCommands.as_view()

        renderer = BaseRenderer([
            re_path(r'^hi/there$', hi_cmds, name='hi.there'),
            re_path(r'^hiyo', hello_cmds, name='hiyo'),
        ])

        assert renderer.render() == {
            'Hi': {
                'method': 'POST',
                'path_conf': {
                    'path': '/hi/there',
                    'pattern': r'/hi/there',
                    'parameters': [],
                },
                'name': 'Hi',
                'some': 'hi.conf',
            },
            'Hello': {
                'method': 'DELETE',
                'path_conf': {
                    'path': '/hiyo',
                    'pattern': '/hiyo',
                    'parameters': [],
                },
                'name': 'Hello',
                'some': 'hello.conf',
            },
        }

    def test_render__same_path_many_commands(self):

        class HiCommands(HTTPCommands):
            def post(self):
                pass

            post.command_conf = {
                'name': 'Hi',
                'some': 'hi.conf',
            }

            def delete(self):
                pass

            delete.command_conf = {
                'name': 'Hello',
                'some': 'hello.conf',
            }

        hi_cmds = HiCommands.as_view()

        renderer = BaseRenderer([
            re_path(r'^hi/there$', hi_cmds, name='hi.there'),
        ])

        assert renderer.render() == {
            'Hi': {
                'method': 'POST',
                'path_conf': {
                    'path': '/hi/there',
                    'pattern': r'/hi/there',
                    'parameters': [],
                },
                'name': 'Hi',
                'some': 'hi.conf',
            },
            'Hello': {
                'method': 'DELETE',
                'path_conf': {
                    'path': '/hi/there',
                    'pattern': r'/hi/there',
                    'parameters': [],
                },
                'name': 'Hello',
                'some': 'hello.conf',
            },
        }

    def test_render__command_belongs_to_many_paths_error(self):

        class HiCommands(HTTPCommands):
            def post(self):
                pass

            post.command_conf = {
                'name': 'Hi',
                'some': 'hi.conf',
            }

        hi_cmds = HiCommands.as_view()

        renderer = BaseRenderer([
            re_path(r'^hi/there$', hi_cmds, name='hi.there'),
            re_path(r'^hello/there$', hi_cmds, name='hello.there'),
        ])

        with pytest.raises(EventFactory.ServerError) as e:
            renderer.render()

        assert e.value.event == 'VIEWS_BELONGING_TO_MULTIPLE_PATHS_DETECTED'
        assert e.value.data == {
            '@event': 'VIEWS_BELONGING_TO_MULTIPLE_PATHS_DETECTED',
            '@type': 'error',
            'duplicates': ['HiCommands'],
        }

    def test_render__not_lily_compatible_cmds(self):

        class HiCommands(HTTPCommands):
            def post(self):
                pass

        renderer = BaseRenderer([
            re_path(r'^hi/there$', HiCommands.as_view(), name='hi.there'),
        ])

        with pytest.raises(EventFactory.BrokenRequest) as e:
            renderer.render()

        assert e.value.data == {
            '@event': 'NOT_LILY_COMPATIBLE_VIEW_DETECTED',
            '@type': 'error',
            'name': 'HiCommands',
        }

    def test_render__duplicated_command(self):

        class HiCommands(HTTPCommands):

            def post(self):
                pass

            post.command_conf = {
                'name': 'HI',
                'some': 'hi.conf',
            }

        class HelloCommands(HTTPCommands):

            def delete(self):
                pass

            delete.command_conf = {
                'name': 'HI',
                'some': 'hello.conf',
            }

        renderer = BaseRenderer([
            re_path(r'^root/hi$', HiCommands.as_view(), name='hi'),

            re_path(r'^root/hello$', HelloCommands.as_view(), name='hello'),
        ])

        with pytest.raises(EventFactory.BrokenRequest) as e:
            renderer.render()

        assert e.value.data == {
            '@event': 'DUPLICATED_COMMAND_DETECTED',
            '@type': 'error',
            'command_name': 'HI',
            'duplicate_command': {
                'path': '/root/hello',
                'method': 'DELETE',
            },
            'existing_command': {
                'path': '/root/hi',
                'method': 'POST',
            },
        }

    #
    # CRAWL_VIEWS
    #
    def test_crawl_commands__deep_url_patterns(self):

        class HiCommands(HTTPCommands):
            def post(self):
                pass

            post.command_conf = {
                'name': 'Hi',
                'conf': 'hi',
            }

        class WatCommands(HTTPCommands):
            def get(self):
                pass

            get.command_conf = {
                'name': 'Wat',
                'conf.wat': 'wat',
            }

        class YoCommands(HTTPCommands):
            def delete(self):
                pass

            delete.command_conf = {
                'name': 'Yo',
                'conf': 'yo',
            }

        hi_cmds, yo_cmds, wat_cmds = (
            HiCommands.as_view(), YoCommands.as_view(), WatCommands.as_view())

        renderer = BaseRenderer([
            re_path(r'^payment/$', include([
                re_path(r'^hi/there$', hi_cmds, 'hi.there'),
                re_path(r'^now/(?P<when>\d+)/$', include([
                    re_path(r'^yes/$', yo_cmds, 'yo'),
                    re_path(r'^wat/$', wat_cmds, 'wat'),
                ])),
            ])),
        ])

        assert renderer.render() == {
            'Hi': {
                'name': 'Hi',
                'method': 'POST',
                'path_conf': {
                    'path': '/payment/hi/there',
                    'pattern': r'/payment/hi/there',
                    'parameters': [],
                },
                'conf': 'hi',
            },
            'Yo': {
                'name': 'Yo',
                'method': 'DELETE',
                'path_conf': {
                    'path': '/payment/now/{when}/yes/',
                    'pattern': r'/payment/now/(?P<when>\d+)/yes/',
                    'parameters': [
                        {
                            'name': 'when',
                            'description': '',
                            'type': 'integer',
                        }
                    ],
                },
                'conf': 'yo',
            },
            'Wat': {
                'name': 'Wat',
                'method': 'GET',
                'path_conf': {
                    'path': '/payment/now/{when}/wat/',
                    'pattern': r'/payment/now/(?P<when>\d+)/wat/',
                    'parameters': [
                        {
                            'name': 'when',
                            'description': '',
                            'type': 'integer',
                        }
                    ],
                },
                'conf.wat': 'wat',
            },
        }

    #
    # url_pattern_to_conf
    #
    def test_url_pattern_to_conf__returns_path_conf__no_params(self):

        renderer = BaseRenderer(Mock())

        assert renderer.url_pattern_to_dict(
            ['^payments/', '^subscriptions/register/$']
        ) == {
            'path': '/payments/subscriptions/register/',
            'pattern': '/payments/subscriptions/register/',
            'parameters': []
        }

        # -- with extra $
        assert renderer.url_pattern_to_dict(
            ['^payments/$', '^subscriptions/register/$', '^/now$']
        ) == {
            'path': '/payments/subscriptions/register/now',
            'pattern': '/payments/subscriptions/register/now',
            'parameters': []
        }

    def test_url_pattern_to_conf__returns_path_conf__int_param(self):

        renderer = BaseRenderer(Mock())

        assert renderer.url_pattern_to_dict(
            ['^payments/', '^payment_cards/(?P<payment_card_id>\\d+)$']
        ) == {
            'path': '/payments/payment_cards/{payment_card_id}',
            'pattern': '/payments/payment_cards/(?P<payment_card_id>\\d+)',
            'parameters': [
                {
                    'name': 'payment_card_id',
                    'description': '',
                    'type': 'integer',
                }
            ]
        }

    def test_url_pattern_to_conf__returns_path_conf__string_param(self):

        renderer = BaseRenderer(Mock())

        assert renderer.url_pattern_to_dict([
            '^payments/',
            '^payment_cards/(?P<card_id>\\w+)/mark_as_default/$'
        ]) == {
            'path': '/payments/payment_cards/{card_id}/mark_as_default/',
            'pattern': (
                '/payments/payment_cards/(?P<card_id>\\w+)/mark_as_default/'),
            'parameters': [
                {
                    'name': 'card_id',
                    'description': '',
                    'type': 'string',
                }
            ]
        }

    def test_url_pattern_to_conf__returns_path_conf__complex_string_param(
            self):

        renderer = BaseRenderer(Mock())

        result = renderer.url_pattern_to_dict([
            '^/mediaitems/uploads/sign/'
            '(?P<upload_file_properties>[\\w\\=\\+\\/]+)',
        ])
        assert result == {
            'path': '/mediaitems/uploads/sign/{upload_file_properties}',
            'pattern': (
                '/mediaitems/uploads/sign/'
                '(?P<upload_file_properties>[\\w\\=\\+\\/]+)'),
            'parameters': [
                {
                    'name': 'upload_file_properties',
                    'description': '',
                    'type': 'string',
                }
            ]
        }

    def test_url_pattern_to_conf__returns_path_conf__many_params(self):

        renderer = BaseRenderer(Mock())

        assert renderer.url_pattern_to_dict([
            '^cards/',
            '^(?P<card_id>\\w+)$',
            '^/with/$',
            '^(?P<messageId>\\d+)/$'
        ]) == {
            'path': '/cards/{card_id}/with/{messageId}/',
            'pattern': (
                '/cards/(?P<card_id>\\w+)/with/(?P<messageId>\\d+)/'),
            'parameters': [
                {
                    'name': 'card_id',
                    'description': '',
                    'type': 'string',
                },
                {
                    'name': 'messageId',
                    'description': '',
                    'type': 'integer',
                },
            ]
        }
