
import json
import os

from lily_assistant.config import Config

from lily.base.events import EventFactory
from .command import Command
from lily.base.utils import normalize_indentation
from .repo import AngularRepo, AngularHTTPRepo, TemplateRepo
from .domain import Domain
from .utils import to_camelcase


class local_cwd:  # noqa

    def __init__(self, cwd):
        self.cwd = cwd

    def __enter__(self):
        self.current_cwd = os.getcwd()
        os.chdir(self.cwd)

    def __exit__(self, *args, **kwargs):
        os.chdir(self.current_cwd)


class AngularClientRenderer(EventFactory):

    AUTOGENERATED_DOC = normalize_indentation('''
        /**
          * THIS FILE WAS AUTOGENERATED, ALL MANUAL CHANGES CAN BE
          * OVERWRITTEN
          */
    ''', 0)

    def __init__(self, client_origin, client_prefix):
        # -- source repo
        self.template_repo = TemplateRepo()

        self.http_repo = AngularHTTPRepo()

        # -- target repo
        self.repo = AngularRepo(client_origin)
        self.client_prefix = client_prefix

    #
    # MAIN
    #
    def render(
            self,
            only_build=False,
            include_domains=None,
            exclude_domains=None):

        root_cwd = os.getcwd()

        # -- save it now before all directory jumps
        config = Config()

        # -- HTTP client
        self.http_repo.cd_to_repo()
        self.http_repo.clone()
        self.http_repo.install()
        self.http_repo.build()
        self.http_repo.link()

        # -- pull newest changes to the template
        self.template_repo.clone()

        # -- copy its content to the temp directory into which client will get
        # -- render
        self.repo.clone()

        self.template_repo.copy_to(self.repo.base_path, self.client_prefix)
        self.repo.cd_to_repo()
        self.repo.install()
        self.repo.link()

        # -- render domains
        with local_cwd(root_cwd):
            commands_by_domain = self.group_commands_by_domain(
                include_domains, exclude_domains)

        # -- render client
        self.render_client_module_ts(commands_by_domain)
        self.render_api_ts(commands_by_domain)
        self.render_api_index_ts(commands_by_domain)

        # -- particular domains
        all_commands = []
        for domain, commands in commands_by_domain.items():
            sorted_commands = []
            for command_name in sorted(commands.keys()):
                sorted_commands.append(commands[command_name])

            self.render_domain(domain, sorted_commands)
            all_commands.extend(sorted_commands)

        # -- enums - must be run after domains rendering since it
        # -- renders enums
        self.render_enums_ts(all_commands)

        self.repo.build()

        if not only_build:
            next_version = self.repo.upgrade_version(config)

            self.repo.add_all()
            self.repo.commit(next_version)
            self.repo.push()

            return next_version

    def group_commands_by_domain(
            self, include_domains=None, exclude_domains=None):

        include_domains = include_domains or []
        include_domains = [d.lower() for d in include_domains]
        exclude_domains = exclude_domains or []
        exclude_domains = [d.lower() for d in exclude_domains]

        commands_by_domain = {}
        for name, conf in self.get_commands().items():
            if name == '@enums':
                continue

            command = Command(name, conf)

            # -- skip excluded domains
            if command.domain_id.lower() in exclude_domains:
                continue

            # -- skip not included domains
            if (include_domains and
                    command.domain_id.lower() not in include_domains):
                continue

            domain = Domain(command.domain_id, command.domain_name)

            if not command.is_private:
                commands_by_domain.setdefault(domain, {})
                commands_by_domain[domain][name] = command

        return commands_by_domain

    def get_commands(self):

        commands_path = os.path.join(
            Config.get_lily_path(),
            'commands',
            f'{Config().version}.json')
        with open(commands_path, 'r') as f:
            return json.loads(f.read())

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

        # -- RENDER ACCESS TS
        self.render_access_ts(domain, commands)

    def render_index_ts(self, domain):
        with open(domain.path.join('index.ts'), 'w') as f:
            f.write(
                normalize_indentation('''
                    export * from './{domain.id}.domain';
                    export * from './{domain.id}.models';
                ''', 0).format(domain=domain))

    def render_models_ts(self, domain, commands):

        model_enums = []
        models = []
        for command in commands:
            # -- REQUEST_QUERY
            b, enums = command.request_query.render()
            if b:
                models.append(b)

            if enums:
                model_enums.extend(enums)

            # -- REQUEST_BODY
            b, enums = command.request_body.render()
            if b:
                models.append(b)

            if enums:
                model_enums.extend(enums)

            # -- RESPONSE
            b, enums = command.response.render()
            if b:
                models.append(b)

            if enums:
                model_enums.extend(enums)

        enums_block = ''
        if model_enums:
            sorted_enum_names = sorted(set([e.name for e in model_enums]))

            enums_block = normalize_indentation('''
                import {{ {enums} }} from '../../shared/enums';
            ''', 0).format(enums=', '.join(sorted_enum_names))

        blocks = [
            normalize_indentation('''
                {autogenerated_doc}

                {enums_block}

                /**
                 * {domain_name} Domain Models
                 */
            ''', 0).format(
                enums_block=enums_block,
                autogenerated_doc=self.AUTOGENERATED_DOC,
                domain_name=domain.name),
            *models,
        ]

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

                import {{ HttpService }} from '@lily/http';

                import * as X from './{domain.id}.models';

                @Injectable()
                export class {domain.camel_id}Domain {{
                    constructor(private client: HttpService) {{}}
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

    def render_access_ts(self, domain, commands):
        header = normalize_indentation('''
            {autogenerated_doc}

            /**
             * {domain.name} Domain Access
             */
        ''', 0).format(  # noqa
            autogenerated_doc=self.AUTOGENERATED_DOC,
            domain=domain)

        blocks = [command.render_access() for command in commands]
        blocks = '\n'.join([f'  {b},' for b in blocks])
        path = domain.path.join('{}.access.ts'.format(domain.id))

        domain_id = to_camelcase(domain.id)
        with open(path, 'w') as f:
            f.write(
                f'{header}\n\n'
                f'export const {domain_id}Access = {{\n'
                f'{blocks}\n'
                '}')

    def render_enums_ts(self, all_commands):

        enums = self.collect_unique_enums(all_commands)

        blocks = [enum.render() for enum in enums]

        rel_path = './projects/client/src/shared'
        self.repo.create_dir(rel_path)

        abs_path = os.path.join(self.repo.base_path, rel_path)
        with open(os.path.join(abs_path, 'enums.ts'), 'w') as f:
            f.write('\n\n'.join(blocks))

    def collect_unique_enums(self, all_commands):

        all_enums = []

        for command in all_commands:
            command.request_query.render()
            command.request_body.render()
            command.response.render()

            all_enums.extend(command.request_query.enums)
            all_enums.extend(command.request_body.enums)
            all_enums.extend(command.response.enums)

        unique_enums = {}
        inconsistent_enums = []
        for maybe in all_enums:
            is_unique = True
            for unique_enum in unique_enums.values():
                if unique_enum == maybe:
                    is_unique = False
                    break

            if is_unique:
                # -- search for inconsistent duplicates
                if unique_enums.get(maybe.name):
                    existing = unique_enums[maybe.name]

                    inconsistent_enums.append({
                        'enum.0': {
                            'name': existing.name,
                            'values': list(existing.values),
                        },
                        'enum.1': {
                            'name': maybe.name,
                            'values': list(maybe.values),
                        },
                    })

                else:
                    unique_enums[maybe.name] = maybe

        if inconsistent_enums:
            raise self.ServerError(
                'INCONSISTENT_ENUMS_DETECTED',
                data={'inconsistent_enums': inconsistent_enums})

        return sorted(
            unique_enums.values(),
            key=lambda x: (x.name, x.index))

    #
    # API Service
    #
    def render_api_index_ts(self, commands_by_domain):

        blocks = []
        for domain in sorted(commands_by_domain.keys(), key=lambda x: x.id):
            blocks.append(
                "export * from './{domain.id}/index';".format(domain=domain))

        path = os.path.join(
            self.repo.base_path,
            'projects/client/src/domains/index.ts')
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

                import {{ Options }} from '@lily/http';

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
            self.repo.base_path,
            'projects/client/src/services/api.service.ts')
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
                ''', 8).format(domain=domain))

        blocks = [
            normalize_indentation('''
                {autogenerated_doc}

                import {{ NgModule }} from '@angular/core';

                /** Domains */
                {domains_imports}

                /** Services */
                import {{ APIService }} from './services/api.service';

                @NgModule({{
                    providers: [
                        // Domains
                {domains_list}

                        // Facade
                        APIService,
                    ]
                }})
                export class ClientModule {{}}
            ''', 0).format(  # noqa
                autogenerated_doc=self.AUTOGENERATED_DOC,
                domains_imports='\n'.join(domains_imports),
                domains_list='\n'.join(domains_list))
        ]

        path = os.path.join(
            self.repo.base_path,
            'projects/client/src/client.module.ts')
        with open(path, 'w') as f:
            f.write('\n\n'.join(blocks))
