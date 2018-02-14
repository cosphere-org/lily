# -*- coding: utf-8 -*-

import re
from unittest import TestCase

from mock import MagicMock, Mock
from django.urls import RegexURLPattern, RegexURLResolver
from django.views.generic import View
import pytest

from lily.docs.views_index_renderer import Renderer


class ViewsIndexRendererTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initfixtures(self, mocker):
        self.mocker = mocker

    #
    # get_views_index
    #
    def test_render__simple_flat_url_patterns(self):

        class HiView(View):
            def post(self):
                pass

        class YoView(View):
            def delete(self):
                pass

            delete.command_conf = {'some': 'conf'}

            def put(self):
                pass

        hi_view, yo_view = HiView.as_view(), YoView.as_view()

        renderer = Renderer([
            RegexURLPattern(r'^hi/there$', hi_view, {}, 'hi.there'),
            RegexURLPattern(r'^hiyo', yo_view, {}, 'hiyo'),
        ])

        assert renderer.render() == {
            '/hi/there': {
                'name': 'HiView',
                'path_patterns': ['^hi/there$'],
                'path_conf': {
                    'path': '/hi/there',
                    'parameters': [],
                },
            },
            '/hiyo': {
                'name': 'YoView',
                'path_patterns': ['^hiyo'],
                'path_conf': {
                    'path': '/hiyo',
                    'parameters': [],
                },
                'delete': {
                    'some': 'conf'
                },
            },
        }

    def test_crawl_views__deep_url_patterns(self):

        class HiView(View):
            def post(self):
                pass

            post.command_conf = {'post_conf': 'here it goes'}

        class WatView(View):
            def get(self):
                pass

        class YoView(View):
            def delete(self):
                pass

            delete.command_conf = {'some': 'conf'}

            def put(self):
                pass

        def resolver(regex, url_patterns):
            return MagicMock(
                regex=re.compile(regex),
                url_patterns=url_patterns,
                spec=RegexURLResolver)

        hi_view, yo_view, wat_view = (
            HiView.as_view(), YoView.as_view(), WatView.as_view())

        renderer = Renderer([
            resolver(r'^payment/$', [
                RegexURLPattern(r'^hi/there$', hi_view, {}, 'hi.there'),
                resolver(r'^now/(?P<when>\d+)/$', [
                    RegexURLPattern(r'^yes/$', yo_view, {}, 'yo'),
                    RegexURLPattern(r'^wat/$', wat_view, {}, 'wat'),
                ]),
            ]),
            RegexURLPattern('^hiyo', yo_view, {}, 'yo'),
        ])

        assert renderer.render() == {
            '/payment/hi/there': {
                'name': 'HiView',
                'path_patterns': [r'^payment/$', r'^hi/there$'],
                'path_conf': {
                    'path': '/payment/hi/there',
                    'parameters': [],
                },
                'post': {
                    'post_conf': 'here it goes',
                }
            },
            '/payment/now/{when}/yes/': {
                'name': 'YoView',
                'path_patterns': [
                    r'^payment/$', r'^now/(?P<when>\d+)/$', r'^yes/$'],
                'path_conf': {
                    'path': '/payment/now/{when}/yes/',
                    'parameters': [
                        {
                            'name': 'when',
                            'in': 'path',
                            'description': '',
                            'required': True,
                            'schema': {
                                'type': 'integer',
                            },
                        }
                    ],
                },
                'delete': {
                    'some': 'conf'
                },
            },
            '/payment/now/{when}/wat/': {
                'name': 'WatView',
                'path_patterns': [
                    r'^payment/$', r'^now/(?P<when>\d+)/$', r'^wat/$'],
                'path_conf': {
                    'path': '/payment/now/{when}/wat/',
                    'parameters': [
                        {
                            'name': 'when',
                            'in': 'path',
                            'description': '',
                            'required': True,
                            'schema': {
                                'type': 'integer',
                            },
                        }
                    ],
                },
            },
            '/hiyo': {
                'name': 'YoView',
                'path_patterns': ['^hiyo'],
                'path_conf': {
                    'path': '/hiyo',
                    'parameters': [],
                },
                'delete': {
                    'some': 'conf'
                },
            },
        }

    #
    # url_pattern_to_conf
    #
    def test_url_pattern_to_conf__returns_path_conf__no_params(self):

        renderer = Renderer(Mock())

        assert renderer.url_pattern_to_dict(
            ['^payments/', '^subscriptions/register/$']
        ) == {
            'path': '/payments/subscriptions/register/',
            'parameters': []
        }

        # -- with extra $
        assert renderer.url_pattern_to_dict(
            ['^payments/$', '^subscriptions/register/$', '^/now$']
        ) == {
            'path': '/payments/subscriptions/register/now',
            'parameters': []
        }

    def test_url_pattern_to_conf__returns_path_conf__int_param(self):

        renderer = Renderer(Mock())

        assert renderer.url_pattern_to_dict(
            ['^payments/', '^payment_cards/(?P<payment_card_id>\\d+)$']
        ) == {
            'path': '/payments/payment_cards/{payment_card_id}',
            'parameters': [
                {
                    'name': 'payment_card_id',
                    'in': 'path',
                    'description': '',
                    'required': True,
                    'schema': {
                        'type': 'integer',
                    }
                }
            ]
        }

    def test_url_pattern_to_conf__returns_path_conf__string_param(self):

        renderer = Renderer(Mock())

        assert renderer.url_pattern_to_dict([
            '^payments/',
            '^payment_cards/(?P<card_id>\\w+)/mark_as_default/$'
        ]) == {
            'path': '/payments/payment_cards/{card_id}/mark_as_default/',
            'parameters': [
                {
                    'name': 'card_id',
                    'in': 'path',
                    'description': '',
                    'required': True,
                    'schema': {
                        'type': 'string',
                    },
                }
            ]
        }

    def test_url_pattern_to_conf__returns_path_conf__many_params(self):

        renderer = Renderer(Mock())

        assert renderer.url_pattern_to_dict([
            '^cards/',
            '^(?P<card_id>\\w+)$',
            '^/with/$',
            '^(?P<messageId>\\d+)/$'
        ]) == {
            'path': '/cards/{card_id}/with/{messageId}/',
            'parameters': [
                {
                    'name': 'card_id',
                    'in': 'path',
                    'description': '',
                    'required': True,
                    'schema': {
                        'type': 'string',
                    },
                },
                {
                    'name': 'messageId',
                    'in': 'path',
                    'description': '',
                    'required': True,
                    'schema': {
                        'type': 'integer',
                    },
                },
            ]
        }
