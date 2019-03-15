
import json
import os

from django.test import TestCase
from django.http import HttpResponse
from django.views.generic import View
from django.urls import re_path
import pytest

from conf.urls import urlpatterns

from lily.base.command import command
from lily.base.meta import Meta, Domain
from lily.base.access import Access
from lily.base.output import Output
from lily.base import serializers
from lily.base.test import Client


class HttpView(View):

    @command(
        name='HTTP_IT',
        meta=Meta(
            title='http it',
            description='http it',
            domain=Domain(id='d', name='d')),
        access=Access(access_list=[]))
    def get(self, request):
        return HttpResponse('http it!')


class SampleSerializer(serializers.Serializer):

    _type = 'test'

    hello = serializers.CharField()


class SampleView(View):

    @command(
        name='POST_IT',
        meta=Meta(
            title='post it',
            description='post it',
            domain=Domain(id='d', name='d')),
        access=Access(access_list=[]),
        output=Output(serializer=SampleSerializer))
    def post(self, request):
        raise self.event.Created(
            event='CREATED', context=request, data={'hello': 'post'})

    @command(
        name='GET_IT',
        meta=Meta(
            title='get it',
            description='get it',
            domain=Domain(id='d', name='d')),
        access=Access(access_list=[]),
        output=Output(serializer=SampleSerializer))
    def get(self, request):

        _type = request.GET.get('type')
        if _type in ['a', None]:
            raise self.event.Executed(
                event='LISTED', context=request, data={'hello': 'get.a'})

        if _type == 'b':
            raise self.event.Executed(
                event='LISTED', context=request, data={'hello': 'get.b'})

        if _type == 'c':
            raise self.event.Executed(
                event='LISTED_AGAIN', context=request, data={'hello': 'get.c'})

        if _type == 'd':
            raise self.event.DoesNotExist(
                event='ERROR_LISTED', context=request, data={'hello': 'get.d'})

    @command(
        name='PUT_IT',
        meta=Meta(
            title='put it',
            description='put it',
            domain=Domain(id='d', name='d')),
        access=Access(access_list=[]),
        output=Output(serializer=SampleSerializer))
    def put(self, request):
        raise self.event.Executed(
            event='UPDATED', context=request, data={'hello': 'put'})

    @command(
        name='DELETE_IT',
        meta=Meta(
            title='delete it',
            description='delete it',
            domain=Domain(id='d', name='d')),
        access=Access(access_list=[]),
        output=Output(serializer=SampleSerializer))
    def delete(self, request):
        raise self.event.Executed(
            event='DELETED', context=request, data={'hello': 'delete'})


urlpatterns.extend([
    re_path(r'^test/it/$', SampleView.as_view(), name='test.it'),
    re_path(r'^http/it/$', HttpView.as_view(), name='http.it'),
])


class ClientTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initfixture(self, mocker, tmpdir):
        self.tmpdir = tmpdir
        self.mocker = mocker

    def prepare_example_file(self):
        examples_file = self.tmpdir.mkdir('docs').join('examples.json')
        examples_file.write('{}')
        get_examples_filepath = self.mocker.patch(
            'lily.base.test.get_examples_filepath')
        get_examples_filepath.return_value = str(examples_file)

        return examples_file

    def test_create_file_if_does_not_exist(self):
        examples_file_dir = self.tmpdir.mkdir('docs')
        filepath = os.path.join(str(examples_file_dir), 'examples007.json')

        get_examples_filepath = self.mocker.patch(
            'lily.base.test.get_examples_filepath')
        get_examples_filepath.return_value = filepath

        response = Client().get('/test/it/')

        examples_file = open(filepath, 'r')
        assert response.status_code == 200
        assert json.loads(examples_file.read()) == {
            'GET_IT': {
                '200 (LISTED)': {
                    'method': 'get',
                    'description': 'LISTED',
                    'request': {
                        'path': '/test/it/',
                    },
                    'response': {
                        'status': 200,
                        'content_type': 'application/json',
                        'content': {
                            '@type': 'test',
                            '@event': 'LISTED',
                            'hello': 'get.a',
                        },
                    },

                },
            },
        }

    def test_single_response(self):
        examples_file = self.prepare_example_file()

        response = Client().get('/test/it/')

        assert response.status_code == 200
        assert json.loads(examples_file.read()) == {
            'GET_IT': {
                '200 (LISTED)': {
                    'method': 'get',
                    'description': 'LISTED',
                    'request': {
                        'path': '/test/it/',
                    },
                    'response': {
                        'status': 200,
                        'content_type': 'application/json',
                        'content': {
                            '@type': 'test',
                            '@event': 'LISTED',
                            'hello': 'get.a',
                        },
                    },

                },
            },
        }

    def test_http_response(self):
        examples_file = self.prepare_example_file()

        response = Client().get('/http/it/')

        assert response.status_code == 200
        assert json.loads(examples_file.read()) == {
            'HTTP_IT': {
                '200': {
                    'method': 'get',
                    'description': None,
                    'request': {
                        'path': '/http/it/',
                    },
                    'response': {
                        'status': 200,
                        'content_type': 'text/html; charset=utf-8',
                        'content': 'http it!',
                    },

                },
            },
        }

    def test_with_extra_desc(self):
        examples_file = self.prepare_example_file()

        response = Client().get('/test/it/', extra_desc='special')

        assert response.status_code == 200
        assert json.loads(examples_file.read()) == {
            'GET_IT': {
                '200 (LISTED) - special': {
                    'method': 'get',
                    'description': 'LISTED',
                    'request': {
                        'path': '/test/it/',
                    },
                    'response': {
                        'status': 200,
                        'content_type': 'application/json',
                        'content': {
                            '@type': 'test',
                            '@event': 'LISTED',
                            'hello': 'get.a',
                        },
                    },

                },
            },
        }

    def test_multiple_different_responses_single_endpoint(self):
        examples_file = self.prepare_example_file()

        Client().get('/test/it/?type=a')
        Client().get('/test/it/?type=b')
        Client().get('/test/it/?type=c')
        Client().get('/test/it/?type=d')

        assert json.loads(examples_file.read()) == {
            'GET_IT': {
                '200 (LISTED)': {
                    'method': 'get',
                    'description': 'LISTED',
                    'request': {
                        'path': '/test/it/?type=b',
                    },
                    'response': {
                        'status': 200,
                        'content_type': 'application/json',
                        'content': {
                            '@type': 'test',
                            '@event': 'LISTED',
                            'hello': 'get.b',
                        },
                    }
                },
                '200 (LISTED_AGAIN)': {
                    'method': 'get',
                    'description': 'LISTED_AGAIN',
                    'request': {
                        'path': '/test/it/?type=c',
                    },
                    'response': {
                        'status': 200,
                        'content_type': 'application/json',
                        'content': {
                            '@type': 'test',
                            '@event': 'LISTED_AGAIN',
                            'hello': 'get.c',
                        },
                    },
                },
                '404 (ERROR_LISTED)': {
                    'method': 'get',
                    'description': 'ERROR_LISTED',
                    'request': {
                        'path': '/test/it/?type=d',
                    },
                    'response': {
                        'status': 404,
                        'content_type': 'application/json',
                        'content': {
                            '@type': 'error',
                            '@event': 'ERROR_LISTED',
                            'hello': 'get.d',
                        },
                    },
                },
            },
        }

    def test_multiple_same_responses_single_endpoint(self):
        examples_file = self.prepare_example_file()

        Client().get('/test/it/?type=a')
        Client().get('/test/it/?type=b')
        Client().get('/test/it/?type=c')
        Client().get('/test/it/?type=c')
        Client().get('/test/it/?type=b')
        Client().get('/test/it/?type=c')

        assert json.loads(examples_file.read()) == {
            'GET_IT': {
                '200 (LISTED)': {
                    'method': 'get',
                    'description': 'LISTED',
                    'request': {
                        'path': '/test/it/?type=b',
                    },
                    'response': {
                        'status': 200,
                        'content_type': 'application/json',
                        'content': {
                            '@type': 'test',
                            '@event': 'LISTED',
                            'hello': 'get.b',
                        },
                    }
                },
                '200 (LISTED_AGAIN)': {
                    'method': 'get',
                    'description': 'LISTED_AGAIN',
                    'request': {
                        'path': '/test/it/?type=c',
                    },
                    'response': {
                        'status': 200,
                        'content_type': 'application/json',
                        'content': {
                            '@type': 'test',
                            '@event': 'LISTED_AGAIN',
                            'hello': 'get.c',
                        },
                    },
                },
            },
        }

    def test_multiple_responses_for_multiple_endpoints(self):
        examples_file = self.prepare_example_file()

        Client().get('/test/it/?type=a')
        Client().get('/test/it/?type=b')
        Client().get('/test/it/?type=a')
        Client().delete('/test/it/')
        Client().get('/test/it/?type=d')
        Client().put('/test/it/')

        assert json.loads(examples_file.read()) == {
            'GET_IT': {
                '200 (LISTED)': {
                    'method': 'get',
                    'description': 'LISTED',
                    'request': {
                        'path': '/test/it/?type=a'
                    },
                    'response': {
                        'status': 200,
                        'content_type': 'application/json',
                        'content': {
                            '@type': 'test',
                            '@event': 'LISTED',
                            'hello': 'get.a',
                        },
                    }
                },
                '404 (ERROR_LISTED)': {
                    'method': 'get',
                    'description': 'ERROR_LISTED',
                    'request': {
                        'path': '/test/it/?type=d'
                    },
                    'response': {
                        'status': 404,
                        'content_type': 'application/json',
                        'content': {
                            '@type': 'error',
                            '@event': 'ERROR_LISTED',
                            'hello': 'get.d',
                        },
                    }
                },
            },
            'DELETE_IT': {
                '200 (DELETED)': {
                    'method': 'delete',
                    'description': 'DELETED',
                    'request': {
                        'path': '/test/it/'
                    },
                    'response': {
                        'status': 200,
                        'content_type': 'application/json',
                        'content': {
                            '@type': 'test',
                            '@event': 'DELETED',
                            'hello': 'delete',
                        },
                    },
                }
            },
            'PUT_IT': {
                '200 (UPDATED)': {
                    'method': 'put',
                    'description': 'UPDATED',
                    'request': {
                        'path': '/test/it/'
                    },
                    'response': {
                        'status': 200,
                        'content_type': 'application/json',
                        'content': {
                            '@type': 'test',
                            '@event': 'UPDATED',
                            'hello': 'put',
                        },
                    },
                }
            },
        }

    def test_body_examples_for_post_and_put(self):
        examples_file = self.prepare_example_file()

        Client().post(
            '/test/it/',
            data=json.dumps({'create': 'it'}),
            content_type='application/json')
        Client().put(
            '/test/it/',
            data=json.dumps({'update': 'it', 'please': 'now'}),
            content_type='application/json')

        assert json.loads(examples_file.read()) == {
            'POST_IT': {
                '201 (CREATED)': {
                    'method': 'post',
                    'description': 'CREATED',
                    'response': {
                        'status': 201,
                        'content_type': 'application/json',
                        'content': {
                            '@type': 'test',
                            '@event': 'CREATED',
                            'hello': 'post',
                        }
                    },
                    'request': {
                        'path': '/test/it/',
                        'headers': {
                            'CONTENT-TYPE': 'application/json',
                        },
                        'content': {
                            'create': 'it',
                        }
                    }
                },
            },
            'PUT_IT': {
                '200 (UPDATED)': {
                    'method': 'put',
                    'description': 'UPDATED',
                    'response': {
                        'status': 200,
                        'content_type': 'application/json',
                        'content': {
                            '@type': 'test',
                            '@event': 'UPDATED',
                            'hello': 'put',
                        },
                    },
                    'request': {
                        'path': '/test/it/',
                        'headers': {
                            'CONTENT-TYPE': 'application/json',
                        },
                        'content': {
                            'update': 'it',
                            'please': 'now',
                        }
                    }
                }
            },
        }
