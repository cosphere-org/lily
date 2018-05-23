# -*- coding: utf-8 -*-

from django.test import TestCase
from mock import Mock, call
import pytest

from lily.docs.renderers.angular.command import Command
from lily.docs.renderers.angular.utils import normalize_indentation


class CommandTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initfixture(self, mocker):
        self.mocker = mocker

    def test_properties(self):

        command_signature = Mock()
        signature = self.mocker.patch(
            'lily.docs.renderers.angular.command.Signature')
        signature.return_value = command_signature
        (
            request_query,
            request_body,
            response,
            request_query_interface,
            request_body_interface,
            response_interface,
        ) = Mock(), Mock(), Mock(), Mock(), Mock(), Mock()
        interface = self.mocker.patch(
            'lily.docs.renderers.angular.command.Interface')
        interface.TYPES.REQUEST_QUERY = 'REQUEST_QUERY'
        interface.TYPES.REQUEST_BODY = 'REQUEST_BODY'
        interface.TYPES.RESPONSE = 'RESPONSE'
        interface.side_effect = [
            request_query_interface,
            request_body_interface,
            response_interface,
        ]
        command = Command(
            'READ_TASK',
            {
                'method': 'POST',
                'meta': {
                    'title': 'Read Task',
                    'description': 'Read Task Now',
                    'domain': {
                        'id': 'tasks',
                        'name': 'Tasks Management',
                    }
                },
                'access': {
                    'is_private': True,
                },
                'path_conf': {
                    'path': '/tasks/{task_id}',
                    'parameters': [
                        {
                            'name': 'task_id',
                            'type': 'integer',
                        }
                    ]
                },
                'schemas': {
                    'input_query': request_query,
                    'input_body': request_body,
                    'output': response,
                }
            })

        assert command.method == 'post'
        assert command.camel_name == 'readTask'
        assert command.domain_id == 'tasks'
        assert command.domain_name == 'Tasks Management'
        assert command.title == 'Read Task'
        assert command.description == 'Read Task Now'
        assert command.is_private is True
        assert command.path == '/tasks/{task_id}'
        assert command.path_parameters == [
            {'name': 'task_id', 'type': 'integer'}]
        assert command.request_query == request_query_interface
        assert command.request_body == request_body_interface
        assert command.response == response_interface
        assert command.signature == command_signature
        assert signature.call_args_list == [call(
            '/tasks/{task_id}',
            [{'name': 'task_id', 'type': 'integer'}],
            request_query_interface,
            request_body_interface
        )]

        assert interface.call_args_list == [
            call('READ_TASK', 'REQUEST_QUERY', request_query),
            call('READ_TASK', 'REQUEST_BODY', request_body),
            call('READ_TASK', 'RESPONSE', response),
        ]

    def test_header(self):
        # -- with title and description
        command = Command(
            'READ_TASK',
            {
                'method': 'GET',
                'meta': {
                    'title': 'Read Task',
                    'description': 'Read Task Now',
                    'domain': {
                        'id': 'tasks',
                        'name': 'Tasks Management',
                    }
                },
                'access': {
                    'is_private': True,
                },
                'path_conf': {
                    'path': '/tasks',
                    'parameters': []
                },
                'schemas': {
                    'input_query': Mock(),
                    'input_body': Mock(),
                    'output': Mock(),
                }
            })

        assert command.header == normalize_indentation('''
            /**
             * Read Task
             * -------------
             *
             * Read Task Now
             */
        ''', 0)

        # -- without description
        command = Command(
            'READ_TASK',
            {
                'method': 'GET',
                'meta': {
                    'title': 'Bulk Read Paths',
                    'domain': {
                        'id': 'tasks',
                        'name': 'Tasks Management',
                    }
                },
                'access': {
                    'is_private': True,
                },
                'path_conf': {
                    'path': '/tasks',
                    'parameters': []
                },
                'schemas': {
                    'input_query': Mock(),
                    'input_body': Mock(),
                    'output': Mock(),
                }
            })

        assert command.header == normalize_indentation('''
            /**
             * Bulk Read Paths
             */
        ''', 0)

    def test_render__get(self):

        command = Command(
            'READ_TASK',
            {
                'method': 'GET',
                'meta': {
                    'title': 'Read Task',
                    'domain': {
                        'id': 'tasks',
                        'name': 'Tasks Management',
                    }
                },
                'access': {
                    'is_private': True,
                },
                'path_conf': {
                    'path': '/tasks/{task_id}',
                    'parameters': [
                        {
                            'name': 'task_id',
                            'type': 'integer',
                        },
                    ]
                },
                'schemas': {
                    'input_query': Mock(),
                    'input_body': Mock(),
                    'output': Mock(),
                }
            })

        assert command.render() == normalize_indentation('''
            /**
             * Read Task
             */
            public readTask(taskId: any, params: ReadTaskQuery, body: ReadTaskBody): DataState<ReadTaskResponse> {
                return this.client.getDataState<ReadTaskResponse>(`/tasks/${taskId}`, { params }, body);
            }
        ''', 0)  # noqa

    def test_render__post(self):

        command = Command(
            'READ_TASK',
            {
                'method': 'POST',
                'meta': {
                    'title': 'Create Path',
                    'domain': {
                        'id': 'paths',
                        'name': 'Paths Management',
                    }
                },
                'access': {
                    'is_private': True,
                },
                'path_conf': {
                    'path': '/paths/',
                    'parameters': []
                },
                'schemas': {
                    'input_query': None,
                    'input_body': Mock(),
                    'output': Mock(),
                }
            })

        assert command.render() == normalize_indentation('''
            /**
             * Create Path
             */
            public readTask(body: ReadTaskBody): Observable<ReadTaskResponse> {
                return this.client
                    .post<ReadTaskResponse>('/paths/', body)
                    .pipe(filter(x => !_.isEmpty(x)));
            }
        ''', 0)  # noqa

    def test_render_facade__get(self):

        command = Command(
            'READ_TASK',
            {
                'method': 'GET',
                'meta': {
                    'title': 'Read Task',
                    'domain': {
                        'id': 'tasks',
                        'name': 'Tasks Management',
                    }
                },
                'access': {
                    'is_private': True,
                },
                'path_conf': {
                    'path': '/tasks/{task_id}',
                    'parameters': [
                        {
                            'name': 'task_id',
                            'type': 'integer',
                        },
                    ]
                },
                'schemas': {
                    'input_query': Mock(),
                    'input_body': Mock(),
                    'output': Mock(),
                }
            })

        assert command.render_facade() == normalize_indentation('''
            readTask(taskId: any, params: ReadTaskQuery, body: ReadTaskBody): DataState<ReadTaskResponse> {
                return this.tasksDomain.readTask(`/tasks/${taskId}`, { params }, body);
            }
        ''', 0)  # noqa

    def test_render_facade__post(self):

        command = Command(
            'READ_TASK',
            {
                'method': 'POST',
                'meta': {
                    'title': 'Create Path',
                    'domain': {
                        'id': 'paths',
                        'name': 'Paths Management',
                    }
                },
                'access': {
                    'is_private': True,
                },
                'path_conf': {
                    'path': '/paths/',
                    'parameters': []
                },
                'schemas': {
                    'input_query': None,
                    'input_body': Mock(),
                    'output': Mock(),
                }
            })

        assert command.render_facade() == normalize_indentation('''
            readTask(body: ReadTaskBody): Observable<ReadTaskResponse> {
                return this.pathsDomain.readTask('/paths/', body);
            }
        ''', 0)  # noqa
