import hashlib


__all__ = (
    'convert_to_legacy_domain',
    'convert_version_tuple_to_version_string',
    'convert_version_to_legacy_version',
    'produce_hashes_from_filepath',
)


BUFFER_CHUNK_SIZE = 131072  # 128kb chunks


def convert_version_tuple_to_version_string(version):
    """Converts a version tuple to a version string.

    :param version: content's major and minor version
    :type version: tuple of int

    """
    return '.'.join([str(vv) for vv in version if vv])


def convert_version_to_legacy_version(version):
    """Converts a version to a legacy version.

    :param version: content's major and minor version
    :type version: tuple of int

    """
    return '1.{}'.format(version[0])


def convert_to_legacy_domain(domain):
    """Given the existing domain, convert it to the legacy domain."""
    sep = len(domain.split('.')) > 2 and '-' or '.'
    return 'legacy{}{}'.format(sep, domain)


def produce_hashes_from_filepath(filepath):
    """Given a filepath to a file, produce the SHA1 and MD5 for that file.

    :param filepath: a filesystem path to the file
    :type filepath: :class:`pathlib.Path`

    """
    sha1 = hashlib.sha1()
    md5 = hashlib.md5()
    with filepath.open('rb') as fb:
        while True:
            data = fb.read(BUFFER_CHUNK_SIZE)
            if not data:
                break
            sha1.update(data)
            md5.update(data)
    return {
        'sha1': sha1.hexdigest(),
        'md5': md5.hexdigest(),
    }
