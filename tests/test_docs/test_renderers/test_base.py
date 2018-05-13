# -*- coding: utf-8 -*-

from unittest import TestCase

from mock import Mock
from django.urls import re_path, include
from django.views.generic import View
import pytest

from lily.docs.renderers.base import BaseRenderer


class BaseRendererTestCase(TestCase):

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

        renderer = BaseRenderer([
            re_path(r'^hi/there$', hi_view, name='hi.there'),
            re_path(r'^hiyo', yo_view, name='hiyo'),
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

        hi_view, yo_view, wat_view = (
            HiView.as_view(), YoView.as_view(), WatView.as_view())

        renderer = BaseRenderer([
            re_path(r'^payment/$', include([
                re_path(r'^hi/there$', hi_view, 'hi.there'),
                re_path(r'^now/(?P<when>\d+)/$', include([
                    re_path(r'^yes/$', yo_view, 'yo'),
                    re_path(r'^wat/$', wat_view, 'wat'),
                ])),
            ])),
            re_path('^hiyo', yo_view, 'yo'),
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
                            'description': '',
                            'type': 'integer',
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
                            'description': '',
                            'type': 'integer',
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

        renderer = BaseRenderer(Mock())

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

        renderer = BaseRenderer(Mock())

        assert renderer.url_pattern_to_dict(
            ['^payments/', '^payment_cards/(?P<payment_card_id>\\d+)$']
        ) == {
            'path': '/payments/payment_cards/{payment_card_id}',
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
            'parameters': [
                {
                    'name': 'card_id',
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
