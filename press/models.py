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
        self.tag = element_name
        self.text = ''
        self.tail = ''
        self.parent = None
        self.__children = []
        self.attrib = dict(attrs)

    def __repr__(self):
        return 'CollectionElement({})'.format(self.tag)

    def __iter__(self):
        return iter(self.__children)

    def __len__(self):
        return len(self.__children)

    def add_child(self, child):
        """Works like append for XML ElementTree-s.
        """
        if isinstance(child, self.__class__):
            child.parent = self
            self.__children.append(child)
            return self
        else:
            raise TypeError("must be of the same type.")

    def traverse(self):
        yield self

        for nested in self:
            yield from nested.traverse()

    def getparent(self):
        return self.parent

    def is_equal_to(self, other):
        """Equality is defined as two collections having the same
        type of tag in the same order and all modules having the same title.
        """
        if self.tag == 'title' and other.tag == 'title':
            # title tags may have nested tags within them,
            # so consider the text in those as well.
            return self._complete_title() == other._complete_title()
        else:
            return self.tag == other.tag

    def insert_text(self, content):
        content = content.strip()
        if bool(self.text):
            self.tail = content
        elif bool(content):
            self.text = content

    def alltext(self):
        text = []
        for t in self.itertext():
            text.append(t)
        return ' '.join(text + [str(self.tail)]).strip()

    def itertext(self):
        tag = self.tag
        if not isinstance(tag, str) and tag is not None:
            return
        if bool(self.text):
            yield self.text
        for node in self:
            for s in node.itertext():
                yield s
            if bool(node.tail):
                yield node.tail

    def _complete_title(self):
        return self.alltext()


class ComparableElement(CollectionElement, set):
    def __init__(self, element_name, attrs):
        super().__init__(element_name, attrs)

    def __hash__():
        return hash((self.tag, self.text, self.tail, frozenset(self.items())))

    def __eq__(self, other):
        return hash(self) == hash(other)
