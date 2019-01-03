from press.errors import AttributeDoesNotExist


class PressElement:
    """Represents a collxml element parsed from a Collection XML file.
    """
    def __init__(self, tag, attrs=None, text='', tail=''):
        self.tag = tag  # TODO: prevent whitespace in tag name / VALIDATE tag
        self.text = text
        self.tail = tail
        self.attrs = (attrs and attrs.copy()) or {}
        self.children = []
        self.parent = None

    """Make it hashable so that we can convert the tree to a set and then use
    set operations.
    """
    def __hash__(self):
        module_id = self.attrs.get('document', '')
        return hash((self.tag, self.text, self.tail, module_id))

    def __eq__(self, other):
        return hash(self) == hash(other)

    """Represent a tag as it would appear in the source collxml file,
    with the exception that this also includes the trailing text (``tail``)
    prepended with ``...`` (ellipsis).
    """
    def __repr__(self):
        text = self.text or ''
        tail = self.tail and '...{}'.format(self.tail) or ''
        keyvals = [' %s="%s"' % item for item in self.attrs.items()]
        attr_str = ''.join(keyvals)
        return '<%s%s>%s</%s>' % (self.tag, attr_str, text + tail, self.tag)

    def __str__(self):
        text = self.text or ''
        tail = self.tail and '...{}'.format(self.tail) or ''
        keyvals = [' %s="%s"' % item for item in self.attrs.items()]
        attr_str = ''.join(keyvals)
        return '<%s%s>%s</%s>' % (self.tag, attr_str, text + tail, self.tag)

    """Easy way to get an element's (direct, not deeply nested) child by name.
    """
    def __getitem__(self, name):
        ch = dict()
        tags = [c.tag for c in self.children]

        for child in self.children:
            if tags.count(name) > 1:  # more than 1 child with the same name
                ch[child.tag] = [c for c in self.children if c.tag == name]
            else:
                ch[child.tag] = child
        # FIXME: perhaps we can improve error messaging by returning
        #        something other than None
        default = None
        return ch.get(name, default)

    def __getattr__(self, name):
        item = self.__getitem__(name)
        if item:  # see: __bool__
            return item
        else:
            raise AttributeDoesNotExist()

    """Make its length be the length of its children."""
    def __len__(self):
        return len(self.children)

    # https://docs.python.org/3/reference/datamodel.html#object.__bool__
    def __bool__(self):
        return True

    """Make it iterable, see also ``iter()``"""
    def __iter__(self):
        return iter(self.children)

    def iter(self, tag=None):
        if tag == '*':
            tag = None
        if tag is None or self.tag == tag:
            yield self

        for child in self:
            yield from child.iter(tag)

    def find(self, tag=None):
        # returns the first matching element within self where tag == tag
        try:
            return tuple(self.iter(tag))[0]
        except IndexError:
            return None  # not found

    def findall(self, tag=None):
        return tuple(self.iter(tag))

    def find_by_path(self, path):
        path = path.strip('/')
        targets = path.split('/')
        found = None
        for target in targets:
            for elem in self.iter(target):
                if target == elem.tag:
                    found = elem
                    break
        return found

    """Make it a tree"""
    def add_child(self, child):
        # Works like append for XML ElementTree-s
        child.parent = self
        self.children.append(child)
        return self

    def insert_text(self, content):
        content = content.strip()
        if self.text and content:  # if it's already got text, it's a tail.
            return PressElement(self.tag, attrs=self.attrs, text=self.text,
                                tail=content)
        else:
            return PressElement(self.tag, attrs=self.attrs, text=content)

    def _itertext(self):
        if self.text:
            yield self.text
        for e in self:
            for s in e._itertext():
                yield s
            if e.tail:
                yield e.tail

    def alltext(self):
        text = [t for t in self._itertext()]
        title_as_string = ' '.join(text + [self.tail or '']).strip()
        return title_as_string

    def child_number(self, pos):
        try:
            return self.children[pos - 1]
        except IndexError:
            return None

    def attr(self, attr_name):
        default = None
        return self.attrs.get(attr_name, default)
