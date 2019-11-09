
import glob
import importlib
import json
import os
import re

from lily_assistant.config import Config
import djclick as click


class Renderer:

    def render(self):

        dependencies = self.get_dependencies(
            self.get_most_current_migrations())

        return {
            'plan': self.get_migrations_plan(dependencies),
            'dependencies': {
                '.'.join(k): list(v)
                for k, v in dependencies.items()
            },
        }

    def get_most_current_migrations(self):
        base_path = os.path.join(os.getcwd(), Config().src_dir)

        filenames = glob.glob(os.path.join(base_path, '**/migrations/*.py'))
        filenames = [f for f in filenames if re.search(r'\d+\w+\.py$', f)]
        filenames = sorted(filenames, reverse=True)

        most_current_migrations = []
        apps_visited = set()
        for f in filenames:
            module = f
            module = re.sub(f'{os.getcwd()}/', '', module)
            module = re.sub(r'(.py$|\.\/)', '', module)
            module = re.sub(r'\/', '.', module)
            module_parts = module.split('.')

            app_name, migration = module_parts[-3], module_parts[-1]

            if app_name not in apps_visited:
                apps_visited.add(app_name)
                most_current_migrations.append((app_name, migration, module))

        return most_current_migrations

    def get_dependencies(self, most_current_migrations):

        return {
            (app_name, migration): set(
                importlib.import_module(module).Migration.dependencies)
            for app_name, migration, module in most_current_migrations
        }

    def get_migrations_plan(self, dependencies):

        all_migrations = sorted(dependencies.keys())
        migrations_plan = []
        while all_migrations:
            current_migration = all_migrations.pop(0)

            if current_migration not in migrations_plan:
                deps = dependencies.get(current_migration)

                # -- if has no dependencies OR
                # -- all of it's dependencies are already in the
                # -- `migrations_plan`
                sub_deps = deps & set(dependencies.keys())
                if not deps or sub_deps.issubset(set(migrations_plan)):
                    migrations_plan.append(current_migration)

                else:
                    all_migrations.append(current_migration)

        return migrations_plan


@click.command()
def command():

    config = Config()

    migrations_dir_path = os.path.join(config.get_lily_path(), 'migrations')
    if not os.path.exists(migrations_dir_path):
        os.mkdir(migrations_dir_path)

    version = config.next_version or config.version
    migrations_path = os.path.join(migrations_dir_path, f'{version}.json')
    with open(migrations_path, 'w') as f:
        f.write(json.dumps(Renderer().render(), indent=4, sort_keys=False))

    click.secho(
        f'Migrations plan rendered for to file {migrations_path}',
        fg='green')
