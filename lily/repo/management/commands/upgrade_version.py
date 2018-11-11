
import djclick as click

from ...repo import Repo
from ...version import VersionRenderer
from ...changelog import ChangelogRenderer
from lily.base.conf import Config
from lily.base.utils import normalize_indentation


@click.command()
@click.argument('upgrade_type', type=click.Choice([
    VersionRenderer.VERSION_UPGRADE.MAJOR,
    VersionRenderer.VERSION_UPGRADE.MINOR,
    VersionRenderer.VERSION_UPGRADE.PATCH,
]))
def command(upgrade_type):
    """
    Upgrade version of the repo and perform the following extra activities:

    - tag branch with the version of repo

    - update config.yaml file with version and last_commit_hash

    - push changes to the remote

    - update CHANGELOG with the compilation of messages coming from the
      previous commit messages [TO BE ADDED]

    """
    config = Config()
    repo = Repo()
    changelog = ChangelogRenderer()
    version = VersionRenderer()

    # -- version
    config.version = version.render_next_version(
        config.version, upgrade_type)

    # -- last_commit_hash
    config.last_commit_hash = repo.current_commit_hash

    # -- changelog
    changelog.render()

    # -- push all changed files
    repo.add(config.path)
    repo.commit('VERSION: {}'.format(config.version))
    repo.push()

    # -- tag
    repo.tag(config.version)

    click.secho(normalize_indentation('''
        - Version upgraded to: {version}
        - branch tagged
        - CHANGELOG rendered
    '''.format(version=config.version), 0), fg='green')
