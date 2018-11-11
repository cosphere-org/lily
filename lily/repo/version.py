

class VersionRenderer:

    class VERSION_UPGRADE:  # noqa
        MAJOR = 'MAJOR'

        MINOR = 'MINOR'

        PATCH = 'PATCH'

    def render_next_version(
            self, current_version, upgrade_type=VERSION_UPGRADE.PATCH):

        major, minor, patch = current_version.split('.')
        major, minor, patch = int(major), int(minor), int(patch)

        if upgrade_type == self.VERSION_UPGRADE.MAJOR:
            major += 1
            minor = 0
            patch = 0

        elif upgrade_type == self.VERSION_UPGRADE.MINOR:
            minor += 1
            patch = 0

        elif upgrade_type == self.VERSION_UPGRADE.PATCH:
            patch += 1

        return '{0}.{1}.{2}'.format(major, minor, patch)
