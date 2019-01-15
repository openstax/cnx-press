from litezip.main import COLLECTION_NSMAP
from press.models import PressElement
from press.parsers import parse_collxml
from tests.helpers import element_tree_from_model


def gen_press_element_tree():
    collection = PressElement('collection')
    collection.add_child(PressElement('mod1'))
    collection.add_child(PressElement('mod2'))
    collection.add_child(PressElement('mod3'))
    collection.add_child(PressElement('mod4'))
    child3 = collection.child_number(3)
    child3.add_child(PressElement('mod3--1'))
    child3.add_child(PressElement('mod3--2'))
    return collection


def test_string_representation():
    attrs = {'some-attr': 'somevalue', 'version': '1.1'}
    attrs_str = 'some-attr="somevalue" version="1.1"'
    content = 'Text and... trailing text!'
    expected = '<sometag %s>%s</sometag>' % (attrs_str, content)
    element = PressElement('sometag', text='Text and', tail=' trailing text!',
                           attrs=attrs)

    assert repr(element) == expected

    assert repr(PressElement('tagname')) == '<tagname></tagname>'
    assert str(PressElement('tagname')) == '<tagname></tagname>'
    assert str(PressElement('tagname', text='Yes')) == '<tagname>Yes</tagname>'


def test_find_method(content_util):
    """Test that you can look at only part of the tree like `content` tag,
    and be able to differentiate between the coll's title and modules' titles
    """
    expected = "The Collection's Title"
    collection, tree, _ = content_util.gen_collection()

    with element_tree_from_model(collection) as x:
        el = x.xpath('//col:metadata/md:title', namespaces=COLLECTION_NSMAP)[0]
        el.text = expected  # TARGET

    tree = parse_collxml(collection.file.open('rb'))
    actual = tree.find('title')  # the first title is the collection's.

    assert actual.text == expected


def test_finding_by_path(content_util):
    expected = 'http://cnx.org/content'

    collection, tree, _ = content_util.gen_collection()
    tree = parse_collxml(collection.file.open('rb'))

    title = tree.find_by_path('collection/metadata/repository').text
    assert title == expected


def test_tree_behavior(content_util):
    """Test that you can insert a child or children
    """
    collection = gen_press_element_tree()

    col_children = ['<mod1></mod1>', '<mod2></mod2>', '<mod3></mod3>',
                    '<mod4></mod4>']
    mod3_children = ['<mod3--1></mod3--1>', '<mod3--2></mod3--2>']
    assert [str(c) for c in collection.children] == col_children
    assert [str(c) for c in mod3_children] == mod3_children


def test_iterator_behavior():
    """You can iterate through the tree depth-first.
    """
    actual = gen_press_element_tree()

    expected = ['<collection></collection>',
                '<mod1></mod1>',
                '<mod2></mod2>',
                '<mod3></mod3>',
                '<mod3--1></mod3--1>', '<mod3--2></mod3--2>',
                '<mod4></mod4>']

    for actual, ex in zip(actual.iter(), expected):
        assert str(actual) == ex


def test_equality_behavior():
    """A Node can be compared against another using the == operator
    (or another as a last resort).
    """
    attrs = {'someattribrute': '_the_value_'}
    a = PressElement('someelement', text='ciao', tail='papaya', attrs=attrs)
    b = PressElement('someelement', text='ciao', tail='papaya', attrs=attrs)

    # this would fail if we hadn't defined __hash__ and __eq__
    assert a == b

    """Modules with a different ``document`` attribute do not equal
    """
    attrs = {'document': 'm00004'}
    a = PressElement('md', text='TxT', tail='TaiL', attrs=attrs)
    attrs = {'document': 'm00005'}
    b = PressElement('md', text='TxT', tail='TaiL', attrs=attrs)
    assert a != b


def test_objectified_magic():
    """Test the ability to access a nested element by simply calling an
    attribute on the tree/element.
    """
    title = PressElement('title', text='Collection Title')
    anothertag = PressElement('anothertag')
    anothertag.add_child(title)
    metadata = PressElement('metadata', text='text within md tag')
    metadata.add_child(anothertag)
    collection = PressElement('collection')
    collection.add_child(metadata)
    """
    collection
        => metadata
            => anothertag
                => title
    """
    assert collection.metadata.anothertag.title.text == 'Collection Title'


# https://github.com/openstax/cnx-press/issues/347
def test_alltext_when_element_not_found():
    assert PressElement('sometag').find('nonExistentTag123').alltext() == ''
