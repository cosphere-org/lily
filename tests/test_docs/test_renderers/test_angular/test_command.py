
from copy import deepcopy
from unittest.mock import Mock, call

from django.test import TestCase
import pytest

from lily.docs.renderers.angular.command import Command
from lily.base.utils import normalize_indentation
from tests import remove_white_chars


CONF = {
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
        'access_list': ['LEARNER'],
    },
    'path_conf': {
        'path': '/paths/',
        'parameters': []
    },
    'schemas': {
        'input_query': None,
        'input_body': None,
        'output': {'schema': {'hi': 'there'}, 'uri': ''},
    },
    'examples': {},
}


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
        self.mocker.patch.object(
            Command, 'get_bulk_read_field').return_value = None
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
                    'access_list': ['LEARNER'],
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
                    'input_query': {'schema': request_query, 'uri': 'Q'},
                    'input_body': {'schema': request_body, 'uri': 'B'},
                    'output': {'schema': response, 'uri': 'R'},
                },
                'examples': {},
            })

        assert command.method == 'post'
        assert command.camel_name == 'readTask'
        assert command.domain_id == 'tasks'
        assert command.domain_name == 'Tasks Management'
        assert command.title == 'Read Task'
        assert command.is_private is True
        assert command.authorization_required is True
        assert command.path == '/tasks/{task_id}'
        assert command.path_parameters == [
            {'name': 'task_id', 'type': 'integer'}]
        assert command.request_query == request_query_interface
        assert command.request_body == request_body_interface
        assert command.response == response_interface
        assert command.signature == command_signature
        assert signature.call_args_list == [call(
            'post',
            '/tasks/{task_id}',
            [{'name': 'task_id', 'type': 'integer'}],
            True,
            request_query_interface,
            request_body_interface,
            bulk_read_field=None,
        )]

        assert interface.call_args_list == [
            call('READ_TASK', 'REQUEST_QUERY', request_query, 'Q'),
            call('READ_TASK', 'REQUEST_BODY', request_body, 'B'),
            call('READ_TASK', 'RESPONSE', response, 'R', bulk_read_field=None),
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
                    'access_list': ['LEARNER'],
                },
                'path_conf': {
                    'path': '/tasks',
                    'parameters': []
                },
                'schemas': {
                    'input_query': None,
                    'input_body': None,
                    'output': {'schema': {}, 'uri': ''},
                },
                'examples': {},
            })

        assert command.header == normalize_indentation('''
            /**
             * Read Task
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
                    'access_list': ['LEARNER'],
                },
                'path_conf': {
                    'path': '/tasks',
                    'parameters': []
                },
                'schemas': {
                    'input_query': None,
                    'input_body': None,
                    'output': {'schema': {}, 'uri': ''},
                },
                'examples': {},
            })

        assert command.header == normalize_indentation('''
            /**
             * Bulk Read Paths
             */
        ''', 0)

    def test_render__get_bulk_read_field__not_get(self):

        self.mocker.patch.object(
            Command, 'get_bulk_read_field').return_value = 'people'
        command = Command(
            'UPDATE_TASK',
            {
                'method': 'PUT',
                'meta': {
                    'title': 'Update Task',
                    'domain': {
                        'id': 'tasks',
                        'name': 'Tasks Management',
                    }
                },
                'access': {
                    'is_private': True,
                    'access_list': ['LEARNER'],
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
                    'input_query': None,
                    'input_body': {'schema': {'hi': 'there'}, 'uri': ''},
                    'output': {
                        'schema': {
                            'type': 'object',
                            'required': ['people'],
                            'properties': {
                                'people': {
                                    'type': 'array',
                                },
                            },
                        },
                        'uri': '',
                    },
                },
                'examples': {},
            })

        assert command.render() == normalize_indentation('''
            /**
             * Update Task
             */
            public updateTask(taskId: any, body: X.UpdateTaskBody): Observable<X.UpdateTaskResponse> {
                return this.client
                    .put<X.UpdateTaskResponse>(`/tasks/${taskId}`, body, { authorizationRequired: true })
                    .pipe(map(x => x.people));
            }
        ''', 0)  # noqa

    def test_render__get_bulk_read_field__get(self):

        self.mocker.patch.object(
            Command, 'get_bulk_read_field').return_value = 'people'
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
                    'access_list': ['LEARNER'],
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
                    'input_query': {'schema': {'hi': 'there'}, 'uri': ''},
                    'input_body': None,
                    'output': {
                        'schema': {
                            'type': 'object',
                            'required': ['people'],
                            'properties': {
                                'people': {
                                    'type': 'array',
                                },
                            },
                        },
                        'uri': '',
                    },
                },
                'examples': {},
            })

        assert command.render() == normalize_indentation('''
            /**
             * Read Task
             */
            public readTask(taskId: any, params: X.ReadTaskQuery): Observable<X.ReadTaskResponse> {
                return this.client.get<X.ReadTaskResponse>(`/tasks/${taskId}`, { params, authorizationRequired: true });
            }
        ''', 0)  # noqa

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
                    'access_list': ['LEARNER'],
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
                    'input_query': {'schema': {'hi': 'there'}, 'uri': ''},
                    'input_body': None,
                    'output': {'schema': {'hi': 'there'}, 'uri': ''},
                },
                'examples': {},
            })

        assert command.render() == normalize_indentation('''
            /**
             * Read Task
             */
            public readTask(taskId: any, params: X.ReadTaskQuery): Observable<X.ReadTaskResponse> {
                return this.client.get<X.ReadTaskResponse>(`/tasks/${taskId}`, { params, authorizationRequired: true });
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
                    'access_list': ['LEARNER'],
                },
                'path_conf': {
                    'path': '/paths/',
                    'parameters': []
                },
                'schemas': {
                    'input_query': None,
                    'input_body': {'schema': {'hi': 'there'}, 'uri': ''},
                    'output': {'schema': {'hi': 'there'}, 'uri': ''},
                },
                'examples': {},
            })

        assert command.render() == normalize_indentation('''
            /**
             * Create Path
             */
            public readTask(body: X.ReadTaskBody): Observable<X.ReadTaskResponse> {
                return this.client
                    .post<X.ReadTaskResponse>('/paths/', body, { authorizationRequired: true })
                    .pipe(filter(x => !_.isEmpty(x)));
            }
        ''', 0)  # noqa

    def test_render_facade__get_bulk_read_field(self):

        self.mocker.patch.object(
            Command, 'get_bulk_read_field').return_value = 'people'
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
                    'access_list': ['LEARNER'],
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
                    'input_query': {'schema': {'hi': 'there'}, 'uri': ''},
                    'input_body': None,
                    'output': {
                        'schema': {
                            'type': 'object',
                            'required': ['people'],
                            'properties': {
                                'people': {
                                    'type': 'array',
                                },
                            },
                        },
                        'uri': '',
                    },
                },
                'examples': {},
            })

        assert command.render_facade() == normalize_indentation('''
            readTask(taskId: any, params: X.ReadTaskQuery): Observable<X.ReadTaskResponse> {
                return this.tasksDomain.readTask(taskId, params);
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
                    'access_list': ['LEARNER'],
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
                    'input_query': {'schema': {'hi': 'there'}, 'uri': ''},
                    'input_body': None,
                    'output': {'schema': {'hi': 'there'}, 'uri': ''},
                },
                'examples': {},
            })

        assert command.render_facade() == normalize_indentation('''
            readTask(taskId: any, params: X.ReadTaskQuery): Observable<X.ReadTaskResponse> {
                return this.tasksDomain.readTask(taskId, params);
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
                    'access_list': ['LEARNER'],
                },
                'path_conf': {
                    'path': '/paths/',
                    'parameters': []
                },
                'schemas': {
                    'input_query': None,
                    'input_body': {'schema': {'hi': 'there'}, 'uri': ''},
                    'output': {'schema': {'hi': 'there'}, 'uri': ''},
                },
                'examples': {},
            })

        assert command.render_facade() == normalize_indentation('''
            readTask(body: X.ReadTaskBody): Observable<X.ReadTaskResponse> {
                return this.pathsDomain.readTask(body);
            }
        ''', 0)  # noqa

    #
    # render_examples
    #
    def test_render_examples(self):

        conf = deepcopy(CONF)
        conf['examples'] = {
            '404 (NOT_FOUND)': {
                'response': {
                    'where': 'here',
                    'error': 'not found',
                    'status': 404,
                },
            },
            '200 (YO)': {
                'response': {
                    'id': 45,
                    'age': 879,
                },
            },

        }

        command = Command('BULK_READ_TASKS', conf)

        assert (
            remove_white_chars(command.render_examples()) ==
            remove_white_chars(normalize_indentation('''
                /**
                 * Examples for BULK_READ_TASKS
                 */
                export const BulkReadTasksExamples = {
                    "200 (YO)": {
                        "age": 879,
                        "id": 45
                    },

                    "404 (NOT_FOUND)": {
                        "error": "not found",
                        "status": 404,
                        "where": "here"
                    }
                }
            ''', 0)))

    #
    # render_access
    #
    def test_render_access(self):

        conf = deepcopy(CONF)
        conf['access'] = {
            'access_list': [
                'LEARNER',
                'MENTOR',
            ],
            'is_private': False,
        }

        command = Command('BULK_READ_TASKS', conf)

        assert command.render_access('AccountType') == (
            'BULK_READ_TASKS: [AccountType.LEARNER,AccountType.MENTOR]')

    def test_render_access__no_access(self):

        conf = deepcopy(CONF)
        conf['access'] = {
            'access_list': [],
            'is_private': False,
        }

        command = Command('BULK_READ_TASKS', conf)

        assert command.render_access('AccountType') == (
            'BULK_READ_TASKS: null')

    #
    # get_bulk_read_field
    #
    def test_get_bulk_read_field(self):

        conf = deepcopy(CONF)
        conf['schemas'] = {
            'output': {
                'schema': {
                    'type': 'object',
                    'properties': {
                        'tasks': {
                            'type': 'array',
                        }
                    }
                },
                'uri': 'hi/there',
            },
        }

        command = Command('BULK_READ_TASKS', conf)

        assert command.get_bulk_read_field() == 'tasks'

    def test_get_bulk_read_field__not_bulk_read_name(self):

        command = Command('READ_TASK', CONF)

        assert command.get_bulk_read_field() is None

    def test_get_bulk_read_field__more_than_one_field(self):

        conf = deepcopy(CONF)
        conf['schemas'] = {
            'output': {
                'schema': {
                    'type': 'object',
                    'properties': {
                        'tasks': {
                            'type': 'array',
                        },
                        'people': {
                            'type': 'array',
                        }
                    }
                },
                'uri': 'hi/there',
            },
        }

        command = Command('BULK_READ_TASKS', conf)

        assert command.get_bulk_read_field() is None

    def test_get_bulk_read_field__empty_schema(self):

        conf = deepcopy(CONF)
        conf['schemas'] = {
            'output': {
                'schema': {},
                'uri': 'hi/there',
            },
        }

        command = Command('BULK_READ_TASKS', conf)

        assert command.get_bulk_read_field() is None
