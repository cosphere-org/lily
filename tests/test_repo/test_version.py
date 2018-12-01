
import pytest

from lily.repo.version import VersionRenderer


@pytest.mark.parametrize(
    'current_version, upgrade_type, expected',
    [
        # -- patch version upgrade
        ('0.1.11', VersionRenderer.VERSION_UPGRADE.PATCH, '0.1.12'),

        # -- patch version upgrade - triangulation
        ('6.14.23', VersionRenderer.VERSION_UPGRADE.PATCH, '6.14.24'),

        # -- minor version upgrade
        ('0.1.11', VersionRenderer.VERSION_UPGRADE.MINOR, '0.2.0'),

        # -- minor version upgrade - triangulation
        ('6.14.23', VersionRenderer.VERSION_UPGRADE.MINOR, '6.15.0'),

        # -- major version upgrade
        ('0.1.11', VersionRenderer.VERSION_UPGRADE.MAJOR, '1.0.0'),

        # -- major version upgrade - triangulation
        ('6.14.23', VersionRenderer.VERSION_UPGRADE.MAJOR, '7.0.0'),
    ])
def test_repo_upgrade_version(current_version, upgrade_type, expected):

    assert VersionRenderer().render_next_version(
        current_version, upgrade_type) == expected
