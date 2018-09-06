from collections import namedtuple


__all__ = ('CollectionMetadata', 'ModuleMetadata',)


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


class CollectionElement:
    """Represents a collxml element parsed from a Collection XML file.
    It is iterable and it is comparable using `is_equal_to`.
    """
    def __init__(self, element_name, attrs):
        self.name = element_name
        self.__children = []
        self.parent = self
        self.text = ''
        # programatically set attributes from data passed-in as a hash
        for k, v in attrs.items():
            uri, localname = k
            setattr(self, localname, v)

    def __repr__(self):
        return 'Element({})'.format(self.name)

    def add_child(self, child):
        """Works like append for XML ElementTree-s.
        """
        if isinstance(child, self.__class__):
            child.parent = self
            self.__children.append(child)
            return self
        else:
            raise Exception("must be of the same type.")

    def __iter__(self):
        return iter(self.__children)

    def __len__(self):
        return len(self.__children)

    def traverse(self):
        yield self

        for nested in self:
            yield from nested.traverse()

    def getparent(self):
        return self.parent

    def is_equal_to(self, other):
        """Equality is defined as two collections having the same
        (type of) elements in the same order and all modules having
        the same title.
        """
        if self.name == 'title' and other.name == 'title':
            # title tags may have nested tags within them,
            # so consider the text in those as well.
            return self._complete_title() == other._complete_title()
        else:
            return self.name == other.name

    def _complete_title(self):
        return ' '.join([node.text for node in self.traverse()])
