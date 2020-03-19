
from collections import OrderedDict
from unittest.mock import call, Mock
import json
import os
import tempfile

from django.test import TestCase
import pytest

from lily.base.events import EventFactory
from lily.base.utils import normalize_indentation
from lily.docs.renderers.angular.domain import Domain
from lily.docs.renderers.angular.interface import Enum
from lily.docs.renderers.angular.renderer import AngularClientRenderer
from tests import remove_white_chars


class AngularClientRendererTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initfixture(self, mocker, tmpdir):
        self.mocker = mocker
        self.tmpdir = tmpdir

    def setUp(self):

        self.base_dir = self.tmpdir.mkdir('client')
        self.src_dir = (
            self.base_dir
            .mkdir('projects')
            .mkdir('client')
            .mkdir('src'))
        self.domains_dir = self.src_dir.mkdir('domains')
        self.services_dir = self.src_dir.mkdir('services')

        self.mocker.patch.object(
            tempfile, 'mkdtemp').return_value = str(self.base_dir)
        self.renderer = AngularClientRenderer('origin', 'prefix')
        self.current_cwd = os.getcwd()
        self.renderer.repo.cd_to_repo()

    def tearDown(self):
        os.chdir(self.current_cwd)

    #
    # RENDER
    #
    def test_render(self):

        class MockConfig:

            @property
            def version(self):
                return '0.9.1'

            @classmethod
            def get_lily_path(cls):
                return str(self.tmpdir)

        commands_dir = self.tmpdir.mkdir('commands')
        commands_dir.join('0.9.1.json').write(json.dumps({'some': 'commands'}))
        self.mocker.patch(
            'lily.docs.renderers.angular.renderer.Config', MockConfig)

        repo = Mock()
        self.mocker.patch.object(self.renderer, 'repo', repo)

        http_repo = Mock()
        self.mocker.patch.object(self.renderer, 'http_repo', http_repo)

        template_repo = Mock()
        self.mocker.patch.object(self.renderer, 'template_repo', template_repo)

        group_commands_by_domain = self.mocker.patch.object(
            self.renderer, 'group_commands_by_domain')
        group_commands_by_domain.return_value = OrderedDict([
            (Domain('cards', ''), {'X': 'X', 'B': 'B'}),
            (Domain('paths', ''), {'Z': 'Z', 'A': 'A'}),
        ])

        render_client_module_ts = self.mocker.patch.object(
            self.renderer, 'render_client_module_ts')

        render_api_ts = self.mocker.patch.object(
            self.renderer, 'render_api_ts')

        render_api_index_ts = self.mocker.patch.object(
            self.renderer, 'render_api_index_ts')

        render_domain = self.mocker.patch.object(
            self.renderer, 'render_domain')

        render_access_ts = self.mocker.patch.object(
            self.renderer, 'render_access_ts')

        render_enums_ts = self.mocker.patch.object(
            self.renderer, 'render_enums_ts')

        self.renderer.render()

        assert group_commands_by_domain.call_count == 1
        assert render_client_module_ts.call_args_list == [
            call(group_commands_by_domain.return_value)]
        assert render_api_index_ts.call_args_list == [
            call(group_commands_by_domain.return_value)]
        assert render_api_ts.call_args_list == [
            call(group_commands_by_domain.return_value)]
        assert render_domain.call_args_list == [
            call(Domain('cards', ''), ['B', 'X']),
            call(Domain('paths', ''), ['A', 'Z']),
        ]

        # -- shared
        assert self.renderer.repo.create_dir.call_args_list == [
            call('./projects/client/src/shared'),
        ]
        assert render_access_ts.call_args_list == [
            call(
                './projects/client/src/shared',
                ['B', 'X', 'A', 'Z']
            )]
        assert render_enums_ts.call_args_list == [
            call(
                './projects/client/src/shared',
                ['B', 'X', 'A', 'Z']
            )]

        assert template_repo.clone.call_count == 1

        assert repo.clone.call_count == 1
        assert repo.install.call_count == 1
        assert repo.upgrade_version.call_count == 1
        assert repo.build.call_count == 1
        assert repo.add_all.call_count == 1
        assert repo.commit.call_count == 1
        assert repo.push.call_count == 1
        assert http_repo.cd_to_repo.call_count == 1
        assert http_repo.clone.call_count == 1
        assert http_repo.install.call_count == 1
        assert http_repo.build.call_count == 1
        assert http_repo.link.call_count == 1

    def test_render__only_build(self):

        class MockConfig:

            @property
            def version(self):
                return '0.9.1'

            @classmethod
            def get_lily_path(cls):
                return str(self.tmpdir)

        commands_dir = self.tmpdir.mkdir('commands')
        commands_dir.join('0.9.1.json').write(json.dumps({'some': 'commands'}))
        self.mocker.patch(
            'lily.docs.renderers.angular.renderer.Config', MockConfig)

        repo = Mock()
        self.mocker.patch.object(self.renderer, 'repo', repo)

        http_repo = Mock()
        self.mocker.patch.object(self.renderer, 'http_repo', http_repo)

        template_repo = Mock()
        self.mocker.patch.object(self.renderer, 'template_repo', template_repo)

        group_commands_by_domain = self.mocker.patch.object(
            self.renderer, 'group_commands_by_domain')
        group_commands_by_domain.return_value = OrderedDict([
            (Domain('cards', ''), {'X': 'X', 'B': 'B'}),
            (Domain('paths', ''), {'Z': 'Z', 'A': 'A'}),
        ])

        render_client_module_ts = self.mocker.patch.object(
            self.renderer, 'render_client_module_ts')

        render_api_ts = self.mocker.patch.object(
            self.renderer, 'render_api_ts')

        render_api_index_ts = self.mocker.patch.object(
            self.renderer, 'render_api_index_ts')

        render_domain = self.mocker.patch.object(
            self.renderer, 'render_domain')

        render_access_ts = self.mocker.patch.object(
            self.renderer, 'render_access_ts')

        render_enums_ts = self.mocker.patch.object(
            self.renderer, 'render_enums_ts')

        self.renderer.render(only_build=True)

        assert group_commands_by_domain.call_count == 1
        assert render_client_module_ts.call_args_list == [
            call(group_commands_by_domain.return_value)]
        assert render_api_index_ts.call_args_list == [
            call(group_commands_by_domain.return_value)]
        assert render_api_ts.call_args_list == [
            call(group_commands_by_domain.return_value)]
        assert render_domain.call_args_list == [
            call(Domain('cards', ''), ['B', 'X']),
            call(Domain('paths', ''), ['A', 'Z']),
        ]

        # -- shared
        assert self.renderer.repo.create_dir.call_args_list == [
            call('./projects/client/src/shared'),
        ]
        assert render_access_ts.call_args_list == [
            call(
                './projects/client/src/shared',
                ['B', 'X', 'A', 'Z']
            )]
        assert render_enums_ts.call_args_list == [
            call(
                './projects/client/src/shared',
                ['B', 'X', 'A', 'Z']
            )]

        assert template_repo.clone.call_count == 1

        assert repo.clone.call_count == 1
        assert repo.install.call_count == 1
        assert repo.build.call_count == 1
        assert repo.upgrade_version.call_count == 0
        assert repo.add_all.call_count == 0
        assert repo.commit.call_count == 0
        assert repo.push.call_count == 0
        assert http_repo.cd_to_repo.call_count == 1
        assert http_repo.clone.call_count == 1
        assert http_repo.install.call_count == 1
        assert http_repo.build.call_count == 1
        assert http_repo.link.call_count == 1

    #
    # GROUP_COMMANDS_BY_DOMAIN
    #
    def test_group_commands_by_domain(self):

        command0, command1, command2 = (
            Mock(domain_id='cards', domain_name='...', is_private=False),
            Mock(domain_id='paths', domain_name='...', is_private=False),
            Mock(domain_id='cards', domain_name='...', is_private=False),
        )
        self.mocker.patch(
            'lily.docs.renderers.angular.renderer.Command'
        ).side_effect = [command0, command1, command2]
        self.mocker.patch.object(
            AngularClientRenderer,
            'get_commands'
        ).return_value = OrderedDict([
            ('CREATE_CARD', {'create_card': 'conf'}),
            ('REMOVE_PATH', {'remove_path': 'conf'}),
            ('REMOVE_CARD', {'remove_card': 'conf'}),
        ])

        commands_by_domain = self.renderer.group_commands_by_domain()

        assert commands_by_domain == {
            Domain('cards', ''): {
                'CREATE_CARD': command0,
                'REMOVE_CARD': command2,
            },
            Domain('paths', ''): {
                'REMOVE_PATH': command1,
            }
        }

    def test_group_commands_by_domain__exclude_domains(self):

        command0, command1, command2 = (
            Mock(domain_id='cards', domain_name='...', is_private=False),
            Mock(domain_id='paths', domain_name='...', is_private=False),
            Mock(domain_id='cards', domain_name='...', is_private=False),
        )
        self.mocker.patch(
            'lily.docs.renderers.angular.renderer.Command'
        ).side_effect = [command0, command1, command2]
        self.mocker.patch.object(
            AngularClientRenderer,
            'get_commands'
        ).return_value = OrderedDict([
            ('CREATE_CARD', {'create_card': 'conf'}),
            ('REMOVE_PATH', {'remove_path': 'conf'}),
            ('REMOVE_CARD', {'remove_card': 'conf'}),
        ])

        commands_by_domain = self.renderer.group_commands_by_domain(
            exclude_domains=('PATHS',))

        assert commands_by_domain == {
            Domain('cards', ''): {
                'CREATE_CARD': command0,
                'REMOVE_CARD': command2,
            },
        }

    def test_group_commands_by_domain__include_domains(self):

        command0, command1, command2 = (
            Mock(domain_id='hashtags', domain_name='...', is_private=False),
            Mock(domain_id='paths', domain_name='...', is_private=False),
            Mock(domain_id='cards', domain_name='...', is_private=False),
        )
        self.mocker.patch(
            'lily.docs.renderers.angular.renderer.Command'
        ).side_effect = [command0, command1, command2]
        self.mocker.patch.object(
            AngularClientRenderer,
            'get_commands'
        ).return_value = OrderedDict([
            ('CREATE_HASHTAG', {'create_hashtag': 'conf'}),
            ('REMOVE_PATH', {'remove_path': 'conf'}),
            ('REMOVE_CARD', {'remove_card': 'conf'}),
        ])

        commands_by_domain = self.renderer.group_commands_by_domain(
            include_domains=('PATHS', 'hashtags'))

        assert commands_by_domain == {
            Domain('hashtags', ''): {
                'CREATE_HASHTAG': command0,
            },
            Domain('paths', ''): {
                'REMOVE_PATH': command1,
            }
        }

    def test_group_commands_by_domain__is_private(self):

        command0, command1, command2 = (
            Mock(domain_id='cards', domain_name='...', is_private=False),
            Mock(domain_id='paths', domain_name='...', is_private=True),
            Mock(domain_id='cards', domain_name='...', is_private=True),
        )
        self.mocker.patch(
            'lily.docs.renderers.angular.renderer.Command'
        ).side_effect = [command0, command1, command2]
        self.mocker.patch.object(
            AngularClientRenderer,
            'get_commands'
        ).return_value = OrderedDict([
            ('CREATE_CARD', {'create_card': 'conf'}),
            ('REMOVE_PATH', {'remove_path': 'conf'}),
            ('REMOVE_CARD', {'remove_card': 'conf'}),
        ])

        commands_by_domain = self.renderer.group_commands_by_domain()

        assert commands_by_domain == {
            Domain('cards', ''): {
                'CREATE_CARD': command0,
            }
        }

    #
    # GET_COMMANDS
    #
    def test_get_commands(self):

        class MockConfig:

            @property
            def version(self):
                return '0.9.1'

            @classmethod
            def get_lily_path(cls):
                return str(self.tmpdir)

        commands_dir = self.tmpdir.mkdir('commands')
        commands_dir.join('0.9.1.json').write(json.dumps({'some': 'commands'}))
        self.mocker.patch(
            'lily.docs.renderers.angular.renderer.Config', MockConfig)

        assert self.renderer.get_commands() == {'some': 'commands'}

    #
    # RENDER_DOMAIN
    #
    def test_render_domain(self):

        render_index_ts = self.mocker.patch.object(
            AngularClientRenderer, 'render_index_ts')
        render_models_ts = self.mocker.patch.object(
            AngularClientRenderer, 'render_models_ts')
        render_domain_ts = self.mocker.patch.object(
            AngularClientRenderer, 'render_domain_ts')
        render_examples_ts = self.mocker.patch.object(
            AngularClientRenderer, 'render_examples_ts')

        domain = Domain('cards', 'Cards Management')

        domains_path = str(self.domains_dir)

        assert os.listdir(domains_path) == []

        self.renderer.render_domain(domain, [])

        assert os.listdir(domains_path) == ['cards']
        assert render_index_ts.call_args_list == [call(domain)]
        assert render_models_ts.call_args_list == [call(domain, [])]
        assert render_domain_ts.call_args_list == [call(domain, [])]
        assert render_examples_ts.call_args_list == [call(domain, [])]

    #
    # RENDER_INDEX_TS
    #
    def test_render_index_ts(self):

        paths_path = str(self.domains_dir.mkdir('paths'))

        assert os.listdir(paths_path) == []

        self.renderer.render_index_ts(Domain('paths', 'Path Management'))

        assert os.listdir(paths_path) == ['index.ts']
        with open(os.path.join(paths_path, 'index.ts'), 'r') as f:
            assert f.read() == normalize_indentation('''
                export * from './paths.domain';
                export * from './paths.models';
            ''', 0)

    #
    # RENDER_MODELS_TS
    #
    def test_render_models_ts__without_enums(self):

        paths_path = str(self.domains_dir.mkdir('paths'))
        domain = Domain('paths', 'Path Management')
        commands = [
            Mock(
                request_query=Mock(
                    render=Mock(return_value=['request 1', []])),
                request_body=Mock(
                    render=Mock(return_value=['', []])),
                response=Mock(
                    render=Mock(return_value=['response 1', []])),
            ),
            Mock(
                request_query=Mock(
                    render=Mock(return_value=['request 2', []])),
                request_body=Mock(
                    render=Mock(return_value=['', []])),
                response=Mock(
                    render=Mock(return_value=['response 2', []])),
            ),
        ]

        assert os.listdir(paths_path) == []

        self.renderer.render_models_ts(domain, commands)

        assert os.listdir(paths_path) == ['paths.models.ts']
        with open(os.path.join(paths_path, 'paths.models.ts'), 'r') as f:
            assert f.read() == normalize_indentation('''
                /**
                  * THIS FILE WAS AUTOGENERATED, ALL MANUAL CHANGES CAN BE
                  * OVERWRITTEN
                  */



                /**
                 * Path Management Domain Models
                 */

                request 1

                response 1

                request 2

                response 2
            ''', 0)

    def test_render_models_ts__with_enums(self):

        paths_path = str(self.domains_dir.mkdir('paths'))
        domain = Domain('paths', 'Path Management')
        commands = [
            Mock(
                request_query=Mock(
                    render=Mock(return_value=[
                        'request 1', [Enum('Type', ['A'])]])),
                request_body=Mock(
                    render=Mock(return_value=['', []])),
                response=Mock(
                    render=Mock(return_value=[
                        'response 1', [Enum('Jack', []), Enum('Type', [])]])),
            ),
        ]

        assert os.listdir(paths_path) == []

        self.renderer.render_models_ts(domain, commands)

        assert os.listdir(paths_path) == ['paths.models.ts']
        with open(os.path.join(paths_path, 'paths.models.ts'), 'r') as f:
            assert f.read() == normalize_indentation('''
                /**
                  * THIS FILE WAS AUTOGENERATED, ALL MANUAL CHANGES CAN BE
                  * OVERWRITTEN
                  */

                import { Jack, Type } from '../../shared/enums';

                /**
                 * Path Management Domain Models
                 */

                request 1

                response 1
            ''', 0)

    #
    # RENDER_DOMAIN_TS
    #
    def test_render_domain_ts(self):

        paths_path = str(self.domains_dir.mkdir('paths'))
        domain = Domain('paths', 'Path Management')
        commands = [
            Mock(render=Mock(return_value='command 1')),
            Mock(render=Mock(return_value='command 2')),
        ]

        assert os.listdir(paths_path) == []

        self.renderer.render_domain_ts(domain, commands)

        assert os.listdir(paths_path) == ['paths.domain.ts']
        with open(os.path.join(paths_path, 'paths.domain.ts'), 'r') as f:
            assert f.read() == normalize_indentation('''
                /**
                  * THIS FILE WAS AUTOGENERATED, ALL MANUAL CHANGES CAN BE
                  * OVERWRITTEN
                  */

                /**
                 * Path Management Domain
                 */
                import { Injectable } from '@angular/core';
                import { filter } from 'rxjs/operators';
                import { Observable } from 'rxjs';
                import * as _ from 'underscore';

                import { HttpService } from '@lily/http';

                import * as X from './paths.models';

                @Injectable()
                export class PathsDomain {
                    constructor(private client: HttpService) {}

                    command 1

                    command 2

                }
            ''', 0)  # noqa

    #
    # RENDER_EXAMPLES_TS
    #
    def test_render_examples_ts(self):

        paths_path = str(self.domains_dir.mkdir('paths'))
        domain = Domain('paths', 'Path Management')
        commands = [
            Mock(render_examples=Mock(return_value='command 1')),
            Mock(render_examples=Mock(return_value='command 2')),
        ]

        assert os.listdir(paths_path) == []

        self.renderer.render_examples_ts(domain, commands)

        assert os.listdir(paths_path) == ['paths.examples.ts']
        with open(os.path.join(paths_path, 'paths.examples.ts'), 'r') as f:
            assert f.read() == normalize_indentation('''
                /**
                  * THIS FILE WAS AUTOGENERATED, ALL MANUAL CHANGES CAN BE
                  * OVERWRITTEN
                  */

                /**
                 * Path Management Domain Examples
                 */

                command 1

                command 2
            ''', 0)  # noqa

    #
    # RENDER_ACCESS_TS
    #
    def test_render_access_ts(self):

        shared_path = str(self.src_dir.mkdir('shared'))
        commands = [
            Mock(render_access=Mock(
                return_value=(
                    'BULK_READ_WHAT: [AccountType.LEARNER, AccountType.MENTOR]'
                ))),
            Mock(render_access=Mock(return_value='BULK_DELETE_THIS: null')),
            Mock(
                render_access=Mock(
                    return_value='CREATE: [AccountType.ADMIN]')),
        ]

        assert os.listdir(shared_path) == []

        self.renderer.render_access_ts(shared_path, commands)

        assert os.listdir(shared_path) == ['access.ts']
        with open(os.path.join(shared_path, 'access.ts'), 'r') as f:
            result = f.read()
            assert result == normalize_indentation('''
                /**
                  * THIS FILE WAS AUTOGENERATED, ALL MANUAL CHANGES CAN BE
                  * OVERWRITTEN
                  */

                import { AccountType } from './enums';

                export const Access = {
                  BULK_READ_WHAT: [AccountType.LEARNER, AccountType.MENTOR],
                  BULK_DELETE_THIS: null,
                  CREATE: [AccountType.ADMIN],
                }
            ''', 0)  # noqa

    #
    # RENDER_ENUMS_TS
    #
    def test_render_enums_ts__no_enums(self):

        self.mocker.patch.object(
            self.renderer,
            'collect_unique_enums'
        ).return_value = []
        shared_path = str(self.src_dir.mkdir('shared'))

        self.renderer.render_enums_ts(shared_path, Mock())

        assert self.src_dir.join('shared/enums.ts').read() == ''

    def test_render_enums_ts(self):

        self.mocker.patch.object(
            self.renderer,
            'collect_unique_enums'
        ).return_value = [
            Enum('age', [11, 33]),
            Enum('category', ['AA', 'YY', 'XX']),
            Enum('name', ['Jack', 'Alice', 'Joe']),
        ]
        shared_path = str(self.src_dir.mkdir('shared'))

        self.renderer.render_enums_ts(shared_path, Mock())

        assert os.listdir(self.src_dir) == ['domains', 'services', 'shared']
        assert (
            self.src_dir.join('shared/enums.ts').read() ==
            normalize_indentation('''
                export enum Age {
                    VALUE_11 = 11,
                    VALUE_33 = 33,
                }

                export enum Category {
                    AA = 'AA',
                    XX = 'XX',
                    YY = 'YY',
                }

                export enum Name {
                    ALICE = 'Alice',
                    JACK = 'Jack',
                    JOE = 'Joe',
                }
            ''', 0))  # noqa

    #
    # COLLECT_UNIQUE_ENUMS
    #
    def test_collect_unique_enums__all_unique(self):

        e0 = Enum('age', [11, 33])
        e1 = Enum('name', ['Jack', 'Alice', 'Joe'])
        e2 = Enum('category', ['AA', 'YY', 'XX'])

        assert self.renderer.collect_unique_enums([
            Mock(
                request_query=Mock(enums=[e0, e1]),
                request_body=Mock(enums=[]),
                response=Mock(enums=[])),
            Mock(
                request_query=Mock(enums=[]),
                request_body=Mock(enums=[e2]),
                response=Mock(enums=[])),
        ]) == [e0, e2, e1]

    def test_collect_unique_enums__with_duplicates(self):

        e0 = Enum('age', [11, 33])
        e1 = Enum('age', [11, 33])
        e2 = Enum('name', ['Jack', 'Alice', 'Joe'])
        e3 = Enum('name', ['Jack', 'Alice', 'Joe'])
        e4 = Enum('category', ['AA', 'YY', 'XX'])

        assert self.renderer.collect_unique_enums([
            Mock(
                request_query=Mock(enums=[e0]),
                request_body=Mock(enums=[]),
                response=Mock(enums=[])),
            Mock(
                request_query=Mock(enums=[]),
                request_body=Mock(enums=[e1, e2]),
                response=Mock(enums=[])),
            Mock(
                request_query=Mock(enums=[]),
                request_body=Mock(enums=[]),
                response=Mock(enums=[e3, e4])),
        ]) == [e0, e4, e2]

    def test_collect_unique_enums__inconsistent_duplicates_detected(self):

        e0 = Enum('age', [11, 33])
        e1 = Enum('age', [11, 22, 33])
        e2 = Enum('name', ['Jack', 'Alice', 'Joe'])

        with pytest.raises(EventFactory.ServerError) as e:
            self.renderer.collect_unique_enums([
                Mock(
                    request_query=Mock(enums=[e0]),
                    request_body=Mock(enums=[]),
                    response=Mock(enums=[])),
                Mock(
                    request_query=Mock(enums=[]),
                    request_body=Mock(enums=[e1, e2]),
                    response=Mock(enums=[])),
            ])

        assert e.value.data == {
            '@event': 'INCONSISTENT_ENUMS_DETECTED',
            '@type': 'error',
            'inconsistent_enums': [
                {
                    'enum.0': {
                        'name': 'Age',
                        'values': [33, 11],
                    },
                    'enum.1': {
                        'name': 'Age',
                        'values': [33, 11, 22],
                    },
                },
            ],
        }

    #
    # RENDER_API_INDEX_TS
    #
    def test_render_api_index_ts(self):

        commands_by_domain = {
            Domain('cards', 'Cards Management'): {},
            Domain('recall', 'Recall Management'): {},
            Domain('paths', 'Path Management'): {},
        }

        self.renderer.render_api_index_ts(commands_by_domain)

        assert os.listdir(self.domains_dir) == ['index.ts']
        assert (
            self.domains_dir.join('index.ts').read() ==
            normalize_indentation('''
                export * from './cards/index';
                export * from './paths/index';
                export * from './recall/index';
            ''', 0))  # noqa

    #
    # RENDER_API_TS
    #
    def test_render_api_ts(self):

        command = lambda x: Mock(render_facade=Mock(return_value=x))  # noqa
        commands_by_domain = {
            Domain('cards', 'Cards Management'): {
                'READ_CARDS': command('    <READ_CARDS>'),
                'DELETE_CARD': command('    <DELETE_CARD>'),
            },
            Domain('paths', 'Path Management'): {
                'CREATE_PATH': command('    <CREATE_PATH>'),
            },
        }
        services_path = str(self.services_dir)

        self.renderer.render_api_ts(commands_by_domain)

        assert os.listdir(services_path) == ['api.service.ts']
        with open(os.path.join(services_path, 'api.service.ts'), 'r') as f:
            assert remove_white_chars(f.read()) == remove_white_chars(normalize_indentation('''
                /**
                  * THIS FILE WAS AUTOGENERATED, ALL MANUAL CHANGES CAN BE
                  * OVERWRITTEN
                  */

                /**
                 * Facade API Service for all domains
                 */
                import { Injectable, Injector } from '@angular/core';
                import { Observable } from 'rxjs';

                import { Options } from '@lily/http';

                import * as X from '../domains/index';

                @Injectable()
                export class APIService {

                    constructor(private injector: Injector) {}

                    /**
                     * Cards Management domain
                     */
                    private _cardsDomain: X.CardsDomain;

                    public get cardsDomain(): X.CardsDomain {
                        if (!this._cardsDomain) {
                            this._cardsDomain = this.injector.get(X.CardsDomain);
                        }

                        return this._cardsDomain;
                    }

                    <DELETE_CARD>

                    <READ_CARDS>

                    /**
                     * Path Management domain
                     */
                    private _pathsDomain: X.PathsDomain;

                    public get pathsDomain(): X.PathsDomain {
                        if (!this._pathsDomain) {
                            this._pathsDomain = this.injector.get(X.PathsDomain);
                        }

                        return this._pathsDomain;
                    }

                    <CREATE_PATH>

                }
            ''', 0))  # noqa

    #
    # RENDER_CLIENT_MODULE_TS
    #
    def test_render_client_module_ts(self):

        commands_by_domain = {
            Domain('cards', 'Cards Management'): {},
            Domain('paths', 'Path Management'): {},
            Domain('recall', 'Recall Management'): {},
        }
        src_path = str(self.src_dir)

        self.renderer.render_client_module_ts(commands_by_domain)

        assert sorted(os.listdir(src_path)) == [
            'client.module.ts',
            'domains',
            'services',
        ]
        with open(
                os.path.join(src_path, 'client.module.ts'), 'r') as f:
            assert f.read() == normalize_indentation('''
                /**
                  * THIS FILE WAS AUTOGENERATED, ALL MANUAL CHANGES CAN BE
                  * OVERWRITTEN
                  */

                import { NgModule } from '@angular/core';

                /** Domains */
                import { CardsDomain } from './domains/cards/index';
                import { PathsDomain } from './domains/paths/index';
                import { RecallDomain } from './domains/recall/index';

                /** Services */
                import { APIService } from './services/api.service';

                @NgModule({
                    providers: [
                        // Domains
                        CardsDomain,
                        PathsDomain,
                        RecallDomain,

                        // Facade
                        APIService,
                    ]
                })
                export class ClientModule {}
            ''', 0)  # noqa
