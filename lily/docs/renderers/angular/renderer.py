# -*- coding: utf-8 -*-

import logging
import os
import json

from django.conf import settings

from lily.base.events import EventFactory
from .command import Command
from .utils import normalize_indentation
from .repo import Repo
from .domain import Domain


logger = logging.getLogger()


event = EventFactory(logger)


class AngularClientRenderer:

    def __init__(self):
        self.repo = Repo()

    # FIXME: test it!!!!
    def group_commands_by_domain(self):

        commands_by_domain = {}
        for filepath in settings.LILY_COMMAND_ENTRYPOINTS:
            with open(filepath, 'r') as f:
                content = json.loads(f.read())
                for name, conf in content['commands'].items():
                    command = Command(name, conf)
                    domain = Domain(command.domain_id, command.domain_name)

                    commands_by_domain.setdefault(domain, {})

                    if not command.is_private:
                        if commands_by_domain[domain].get(name):
                            raise event.ServerError(
                                'DUPLICATE_PIBLIC_DOMAIN_COMMAND_DETECTED',
                                data={
                                    'command_name': name,
                                    'domain_id': domain
                                })

                        else:
                            commands_by_domain[domain][name] = command

        return commands_by_domain

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

    def render_index_ts(self, domain):
        with open(domain.path.join('index.ts'), 'w') as f:
            f.write(
                normalize_indentation('''
                    export * from './{domain_id}.domain';
                    export * from './{domain_id}.models';
                ''', 0).format(domain_id=domain.id))

    def render_models_ts(self, domain, commands):
        blocks = [
            normalize_indentation('''
                /**
                 * {domain_name} Domain Models
                 */
            ''', 0).format(domain_name=domain.name)
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
                /**
                 * {domain_name} Domain
                 */
                import {{ Injectable }} from '@angular/core';
                import {{ filter }} from 'rxjs/operators';
                import {{ Observable }} from 'rxjs';
                import * as _ from 'underscore';

                import {{ ClientService, DataState }} from '../../services/client.service';
                import * from './{domain_id}.model';

                @Injectable()
                export class {domain_camel_id}Domain {{
                    constructor(private client: ClientService) {{}}
            ''', 0).format(  # noqa
                domain_name=domain.name,
                domain_id=domain.id,
                domain_camel_id=domain.camel_id,
            )
        ]
        for command in commands:
            blocks.append(normalize_indentation(command.render(), 4))

        blocks.append('}')

        path = domain.path.join('{}.domain.ts'.format(domain.id))
        with open(path, 'w') as f:
            f.write('\n\n'.join(blocks))

    #
    # API Service
    #
    def render_api_ts(self, commands_by_domain):
        domain_imports = []
        for domain in commands_by_domain.keys():
            domain_imports.append(normalize_indentation('''
            import * from '../domains/{domain_id}/index';

            ''', 0).format(domain_id=domain.id))

        blocks = [
            normalize_indentation('''
                /**
                 * Facade Service for all domains
                 */
                import {{ Injectable, Injector }} from '@angular/core';
                import {{ Observable }} from 'rxjs';

                import {{ DataState, Options }} from './index';

                {domain_imports}

                @Injectable()
                export class APIService {{

                    constructor(private injector: Injector) {{}}

            ''', 0).format(domain_imports='\n'.join(sorted(domain_imports)))
        ]

        for domain in sorted(commands_by_domain.keys(), key=lambda x: x.id):
            commands = commands_by_domain[domain]
            blocks.append(normalize_indentation('''
                /**
                 * {domain_name} domain
                 */
                private _{domain_id}Domain: {domain_camel_id}Domain;

                public get {domain_id}Domain(): {domain_camel_id}Domain {{
                    if (!this._{domain_id}Domain) {{
                        this._{domain_id}Domain = this.injector.get({domain_camel_id}Domain);
                    }}

                    return this._{domain_id}Domain;
                }}
            ''', 4).format(  # noqa
                domain_name=domain.name,
                domain_id=domain.id,
                domain_camel_id=domain.camel_id,
            ))

            for command_name in sorted(commands.keys()):
                command = commands[command_name]
                blocks.append(command.render_facade())

        blocks.append('}')

        path = os.path.join(
            self.repo.base_path, 'src/services/api.service.ts')
        with open(path, 'w') as f:
            f.write('\n\n'.join(blocks))

    # FIXME: test it!!!!
    def render(self):
        self.repo.pull()
        self.repo.install()

        # -- render domains
        commands_by_domain = self.group_commands_by_domain()
        self.render_api_ts(commands_by_domain)
        for domain, commands in commands_by_domain.items():
            self.render_domain(domain, commands.values())

        # !!!!!!!!!!!!
        # FIXME: make it dynamical based on the versions of services
        next_version = self.repo.upgrade_version(
            self.repo.VERSION_UPGRADE.MINOR)

        self.repo.build()
        self.repo.add_all()
        self.repo.commit(next_version)
        self.repo.push()


if __name__ == '__main__':
    renderer = AngularClientRenderer()
    renderer.render()
