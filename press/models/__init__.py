from collections import namedtuple

from .press_element import PressElement

__all__ = (
    'CollectionMetadata',
    'ModuleMetadata',
    'PressElement',
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
