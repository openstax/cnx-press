__all__ = (
    'convert_version_to_legacy_version',
)


def convert_version_to_legacy_version(version):
    """Converts a version to a legacy version.

    :param version: content's major and minor version
    :type version: tuple of int

    """
    return '1.{}'.format(version[0])
