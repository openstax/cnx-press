import io
from collections import namedtuple

import magic

from press.utils import produce_hashes_from_filepath


__all__ = (
    'convert_litezip_resources',
    'CollectionMetadata',
    'ModuleMetadata',
)


CollectionMetadata = namedtuple(
    'CollectionMetadata',
    ('id version created revised title '
     'license_url language print_style '
     'authors maintainers licensors '
     'keywords subjects abstract'),
)

ModuleMetadata = namedtuple(
    'ModuleMetadata',
    ('id version created revised title '
     'license_url language '
     'authors maintainers licensors '
     'keywords subjects abstract'),
)


Resource = namedtuple(
    'Resource',
    ('data filename media_type sha1'),
)


def convert_litezip_resources(litezip_struct):
    """Converts the resources within a litezip structure of data
    to :class:`Resource` instances rather than simple :class:`pathlib.Path`
    instances.

    """
    for model in litezip_struct:
        for i, res_filepath in enumerate(model.resources):
            if isinstance(res_filepath, Resource):
                # It's actually already a Resource, so leave it as is.
                continue
            media_type = magic.from_file(str(res_filepath), mime=True)
            sha1 = produce_hashes_from_filepath(res_filepath)['sha1']
            with res_filepath.open('rb') as fb:
                model.resources[i] = Resource(
                    io.BytesIO(fb.read()),
                    res_filepath.name,
                    media_type,
                    sha1,
                )
    # This function side-effect oriented, but still returns the given object
    return litezip_struct
