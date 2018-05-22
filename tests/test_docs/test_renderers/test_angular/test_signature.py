# -*- coding: utf-8 -*-

from django.test import TestCase

from lily.docs.renderers.angular.signature import Signature


class Req:

    def __init__(self, name):
        self.name = name


class SignatureTestCase(TestCase):

    #
    # INPUT
    #
    def test_input__nothing(self):

        s = Signature(path='/cards', path_parameters=[])

        assert s.input == ''

    def test_input__path_parameters(self):

        # -- single parameter
        s = Signature(
            path='/cards/{card_id}',
            path_parameters=[{'name': 'card_id', 'type': int}])

        assert s.input == 'cardId: number'

        # -- multiple parameters
        s = Signature(
            path='/cards/{card_id}',
            path_parameters=[
                {'name': 'card_id', 'type': int},
                {'name': 'user_id', 'type': str},
                {'name': 'name', 'type': str},
            ])

        assert s.input == 'cardId: number, userId: string, name: string'

    def test_input__query_params(self):

        s = Signature(
            path='/cards/',
            path_parameters=[],
            request_query=Req(name='ReadCardRequestQuery'))

        assert s.input == 'params: ReadCardRequestQuery'

    def test_input__path_parameters_and_query_params(self):

        s = Signature(
            path='/cards/{card_id}/users/{user_id}',
            path_parameters=[
                {'name': 'card_id', 'type': int},
                {'name': 'user_id', 'type': str},
            ],
            request_query=Req(name='ReadCardRequestQuery'))

        assert s.input == (
            'cardId: number, userId: string, params: ReadCardRequestQuery')

    def test_input__body_params(self):

        s = Signature(
            path='/paths/',
            path_parameters=[],
            request_body=Req(name='ReadCardRequestBody'))

        assert s.input == 'body: ReadCardRequestBody'

    def test_input__path_parameters_and_body_params(self):

        s = Signature(
            path='/cards/{card_id}/users/{user_id}',
            path_parameters=[
                {'name': 'card_id', 'type': int},
                {'name': 'user_id', 'type': str},
            ],
            request_body=Req(name='ReadCardRequestBody'))

        assert s.input == (
            'cardId: number, userId: string, body: ReadCardRequestBody')

    #
    # CALL_ARGS
    #
    def test_call_args__nothing(self):

        s = Signature(path='/cards', path_parameters=[])

        assert s.call_args == "'/cards'"

    def test_call_args__path_parameters(self):

        # -- single parameter
        s = Signature(
            path='/cards/{card_id}',
            path_parameters=[{'name': 'card_id', 'type': int}])

        assert s.call_args == '`/cards/${cardId}`'

        # -- multiple parameters
        s = Signature(
            path='/cards/{card_id}/{name}/users/{user_id}',
            path_parameters=[
                {'name': 'card_id', 'type': int},
                {'name': 'user_id', 'type': str},
                {'name': 'name', 'type': str},
            ])

        assert s.call_args == (
            '`/cards/${cardId}/${name}/users/${userId}`')

    def test_call_args__query_params(self):

        s = Signature(
            path='/paths/',
            path_parameters=[],
            request_query=Req(name='ReadPathRequestQuery'))

        assert s.call_args == (
            "'/paths/', { params }")

    def test_call_args__path_parameters_and_query_params(self):

        s = Signature(
            path='/paths/{path_id}/users/{user_id}',
            path_parameters=[
                {'name': 'path_id', 'type': int},
                {'name': 'user_id', 'type': str},
            ],
            request_query=Req(name='ReadPathRequestQuery'))

        assert s.call_args == (
            '`/paths/${pathId}/users/${userId}`, { params }')

    def test_call_args__body_params(self):

        s = Signature(
            path='/cards/',
            path_parameters=[],
            request_body=Req(name='ReadCardRequestBody'))

        assert s.call_args == "'/cards/', body"

    def test_call_args__path_parameters_and_body_params(self):

        s = Signature(
            path='/cards/{card_id}/users/{user_id}',
            path_parameters=[
                {'name': 'card_id', 'type': int},
                {'name': 'user_id', 'type': str},
            ],
            request_body=Req(name='ReadCardRequestBody'))

        assert s.call_args == '`/cards/${cardId}/users/${userId}`, body'
