from press.models import PressElement
from press.parsers import parse_collxml


def test_dested_text_in_coll_title_gets_parsed(collxml_templates):
    # Modules with markup in `title` gets parsed as part of the title.
    titles_with_markup = [
        'Introduction to SOME MATH Quartus and Circuit Diagram Design',
        'Lab 1-1: 4-Bit Mux and SOME STYLED TEXT all NAND/NOR Mux',
        'Lab 4-1 Interrupt Driven SOME SOME SPAN TAG DIV TAG '
        'Programming in MSP430 Assembly',
    ]

    with (collxml_templates / 'markup_in_title.xml').open('r') as doc:
        tree = parse_collxml(doc)

    for title in titles_with_markup:
        assert title in [node.alltext() for node in tree.iter()
                         if node.tag == 'title']


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


def test_find_method(collxml_templates):
    """Test that you can look at only part of the tree like `content` tag,
    and be able to differentiate between the coll's title and modules' titles
    """
    # I need a tree to work with
    with (collxml_templates / 'original.xml').open('r') as doc:
        root = parse_collxml(doc)

    actual = root.find('content')

    assert actual.tag == 'content'
    assert actual.children[0].tag == 'module'
    assert actual.children[0].attr('document') == 'm42303'


def test_finding_an_element(collxml_templates):
    with (collxml_templates / 'original.xml').open('r') as doc:
        tree = parse_collxml(doc)
    expected = 'Intro to Computational Engineering: Elec 220 Labs'

    title = tree.find_by_path('collection/metadata/title').text
    assert title == expected

    # FIXME: should be able to call title on metadata
    title = tree.collection.metadata['title'].text
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
    """Test that you can iterate through the tree depth-first.
    """
    actual = gen_press_element_tree()

    col_children = ['<collection></collection>',
                    '<mod1></mod1>',
                    '<mod2></mod2>',
                    '<mod3></mod3>',
                    '<mod3--1></mod3--1>', '<mod3--2></mod3--2>',
                    '<mod4></mod4>']

    for actual, ex in zip(actual.iter(), col_children):
        assert str(actual) == ex


def test_equality_behavior():
    """Test that a tree can be compared against another, with the == operator
    (or another as a last resort).
    """
    attrs = {'someattribrute': '_the_value_'}
    a = PressElement('someelement', text='ciao', tail='papaya', attrs=attrs)
    b = PressElement('someelement', text='ciao', tail='papaya', attrs=attrs)

    # this would fail if we hadn't defined __hash__ and __eq__
    assert a == b

    """Modules with a different `document` attribute do not equal each other
    """
    attrs = {'document': 'm00004'}
    a = PressElement('md', text='TxT', tail='TaiL', attrs=attrs)
    attrs = {'document': 'm00005'}
    b = PressElement('md', text='TxT', tail='TaiL', attrs=attrs)
    assert a != b


def test_objectified_magic():
    """Test the ability to get hold of a nested element by simply calling an
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
