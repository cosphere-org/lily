# -*- coding: utf-8 -*-

from unittest import TestCase

from mock import Mock
from django.urls import re_path, include
from django.views.generic import View
import pytest

from lily.entrypoint.renderers.base import BaseRenderer
from lily.base.events import EventFactory


class BaseRendererTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initfixtures(self, mocker):
        self.mocker = mocker

    #
    # render
    #
    def test_render__simple_flat_url_patterns(self):

        class HiView(View):
            def post(self):
                pass

            post.command_conf = {
                'name': 'Hi',
                'some': 'hi.conf',
            }

        class HelloView(View):
            def delete(self):
                pass

            delete.command_conf = {
                'name': 'Hello',
                'some': 'hello.conf',
            }

        hi_view, hello_view = HiView.as_view(), HelloView.as_view()

        renderer = BaseRenderer([
            re_path(r'^hi/there$', hi_view, name='hi.there'),
            re_path(r'^hiyo', hello_view, name='hiyo'),
        ])

        assert renderer.render() == {
            'Hi': {
                'method': 'post',
                'path_conf': {
                    'path': '/hi/there',
                    'pattern': r'/hi/there',
                    'parameters': [],
                },
                'name': 'Hi',
                'some': 'hi.conf',
            },
            'Hello': {
                'method': 'delete',
                'path_conf': {
                    'path': '/hiyo',
                    'pattern': '/hiyo',
                    'parameters': [],
                },
                'name': 'Hello',
                'some': 'hello.conf',
            },
        }

    def test_crawl_views__deep_url_patterns(self):

        class HiView(View):
            def post(self):
                pass

            post.command_conf = {
                'name': 'Hi',
                'conf': 'hi',
            }

        class WatView(View):
            def get(self):
                pass

            get.command_conf = {
                'name': 'Wat',
                'conf.wat': 'wat',
            }

        class YoView(View):
            def delete(self):
                pass

            delete.command_conf = {
                'name': 'Yo',
                'conf': 'yo',
            }

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
        ])

        assert renderer.render() == {
            'Hi': {
                'name': 'Hi',
                'method': 'post',
                'path_conf': {
                    'path': '/payment/hi/there',
                    'pattern': r'/payment/hi/there',
                    'parameters': [],
                },
                'conf': 'hi',
            },
            'Yo': {
                'name': 'Yo',
                'method': 'delete',
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
                'method': 'get',
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

    def test_render__not_lily_compatible_view(self):

        class HiView(View):
            def post(self):
                pass

        renderer = BaseRenderer([
            re_path(r'^hi/there$', HiView.as_view(), name='hi.there'),
        ])

        with pytest.raises(EventFactory.BrokenRequest):
            renderer.render()

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
