# -*- coding: utf-8 -*-

import os
import re

from django.test import TestCase
import pytest
from mock import call, Mock

from lily.docs.renderers.angular.renderer import AngularClientRenderer
from lily.docs.renderers.angular.domain import Domain
from lily.docs.renderers.angular.repo import Repo
from lily.docs.renderers.angular.utils import normalize_indentation


def remove_white_chars(text):
    return re.sub(r'\s+', '', text)


class AngularClientRendererTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initfixture(self, mocker, tmpdir):
        self.mocker = mocker
        self.tmpdir = tmpdir

        self.base_dir = self.tmpdir.mkdir('cosphere-angular-client')
        self.src_dir = self.base_dir.mkdir('src')
        self.domains_dir = self.src_dir.mkdir('domains')
        self.services_dir = self.src_dir.mkdir('services')

        self.mocker.patch.object(Repo, 'base_path', str(self.base_dir))

    def setUp(self):
        self.renderer = AngularClientRenderer()

    #
    # group_commands_by_domain
    #
    def test_group_commands_by_domain(self):
        pass

    #
    # render_domain
    #
    def test_render_domain(self):

        render_index_ts = self.mocker.patch.object(
            AngularClientRenderer, 'render_index_ts')
        render_models_ts = self.mocker.patch.object(
            AngularClientRenderer, 'render_models_ts')
        render_domain_ts = self.mocker.patch.object(
            AngularClientRenderer, 'render_domain_ts')
        domain = Domain('cards', 'Cards Management')

        domains_path = str(self.domains_dir)

        assert os.listdir(domains_path) == []

        self.renderer.render_domain(domain, [])

        assert os.listdir(domains_path) == ['cards']
        assert render_index_ts.call_args_list == [call(domain)]
        assert render_models_ts.call_args_list == [call(domain, [])]
        assert render_domain_ts.call_args_list == [call(domain, [])]

    #
    # render_index_ts
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
    # render_models_ts
    #
    def test_render_models_ts(self):
        paths_path = str(self.domains_dir.mkdir('paths'))
        domain = Domain('paths', 'Path Management')
        commands = [
            Mock(
                request_query=Mock(render=Mock(return_value='request 1')),
                request_body=Mock(render=Mock(return_value='')),
                response=Mock(render=Mock(return_value='response 1')),
            ),
            Mock(
                request_query=Mock(render=Mock(return_value='request 2')),
                request_body=Mock(render=Mock(return_value='')),
                response=Mock(render=Mock(return_value='response 2')),
            ),
        ]

        assert os.listdir(paths_path) == []

        self.renderer.render_models_ts(domain, commands)

        assert os.listdir(paths_path) == ['paths.models.ts']
        with open(os.path.join(paths_path, 'paths.models.ts'), 'r') as f:
            assert f.read() == normalize_indentation('''
                /**
                 * Path Management Domain Models
                 */

                request 1

                response 1

                request 2

                response 2
            ''', 0)

    #
    # render_domain_ts
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
                 * Path Management Domain
                 */
                import { Injectable } from '@angular/core';
                import { filter } from 'rxjs/operators';
                import { Observable } from 'rxjs';
                import * as _ from 'underscore';

                import { ClientService, DataState } from '../../services/client.service';
                import * from './paths.model';

                @Injectable()
                export class PathsDomain {
                    constructor(private client: ClientService) {}

                    command 1

                    command 2

                }
            ''', 0)  # noqa

    #
    # render_api_ts
    #
    def test_render_api_ts(self):

        command = lambda x: Mock(render_facade=Mock(return_value=x))
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
                 * Facade Service for all domains
                 */
                import { Injectable, Injector } from '@angular/core';
                import { Observable } from 'rxjs';

                import { DataState, Options } from './index';

                import * from '../domains/cards/index';
                import * from '../domains/paths/index';

                @Injectable()
                export class APIService {

                    constructor(private injector: Injector) {}

                    /**
                     * Cards Management domain
                     */
                    private _cardsDomain: CardsDomain;

                    public get cardsDomain(): CardsDomain {
                        if (!this._cardsDomain) {
                            this._cardsDomain = this.injector.get(CardsDomain);
                        }

                        return this._cardsDomain;
                    }

                    <DELETE_CARD>

                    <READ_CARDS>

                    /**
                     * Path Management domain
                     */
                    private _pathsDomain: PathsDomain;

                    public get pathsDomain(): PathsDomain {
                        if (!this._pathsDomain) {
                            this._pathsDomain = this.injector.get(PathsDomain);
                        }

                        return this._pathsDomain;
                    }

                    <CREATE_PATH>

                }
            ''', 0))  # noqa
