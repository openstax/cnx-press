import io
from collections import namedtuple

from litezip import Collection, Module

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
    new_litezip = []
    for model in litezip_struct:
        if model.resources:
            new_resources = []
            for res_filepath in model.resources:
                if isinstance(res_filepath, Resource):
                    # It's actually already a Resource, so leave it as is.
                    new_resources.append(res_filepath)
                    continue
                media_type = magic.from_file(str(res_filepath), mime=True)
                sha1 = produce_hashes_from_filepath(res_filepath)['sha1']
                with res_filepath.open('rb') as fb:
                    new_resources.append(Resource(
                        io.BytesIO(fb.read()),
                        res_filepath.name,
                        media_type,
                        sha1,
                    ))
            if isinstance(model, Collection):
                new_litezip.append(Collection(
                    model.id,
                    model.file,
                    tuple(new_resources)
                ))
            else:  # Module
                new_litezip.append(Module(
                    model.id,
                    model.file,
                    tuple(new_resources)
                ))
        else:
            new_litezip.append(model)
    return tuple(new_litezip)
