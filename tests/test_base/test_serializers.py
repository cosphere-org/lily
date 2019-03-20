
from unittest.mock import Mock, call

from django.test import TestCase
from django.db import models
import pytest

from lily.base import serializers
from lily.base.events import EventFactory


class CommandLinkTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initfixtures(self, mocker):
        self.mocker = mocker

    def test_required_fields(self):

        # -- missing command_name and description and parameters
        with pytest.raises(TypeError):
            serializers.CommandLink()

        # -- missing name
        with pytest.raises(TypeError):
            serializers.CommandLink(
                description='makes it', parameters={'hi': 'there'})

    def test_arguments_are_optional(self):

        link = serializers.CommandLink(name='MAKE_IT')

        assert link.name == 'MAKE_IT'
        assert link.parameters == {}
        assert link.description is None

    def test_arguments_are_saved(self):

        link = serializers.CommandLink(
            name='MAKE_IT',
            parameters={'hi': 'there'},
            description='just make it!')

        assert link.name == 'MAKE_IT'
        assert link.parameters == {'hi': 'there'}
        assert link.description == 'just make it!'

    #
    # resolve_parameters
    #
    def test_resolve_parameters(self):
        self.mocker.patch.object(
            serializers.CommandLink, 'parse_parameter_pattern'
        ).side_effect = lambda x: {
            '$response.body#/client_id': {
                'entity': 'response',
                'prop': 'body',
                'selector': ['client_id'],
            },
            '$request.header.user_id': {
                'entity': 'request',
                'prop': 'header',
                'selector': 'user_id',
            },
        }[x]

        request = Mock(META={'HTTP_X_CS_USER_ID': '78', 'SERVER_NAME': 'yo'})
        response = {'client_id': 891}
        cl = serializers.CommandLink('HELLO', parameters={
            'client_id': '$response.body#/client_id',
            'user_id': '$request.header.user_id',
        })

        assert cl.resolve_parameters(request, response) == {
            'client_id': 891,
            'user_id': '78',
        }

    def test_resolve_parameters__with_type(self):
        self.mocker.patch.object(
            serializers.CommandLink, 'parse_parameter_pattern'
        ).side_effect = lambda x: {
            '$response.body#/client_id': {
                'entity': 'response',
                'prop': 'body',
                'selector': ['client_id'],
            },
            '$request.header.user_id': {
                'entity': 'request',
                'prop': 'header',
                'selector': 'user_id',
            },
        }[x]

        request = Mock(META={'HTTP_X_CS_USER_ID': '78', 'SERVER_NAME': 'yo'})
        response = {'client_id': 891, 'id': 12}
        cl = serializers.CommandLink('HELLO', parameters={
            'client_id': '$response.body#/client_id',
            'user_id': '$request.header.user_id',
        })

        assert cl.resolve_parameters(request, response, _type='order') == {
            'client_id': 891,
            'user_id': '78',
            'order_id': 12,
            'id': 12,
        }

    #
    # resolve
    #
    def test_resolve(self):

        self.mocker.patch.object(
            serializers,
            'COMMANDS_CONF',
            {
                'SOME_COMMAND': {
                    'name': 'SOME_COMMAND',
                    'service_base_uri': 'http://192.11.2.1:9000',
                    'method': 'post',
                    'path_conf': {
                        'path': '/payment_cards/{card_id}/something/',
                        'parameters': [
                            {
                                'name': 'card_id',
                                'in': 'path',
                                'description': None,
                                'required': True,
                                'type': 'integer'
                            },
                        ],
                    },
                    'access': {
                        'access_list': ['MENTOR'],
                        'is_private': False,
                    },
                }
            })

        cl = serializers.CommandLink(
            'SOME_COMMAND', {'card_id': '$response.body#/card_id'})

        assert cl.resolve(
            Mock(account_type='MENTOR'),
            {'card_id': 167},
            'payment_card'
        ) == {
            'name': 'SOME_COMMAND',
            'method': 'post',
            'uri': 'http://192.11.2.1:9000/payment_cards/167/something/',
        }

    def test_resolve__with_body(self):
        self.mocker.patch.object(
            serializers,
            'COMMANDS_CONF',
            {
                'SOME_COMMAND': {
                    'name': 'SOME_COMMAND',
                    'service_base_uri': 'http://192.11.2.1:9000',
                    'method': 'post',
                    'path_conf': {
                        'path': '/payment_cards/{card_id}/something/',
                        'parameters': [
                            {
                                'name': 'card_id',
                                'in': 'path',
                                'description': None,
                                'required': True,
                                'type': 'integer'
                            },
                        ],
                    },
                    'access': {
                        'access_list': ['MENTOR'],
                        'is_private': False,
                    },
                    'body': {'some': 'thing'},
                }
            })

        cl = serializers.CommandLink(
            'SOME_COMMAND', {'card_id': '$response.body#/card_id'})

        assert cl.resolve(
            Mock(account_type='MENTOR'),
            {'card_id': 167},
            'payment_card'
        ) == {
            'name': 'SOME_COMMAND',
            'method': 'post',
            'uri': 'http://192.11.2.1:9000/payment_cards/167/something/',
            'body': {'some': 'thing'},
        }

    def test_resolve__with_query(self):
        self.mocker.patch.object(
            serializers,
            'COMMANDS_CONF',
            {
                'SOME_COMMAND': {
                    'name': 'SOME_COMMAND',
                    'service_base_uri': 'http://192.11.2.1:9000',
                    'method': 'post',
                    'path_conf': {
                        'path': '/payment_cards/{card_id}/something/',
                        'parameters': [
                            {
                                'name': 'card_id',
                                'in': 'path',
                                'description': None,
                                'required': True,
                                'type': 'integer'
                            },
                        ],
                    },
                    'access': {
                        'access_list': ['MENTOR'],
                        'is_private': False,
                    },
                    'query': {'some': 'thing'},
                }
            })

        cl = serializers.CommandLink(
            'SOME_COMMAND', {'card_id': '$response.body#/card_id'})

        assert cl.resolve(
            Mock(account_type='MENTOR'),
            {'card_id': 167},
            'payment_card'
        ) == {
            'name': 'SOME_COMMAND',
            'method': 'post',
            'uri': 'http://192.11.2.1:9000/payment_cards/167/something/',
            'query': {'some': 'thing'},
        }

    def test_resolve__warning_if_link_not_completed(self):

        warning = self.mocker.patch.object(EventFactory, 'Warning')
        self.mocker.patch.object(
            serializers,
            'COMMANDS_CONF',
            {
                'SOME_COMMAND': {
                    'name': 'SOME_COMMAND',
                    'service_base_uri': 'http://192.11.2.1:9000',
                    'method': 'post',
                    'path_conf': {
                        'path': '/payment_cards/{card_id}/sth/{this_id}',
                        'parameters': [
                            {
                                'name': 'card_id',
                                'in': 'path',
                                'description': None,
                                'required': True,
                                'type': 'integer'
                            },
                            {
                                'name': 'this_id',
                                'in': 'path',
                                'description': None,
                                'required': True,
                                'type': 'integer'
                            },
                        ],
                    },
                    'access': {
                        'access_list': ['MENTOR'],
                        'is_private': False,
                    },
                }
            })

        cl = serializers.CommandLink(
            'SOME_COMMAND', {
                'card_id': '$response.body#/card_id',
                'this_id': '$response.body#/this_id',
            })
        request = Mock(account_type='MENTOR', command_name='CALLER_COMMAND')

        cl.resolve(request, {'wat_id': 167}, 'payment_card')

        assert warning.call_args_list == [
            call(
                event='MISSING_COMMAND_LINK_PARAMS_DETECTED',
                context=request,
                is_critical=True,
                data={'from': 'CALLER_COMMAND', 'to': 'SOME_COMMAND'})]

    def test_resolve__prevent_if_no_access(self):

        self.mocker.patch.object(
            serializers,
            'COMMANDS_CONF',
            {
                'SOME_COMMAND': {
                    'name': 'SOME_COMMAND',
                    'service_base_uri': 'http://192.11.2.1:9000',
                    'method': 'post',
                    'path_conf': {
                        'path': '/payment_cards/{card_id}/something/',
                        'parameters': [
                            {
                                'name': 'card_id',
                                'in': 'path',
                                'description': None,
                                'required': True,
                                'type': 'integer'
                            },
                        ],
                    },
                    'access': {
                        'access_list': ['MENTOR'],
                        'is_private': False,
                    },
                }
            })

        cl = serializers.CommandLink(
            'SOME_COMMAND', {'card_id': '$response.body#/card_id'})

        assert cl.resolve(
            Mock(account_type='LEARNER'), {'card_id': 167}, 'payment_card'
        ) == {}

    def test_resolve__allow_if_no_access_list(self):

        self.mocker.patch.object(
            serializers,
            'COMMANDS_CONF',
            {
                'SOME_COMMAND': {
                    'name': 'SOME_COMMAND',
                    'service_base_uri': 'http://192.11.2.1:9000',
                    'method': 'post',
                    'path_conf': {
                        'path': '/payment_cards/{card_id}/something/',
                        'parameters': [
                            {
                                'name': 'card_id',
                                'in': 'path',
                                'description': None,
                                'required': True,
                                'type': 'integer'
                            },
                        ],
                    },
                    'access': {
                        'access_list': None,
                        'is_private': False,
                    },
                }
            })

        cl = serializers.CommandLink(
            'SOME_COMMAND', {'card_id': '$response.body#/card_id'})

        assert cl.resolve(
            Mock(account_type='LEARNER'), {'card_id': 167}, 'payment_card'
        ) == {
            'method': 'post',
            'name': 'SOME_COMMAND',
            'uri': 'http://192.11.2.1:9000/payment_cards/167/something/',
        }

    #
    # resolve_pre_computed
    #
    def test_resolve_pre_computed__body(self):

        self.mocker.patch.object(
            serializers,
            'COMMANDS_CONF',
            {
                'SOME_COMMAND': {
                    'name': 'SOME_COMMAND',
                    'service_base_uri': 'http://192.11.2.1:9000',
                    'method': 'post',
                    'path_conf': {
                        'path': '/payment_cards/',
                        'parameters': [],
                    },
                    'access': {
                        'access_list': ['MENTOR'],
                        'is_private': False,
                    },
                    'body': {
                        '@type': 'object',
                        'value': {
                            '@type': 'integer',
                            '@required': True,
                        },
                        'order': {
                            '@type': 'object',
                            'amount': {
                                '@type': 'float',
                            }
                        },
                    }
                }
            })

        cl = serializers.CommandLink('SOME_COMMAND', {})

        assert cl.resolve_pre_computed(
            Mock(account_type='MENTOR'), {}, 'payment_card',
            body_values={
                'value': 11,
                'order.amount': 15.6,
            }
        ) == {
            'body': {
                '@type': 'object',
                'value': {
                    '@required': True,
                    '@type': 'integer',
                    '@value': 11,
                },
                'order': {
                    '@type': 'object',
                    'amount': {
                        '@type': 'float',
                        '@value': 15.6
                    }
                },
            },
            'method': 'post',
            'name': 'SOME_COMMAND',
            'uri': 'http://192.11.2.1:9000/payment_cards/',
        }

    def test_resolve_pre_computed__query(self):

        self.mocker.patch.object(
            serializers,
            'COMMANDS_CONF',
            {
                'SOME_COMMAND': {
                    'name': 'SOME_COMMAND',
                    'service_base_uri': 'http://192.11.2.1:9000',
                    'method': 'get',
                    'path_conf': {
                        'path': '/payment_cards/',
                        'parameters': [],
                    },
                    'access': {
                        'access_list': ['MENTOR'],
                        'is_private': False,
                    },
                    'query': {
                        '@type': 'object',
                        'value': {
                            '@type': 'integer',
                            '@required': True,
                        },
                        'amount': {
                            '@type': 'float',
                        },
                    }
                }
            })

        cl = serializers.CommandLink('SOME_COMMAND', {})

        assert cl.resolve_pre_computed(
            Mock(account_type='MENTOR'), {}, 'payment_card',
            query_values={
                'value': 11,
                'amount': 15.6,
            }
        ) == {
            'query': {
                '@type': 'object',
                'value': {
                    '@required': True,
                    '@type': 'integer',
                    '@value': 11,
                },
                'amount': {
                    '@type': 'float',
                    '@value': 15.6,
                },
            },
            'method': 'get',
            'name': 'SOME_COMMAND',
            'uri': 'http://192.11.2.1:9000/payment_cards/',
        }

    #
    # resolve_with_result
    #
    def test_resolve_with_result(self):
        self.mocker.patch.object(
            serializers,
            'COMMANDS_CONF',
            {
                'SOME_COMMAND': {
                    'name': 'SOME_COMMAND',
                    'service_base_uri': 'http://192.11.2.1:9000',
                    'method': 'get',
                    'path_conf': {
                        'path': '/payment_cards/',
                        'parameters': [],
                    },
                    'access': {
                        'access_list': ['MENTOR'],
                        'is_private': False,
                    }
                }
            })

        cl = serializers.CommandLink('SOME_COMMAND', {})

        assert cl.resolve_with_result(
            Mock(account_type='MENTOR'), {}, 'payment_card',
            result={'hi': 'there'}
        ) == {
            'method': 'get',
            'name': 'SOME_COMMAND',
            'uri': 'http://192.11.2.1:9000/payment_cards/',
            'result': {'hi': 'there'},
        }


@pytest.mark.parametrize(
    "pattern, expected",
    [
        # -- case 0 - field from the response's body (level 1)
        (
            '$response.body#/id',
            {
                'entity': 'response',
                'prop': 'body',
                'selector': ['id'],
            },
        ),

        # -- case 1 - field from the request's body (level 2)
        (
            '$request.body#/user/uuid',
            {
                'entity': 'request',
                'prop': 'body',
                'selector': ['user', 'uuid'],
            },
        ),

        # -- case 2 - header of the response
        (
            '$response.header.accept',
            {
                'entity': 'response',
                'prop': 'header',
                'selector': 'accept',
            },
        ),

        # -- case 3 - value from the request's path
        (
            '$request.path.client_id',
            {
                'entity': 'request',
                'prop': 'path',
                'selector': 'client_id',
            },
        ),
    ])
def test_parse_parameter_pattern(pattern, expected):

    cl = serializers.CommandLink('HI')
    assert cl.parse_parameter_pattern(pattern) == expected


#
# Test Serializers
#
class Customer(models.Model):

    name = models.CharField(max_length=100)

    age = models.IntegerField(null=True, blank=True)

    is_ready = models.BooleanField()

    class Meta:
        app_label = 'base'


class CustomerSerializer(serializers.Serializer):

    _type = 'customer'

    name = serializers.CharField(max_length=123, required=False)

    age = serializers.IntegerField(min_value=18)


class CustomerModelSerializer(serializers.ModelSerializer):

    _type = 'customer'

    class Meta:
        model = Customer
        fields = ('name', 'age')


class SerializerTestCase(TestCase):

    serializer = CustomerSerializer

    @pytest.fixture(autouse=True)
    def initfixture(self, mocker):
        self.mocker = mocker

    def test_to_internal_value(self):

        class MetaCustomer(serializers.Serializer):
            _type = 'customer'
            at__name = serializers.CharField()
            at__age = serializers.IntegerField()
            is_ready = serializers.BooleanField()

        s = MetaCustomer({
            '@name': 'George',
            '@age': 13,
            'is_ready': False,
        })

        # assert s.is_valid() is True
        assert s.data == {
            '@type': 'customer',
            '@name': 'George',
            '@age': 13,
            'is_ready': False,
        }

    def test_to_internal_value_with_instance(self):

        class WhatSerializer(serializers.Serializer):
            what = serializers.IntegerField()

        class MetaCustomer(serializers.Serializer):
            _type = 'customer'
            name = serializers.CharField()
            age = serializers.IntegerField()
            is_ready = serializers.BooleanField()
            what = WhatSerializer()

        data = {
            'name': 'George',
            'age': 13,
            'is_ready': False,
            'what': ['what'],
        }
        s = MetaCustomer(data=data)

        assert dict(s.to_internal_value(data)) == {
            'name': 'George',
            'age': 13,
            'is_ready': False,
            'what': ['what'],
        }

    def test_to_representation__without_command_links(self):

        p = Customer(name='John', age=81)

        assert self.serializer(
            context={'request': Mock(), 'command_name': 'ACT_NOW'}
        ).to_representation(p) == {
            '@type': 'customer',
            'age': 81,
            'name': 'John',
        }

    def test_to_representation__with_command_links(self):

        p = Customer(name='John', age=81)
        resolved_commands = [
            {
                'name': 'MARK_IT',
                'method': 'GET',
                'uri': 'http://localhost/mark.it',
            },
            {
                'name': 'REMOVE_IT',
                'method': 'GET',
                'uri': 'http://localhost/remove.it',
            },
        ]

        def resolve(*args, **kwargs):
            return resolved_commands.pop(0)

        self.mocker.patch.object(
            serializers.CommandLink, 'resolve').side_effect = resolve
        self.serializer._command_links = [
            serializers.CommandLink(
                name='MARK_IT', description='marking'),

            serializers.CommandLink(
                name='REMOVE_IT', description='removing'),
        ]

        assert self.serializer(
            context={'request': Mock(), 'command_name': 'ACT_NOW'}
        ).to_representation(p) == {
            '@type': 'customer',
            '@commands': {
                'MARK_IT': {
                    'name': 'MARK_IT',
                    'method': 'GET',
                    'uri': 'http://localhost/mark.it',
                },
                'REMOVE_IT': {
                    'name': 'REMOVE_IT',
                    'method': 'GET',
                    'uri': 'http://localhost/remove.it',
                },
            },
            'age': 81,
            'name': 'John',
        }

        # -- make sure that the test doesn't expose any side effects
        self.serializer._command_links = []


class ModelSerializerTestCase(SerializerTestCase):

    serializer = CustomerModelSerializer


class EmptySerializerTestCase(TestCase):

    def test__passes_nothing(self):

        s = serializers.EmptySerializer({'hi': 'there'})

        assert s.data == {'@type': 'empty'}


class ObjectSerializerTestCase(TestCase):

    def test__passes_everything(self):

        s = serializers.ObjectSerializer({'hi': 'there'})

        assert s.data == {
            '@type': 'object',
            'hi': 'there',
        }


class CommandSerializerTestCase(TestCase):

    def test_serializes_command_correctly(self):

        s = serializers.CommandSerializer(data={
            'name': 'DO_IT',
            'method': 'post',
            'uri': 'http://do.it/now',
            'body': {'wat': 'yes'},
        })

        assert s.is_valid() is True
        assert s.data == {
            '@type': 'command',
            'name': 'DO_IT',
            'method': 'post',
            'uri': 'http://do.it/now',
            'body': {'wat': 'yes'},
        }

    def test__fails_on_invalid_input(self):
        s = serializers.CommandSerializer(data={
            'name': 'hi there',
            'uri': 'not url',
        })

        assert s.is_valid() is False
        assert s.errors == {
            'method': ['This field is required.'],
            'uri': ['Enter a valid URL.'],
        }
