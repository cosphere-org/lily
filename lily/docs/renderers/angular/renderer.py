# -*- coding: utf-8 -*-

import logging
import os

from django.conf import settings
import requests

from lily.base.events import EventFactory
from lily.repo.version import VersionRenderer
from .command import Command
from lily.base.utils import normalize_indentation
from .repo import AngularRepo
from .domain import Domain


logger = logging.getLogger()


event = EventFactory(logger)


class AngularClientRenderer:

    def __init__(self):
        self.repo = AngularRepo()

    AUTOGENERATED_DOC = normalize_indentation('''
        /**
          * THIS FILE WAS AUTOGENERATED, ALL MANUAL CHANGES CAN BE
          * OVERWRITTEN
          */
    ''', 0)

    #
    # MAIN
    #
    def render(self, only_build=False):
        self.repo.stash()
        self.repo.pull()
        self.repo.install()

        # -- render domains
        commands_by_domain = self.group_commands_by_domain()
        self.render_client_module_ts(commands_by_domain)
        self.render_api_ts(commands_by_domain)
        self.render_api_index_ts(commands_by_domain)
        for domain, commands in commands_by_domain.items():
            sorted_commands = []
            for command_name in sorted(commands.keys()):
                sorted_commands.append(commands[command_name])

            self.render_domain(domain, sorted_commands)

        self.repo.build()

        if not only_build:
            # !!!!!!!!!!!!
            # FIXME: make it dynamical based on the versions of services
            next_version = self.repo.upgrade_version(
                VersionRenderer.VERSION_UPGRADE.MINOR)
            self.repo.add_all()
            self.repo.commit(next_version)
            self.repo.push()

    def group_commands_by_domain(self):

        commands_by_domain = {}
        seen = []
        for entrypoint in self.collect_entrypoints():
            for name, conf in entrypoint['commands'].items():
                command = Command(name, conf)
                domain = Domain(command.domain_id, command.domain_name)

                if not command.is_private:
                    if name in seen:
                        raise event.ServerError(
                            'DUPLICATE_PUBLIC_DOMAIN_COMMAND_DETECTED',
                            data={
                                'command_name': name,
                                'domain_id': domain.id,
                            })

                    commands_by_domain.setdefault(domain, {})
                    commands_by_domain[domain][name] = command
                    seen.append(name)

        return commands_by_domain

    def collect_entrypoints(self):

        entrypoints = []
        for url in settings.LILY_COMMAND_ENTRYPOINTS:
            response = requests.get(url, params={'with_examples': True})

            if response.status_code != 200:
                raise event.ServerError(
                    'BROKEN_SERVICE_DETECTED',
                    data={'service': url})

            else:
                entrypoints.append(response.json())

        return entrypoints

    #
    # Domain Specific Folder
    #
    def render_domain(self, domain, commands):

        self.repo.create_dir(domain.path.base_path)
        self.repo.clear_dir(domain.path.base_path)

        # -- RENDER INDEX TS
        self.render_index_ts(domain)

        # -- RENDER MODELS TS
        self.render_models_ts(domain, commands)

        # -- RENDER DOMAIN TS
        self.render_domain_ts(domain, commands)

        # -- RENDER EXAMPLES TS
        self.render_examples_ts(domain, commands)

    def render_index_ts(self, domain):
        with open(domain.path.join('index.ts'), 'w') as f:
            f.write(
                normalize_indentation('''
                    export * from './{domain.id}.domain';
                    export * from './{domain.id}.models';
                ''', 0).format(domain=domain))

    def render_models_ts(self, domain, commands):
        blocks = [
            normalize_indentation('''
                {autogenerated_doc}

                /**
                 * {domain_name} Domain Models
                 */
            ''', 0).format(
                autogenerated_doc=self.AUTOGENERATED_DOC,
                domain_name=domain.name)
        ]
        for command in commands:
            blocks.extend([
                b
                for b in [
                    command.request_query.render(),
                    command.request_body.render(),
                    command.response.render(),
                ]
                if b
            ])

        path = domain.path.join('{}.models.ts'.format(domain.id))
        with open(path, 'w') as f:
            f.write('\n\n'.join(blocks))

    def render_domain_ts(self, domain, commands):
        blocks = [
            normalize_indentation('''
                {autogenerated_doc}

                /**
                 * {domain.name} Domain
                 */
                import {{ Injectable }} from '@angular/core';
                import {{ filter }} from 'rxjs/operators';
                import {{ Observable }} from 'rxjs';
                import * as _ from 'underscore';

                import {{ ClientService }} from '../../services/client.service';
                import {{ DataState }} from '../../services/client.interface';

                import * as X from './{domain.id}.models';

                @Injectable()
                export class {domain.camel_id}Domain {{
                    constructor(private client: ClientService) {{}}
            ''', 0).format(  # noqa
                autogenerated_doc=self.AUTOGENERATED_DOC,
                domain=domain,
            )
        ]
        for command in commands:
            blocks.append(normalize_indentation(command.render(), 4))

        blocks.append('}')

        path = domain.path.join('{}.domain.ts'.format(domain.id))
        with open(path, 'w') as f:
            f.write('\n\n'.join(blocks))

    def render_examples_ts(self, domain, commands):
        blocks = [
            normalize_indentation('''
                {autogenerated_doc}

                /**
                 * {domain.name} Domain Examples
                 */
            ''', 0).format(  # noqa
                autogenerated_doc=self.AUTOGENERATED_DOC,
                domain=domain,
            )
        ]
        for command in commands:
            blocks.append(normalize_indentation(command.render_examples(), 0))

        path = domain.path.join('{}.examples.ts'.format(domain.id))
        with open(path, 'w') as f:
            f.write('\n\n'.join(blocks))

    #
    # API Service
    #
    def render_api_index_ts(self, commands_by_domain):

        blocks = []
        for domain in sorted(commands_by_domain.keys(), key=lambda x: x.id):
            blocks.append(
                "export * from './{domain.id}/index';".format(domain=domain))

        path = os.path.join(self.repo.base_path, 'src/domains/index.ts')
        with open(path, 'w') as f:
            f.write('\n'.join(blocks))

    def render_api_ts(self, commands_by_domain):

        blocks = [
            normalize_indentation('''
                {autogenerated_doc}

                /**
                 * Facade API Service for all domains
                 */
                import {{ Injectable, Injector }} from '@angular/core';
                import {{ Observable }} from 'rxjs';

                import {{ DataState, Options }} from './client.interface';

                import * as X from '../domains/index';

                @Injectable()
                export class APIService {{

                    constructor(private injector: Injector) {{}}

            ''', 0).format(autogenerated_doc=self.AUTOGENERATED_DOC,)
        ]

        for domain in sorted(commands_by_domain.keys(), key=lambda x: x.id):
            commands = commands_by_domain[domain]
            blocks.append(normalize_indentation('''
                /**
                 * {domain.name} domain
                 */
                private _{domain.id}Domain: X.{domain.camel_id}Domain;

                public get {domain.id}Domain(): X.{domain.camel_id}Domain {{
                    if (!this._{domain.id}Domain) {{
                        this._{domain.id}Domain = this.injector.get(X.{domain.camel_id}Domain);
                    }}

                    return this._{domain.id}Domain;
                }}
            ''', 4).format(  # noqa
                domain=domain,
            ))

            for command_name in sorted(commands.keys()):
                command = commands[command_name]
                blocks.append(
                    normalize_indentation(command.render_facade(), 4))

        blocks.append('}')

        path = os.path.join(
            self.repo.base_path, 'src/services/api.service.ts')
        with open(path, 'w') as f:
            f.write('\n\n'.join(blocks))

    #
    # Client Module
    #
    def render_client_module_ts(self, commands_by_domain):

        domains_imports = []
        domains_list = []
        for domain in sorted(commands_by_domain.keys(), key=lambda x: x.id):
            domains_imports.append(normalize_indentation('''
                import {{ {domain.camel_id}Domain }} from './domains/{domain.id}/index';
            ''', 0).format(  # noqa
                domain=domain))
            domains_list.append(normalize_indentation('''
                    {domain.camel_id}Domain,
                ''', 16).format(domain=domain))

        blocks = [
            normalize_indentation('''
                {autogenerated_doc}

                import {{ NgModule, ModuleWithProviders }} from '@angular/core';
                import {{ HttpClientModule }} from '@angular/common/http';

                /** Domains */
                {domains_imports}

                /** Services */
                import {{
                  APIService,
                  ClientService,
                  ConfigService,
                  Config
                }} from './services/index';

                @NgModule({{
                  imports: [HttpClientModule]
                }})
                export class ClientModule {{
                    static forRoot(config: Config): ModuleWithProviders {{
                        return {{
                            ngModule: ClientModule,
                            providers: [
                                {{
                                    provide: ConfigService,
                                    useFactory: () => new ConfigService(config)
                                }},
                                ClientService,

                                // Domains
                {domains_list}

                                // Facade
                                APIService,
                            ]
                        }};
                    }}
                }}
            ''', 0).format(  # noqa
                autogenerated_doc=self.AUTOGENERATED_DOC,
                domains_imports='\n'.join(domains_imports),
                domains_list='\n'.join(domains_list))
        ]

        path = os.path.join(self.repo.base_path, 'src/client.module.ts')
        with open(path, 'w') as f:
            f.write('\n\n'.join(blocks))
