from lxml import etree
from litezip.main import COLLECTION_NSMAP
from press.legacy_publishing.utils import (
    replace_derived_from,
    replace_id_and_version,
    needs_major_rev,
    needs_minor_rev,
)
from press.parsers import parse_collxml

#########################################
#  Test feature: major version revision #
#########################################
def test_when_collection_title_changes(content_util):
    collection, tree, modules = content_util.gen_collection()
    with collection.file.open('rb') as fb:
        xml = etree.parse(fb)
    elem = xml.xpath('//md:title', namespaces=COLLECTION_NSMAP)[0]
    expected_title = 'Some other, different title'
    assert elem.text != expected_title

    elem.text = expected_title  # change the collection's title

    file_copy = str(collection.file)[:-4] + '_copy.xml'
    with open(file_copy, 'wb') as fb:
        # Write the modified xml to a different file
        fb.write(etree.tostring(xml))

    with collection.file.open('rb') as original, open(file_copy, 'rb') as cp:
        tree_before = parse_collxml(original)
        tree_after = parse_collxml(cp)
        assert needs_major_rev(tree_before, tree_after)

    # and just to be sure, this should be false:
    with collection.file.open('rb') as original:
        tree = same_tree = parse_collxml(original)
        assert needs_major_rev(tree, same_tree) is False


def test_when_collection_structure_changes(content_util):
    # TODO: assert ONLY content tree (modules) reordering cause major rev
    collection, tree, _ = content_util.gen_collection()

    with collection.file.open('rb') as f:
        tree_before = parse_collxml(f)

    # move the first element to location index 3 in the tree
    element = tree.pop(0)
    tree.insert(2, element)

    # generate a new collection.xml file with the reaaranged tree
    collection_after, _, _ = content_util.rebuild_collection(collection, tree)

    with collection_after.file.open('rb') as f:
        tree_after = parse_collxml(f)

    assert needs_major_rev(tree_before, tree_after)


def test_when_adding_a_new_module(content_util):
    collection, tree, _ = content_util.gen_collection()

    with collection.file.open('rb') as f:
        tree_before = parse_collxml(f)

    # add a new module
    new_module = content_util.gen_module(relative_to=collection)
    tree.append(content_util.make_tree_node_from(new_module))

    # generate a new collection.xml file with the extra module
    collection_after, _, _ = content_util.rebuild_collection(collection, tree)

    with collection_after.file.open('rb') as f:
        tree_after = parse_collxml(f)

    assert needs_major_rev(tree_before, tree_after)


def test_when_removing_a_module(content_util):
    collection, tree, _ = content_util.gen_collection()

    with collection.file.open('rb') as f:
        tree_before = parse_collxml(f)

    # remove a module (or subcollection which is a set of modules, same result)
    tree.pop(1)

    collection_after, _, _ = content_util.rebuild_collection(collection, tree)

    with collection_after.file.open('rb') as f:
        tree_after = parse_collxml(f)

    assert needs_major_rev(tree_before, tree_after)
    mods_len_before = len(tuple(tree_before.iter('module')))
    mods_len_after = len(tuple(tree_after.iter('module')))
    assert mods_len_before > mods_len_after


#########################################
#  Test feature: minor version revision #
#########################################
def test_when_md_abstr_changes(content_util):
    # metadata other than that which causes major rev or that which we ignore.
    # eg: abstract or subject is updated
    collection, tree, _ = content_util.gen_collection()
    with collection.file.open('rb') as f1, collection.file.open('rb') as f2:
        tree_before = parse_collxml(f1)
        xml = etree.parse(f2)

    """change the abstract"""
    abstract = xml.xpath('//md:abstract', namespaces=COLLECTION_NSMAP)[0]
    abstract.text = 'A different abstract'

    # write it to a different file
    file_abstr_changed = '{}_abstr.xml'.format(str(collection.file)[:-4])
    with open(file_abstr_changed, 'wb') as f:
        f.write(etree.tostring(xml))

    with open(file_abstr_changed, 'rb') as f:
        tree_after = parse_collxml(f)

    assert abstract.text == 'A different abstract'  # is this line necessary?
    assert needs_minor_rev(tree_before, tree_after)


def test_when_md_subj_changes(content_util):
    """change the subject(s)"""
    collection, tree, _ = content_util.gen_collection()
    with collection.file.open('rb') as f1, collection.file.open('rb') as f2:
        tree_before = parse_collxml(f1)
        xml = etree.parse(f2)

    subj = xml.xpath('//md:subject', namespaces=COLLECTION_NSMAP)[0]
    original_subj = subj.text
    subj.text = 'Some other subject'

    file_subj_changed = '{}_subj.xml'.format(str(collection.file)[:-4])
    with open(file_subj_changed, 'wb') as f:
        f.write(etree.tostring(xml))

    with open(file_subj_changed, 'rb') as f:
        tree_after = parse_collxml(f)

    assert needs_minor_rev(tree_before, tree_after)

    # adding a new subject also works
    # but revert the xml object to original subject(s) first
    subj.text = original_subj
    assert subj.text != 'Some other subject'

    subjs = xml.xpath('//md:subjectlist', namespaces=COLLECTION_NSMAP)[0]
    new_subject = etree.Element(
        '{{{}}}subjectlist'.format(COLLECTION_NSMAP['md']),
        nsmap=COLLECTION_NSMAP)
    new_subject.text = 'A new subject'
    subjs.append(new_subject)

    file_new_subj = '{}_new_subj.xml'.format(str(collection.file)[:-4])
    with open(file_new_subj, 'wb') as f:
        f.write(etree.tostring(xml))

    with open(file_new_subj, 'rb') as f:
        tree_after = parse_collxml(f)
    # assert 'Some other subject' in
    assert needs_minor_rev(tree_before, tree_after)


def test_when_md_params_change(content_util):
    """change params"""
    collection, tree, _ = content_util.gen_collection()
    with collection.file.open('rb') as f1, collection.file.open('rb') as f2:
        tree_before = parse_collxml(f1)
        xml = etree.parse(f2)

    # change an existing param's value
    params = xml.xpath('//col:parameters', namespaces=COLLECTION_NSMAP)[0]
    first_param = params[0]
    first_param.attrib['value'] = 'A different value'

    file_changed_param = '{}_ch_param.xml'.format(str(collection.file)[:-4])
    with open(file_changed_param, 'wb') as f:
        f.write(etree.tostring(xml))

    with open(file_changed_param, 'rb') as f:
        tree_after = parse_collxml(f)

    assert needs_minor_rev(tree_before, tree_after)

    """Test that changing the order of the params doesn't matter."""
    collection, tree, _ = content_util.gen_collection()
    with collection.file.open('rb') as f1, collection.file.open('rb') as f2:
        tree_before = parse_collxml(f1)
        xml = etree.parse(f2)

    # make the last param become the first param
    params = xml.xpath('//col:parameters', namespaces=COLLECTION_NSMAP)[0]
    # ... but first, essentially make a copy of the last param
    last_param = params[-1]
    new_param_obj = etree.Element(
        '{{{}}}param'.format(COLLECTION_NSMAP['col']),
        nsmap=COLLECTION_NSMAP, name=last_param.attrib['name'],
        value=last_param.attrib['value'])
    params.insert(0, new_param_obj)
    params.remove(last_param)

    # ... and save modified xml into a new file
    file_ch_ps_order = '{}_ch_ps_order.xml'.format(str(collection.file)[:-4])
    with open(file_ch_ps_order, 'wb') as f:
        f.write(etree.tostring(xml))

    with open(file_ch_ps_order, 'rb') as f:
        tree_after = parse_collxml(f)

    assert needs_minor_rev(tree_before, tree_after) is False


def test_when_md_actors_change(content_util):
    """Change actors"""
    collection, tree, _ = content_util.gen_collection()
    with collection.file.open('rb') as f1, collection.file.open('rb') as f2:
        tree_before = parse_collxml(f1)
        xml = etree.parse(f2)

    firstname = xml.xpath('//md:firstname', namespaces=COLLECTION_NSMAP)[0]
    firstname.text = 'Elon'
    surname = xml.xpath('//md:surname', namespaces=COLLECTION_NSMAP)[0]
    surname.text = 'Musk'
    fullname = xml.xpath('//md:fullname', namespaces=COLLECTION_NSMAP)[0]
    fullname.text = 'Elon Musk'

    actor_changed = '{}_ch_acto_order.xml'.format(str(collection.file)[:-4])
    with open(actor_changed, 'wb') as f:
        f.write(etree.tostring(xml))

    with open(actor_changed, 'rb') as f:
        tree_after = parse_collxml(f)

    assert needs_minor_rev(tree_before, tree_after)

    """Test that changing the order of the actors doesn't matter."""
    def gen_element(prefix, tag, text):
        elem = etree.Element(
            '{{{}}}{}'.format(COLLECTION_NSMAP[prefix], tag),
            nsmap=COLLECTION_NSMAP)
        elem.text = text
        return elem

    collection, tree, _ = content_util.gen_collection()
    with collection.file.open('rb') as f1, collection.file.open('rb') as f2:
        tree_before = parse_collxml(f1)
        xml = etree.parse(f2)

    # make the last actor become the first actor
    actors = xml.xpath('//md:actors', namespaces=COLLECTION_NSMAP)[0]
    assert len(actors) == 1  # only one child, so only one actor.
    # ... but first, essentially make a copy of the last actor
    new_actor_obj = gen_element('md', 'person', None)
    new_actor_obj.insert(0, gen_element('md', 'firstname', 'Elon'))
    new_actor_obj.insert(1, gen_element('md', 'surname', 'Musk'))
    new_actor_obj.insert(2, gen_element('md', 'fullname', 'Elon Musk'))
    actors.insert(1, new_actor_obj)  # insert in second place
    assert len(actors) == 2

    # NOW change the order
    actors = xml.xpath('//md:actors', namespaces=COLLECTION_NSMAP)[0]
    last_actor = actors[1]
    actors.insert(0, last_actor)
    actors.remove(last_actor)

    file_acto_order = '{}_ch_acto_order.xml'.format(str(collection.file)[:-4])
    with open(file_acto_order, 'wb') as f:
        f.write(etree.tostring(xml))

    with open(file_acto_order, 'rb') as f:
        tree_after = parse_collxml(f)

    assert needs_minor_rev(tree_before, tree_after) is False


def test_when_md_roles_change(content_util):
    """Change roles"""
    collection, tree, _ = content_util.gen_collection()
    with collection.file.open('rb') as f1, collection.file.open('rb') as f2:
        tree_before = parse_collxml(f1)
        xml = etree.parse(f2)

    author = xml.xpath('//md:role[@type="author"]',
                       namespaces=COLLECTION_NSMAP)[0]
    author.text = 'A different author'
    maintainer = xml.xpath('//md:role[@type="maintainer"]',
                           namespaces=COLLECTION_NSMAP)[0]
    maintainer.text = 'A different maintainer'
    licensor = xml.xpath('//md:role[@type="licensor"]',
                         namespaces=COLLECTION_NSMAP)[0]
    licensor.text = 'A different licensor'

    file_author_changed = '{}_ch_auth.xml'.format(str(collection.file)[:-4])
    with open(file_author_changed, 'wb') as f:
        f.write(etree.tostring(xml))

    with open(file_author_changed, 'rb') as f:
        tree_after = parse_collxml(f)

    assert needs_minor_rev(tree_before, tree_after)

    """Test that the order of roles (per type) don't matter"""
    # for this test I'll just change the authors, not maintainer or licensor.
    collection, tree, _ = content_util.gen_collection()
    with collection.file.open('rb') as f1, collection.file.open('rb') as f2:
        tree_before = parse_collxml(f1)
        xml = etree.parse(f2)

    authors = xml.xpath('//md:role[@type="author"]',
                        namespaces=COLLECTION_NSMAP)[0]
    authors_list = authors.text.split(' ')
    authors.text = '{} {}'.format(authors_list[1], authors_list[0])

    file_auth_order = '{}_ch_auth_order.xml'.format(str(collection.file)[:-4])
    with open(file_auth_order, 'wb') as f:
        f.write(etree.tostring(xml))

    with open(file_auth_order, 'rb') as f:
        tree_after = parse_collxml(f)

    assert needs_minor_rev(tree_before, tree_after) is False
#####################


def test_replace_id_and_version(content_util):
    module = content_util.gen_module()
    id = '$$$_id_$$$'
    version = ('$', '%',)

    # Call the target
    replace_id_and_version(module, id, version)

    # Check the id and version were replaced
    with module.file.open('r') as fb:
        text = fb.read()
    assert id in text
    assert '1.{}'.format(version[0]) in text


class TestReplaceDerivedFrom:

    def test_create(self, content_util):
        module = content_util.gen_module()
        id = '$$$_id_$$$'
        version = '$.%'
        url = 'http://cnx.org/content/{}/{}'.format(id, version)

        # Call the target
        replace_derived_from(module, url)

        # Check the derived-from was replaced
        with module.file.open('r') as fb:
            text = fb.read()
        expected = '<md:derived-from url="{}"/>'.format(url)
        assert expected in text

    def test_replace(self, content_util):
        original_module = content_util.gen_module()
        module = content_util.gen_module(derived_from=original_module)
        id = '$$$_id_$$$'
        version = '$.%'

        url = 'http://cnx.org/content/{}/{}'.format(id, version)

        # Call the target
        replace_derived_from(module, url)

        # Check the derived-from was replaced
        with module.file.open('r') as fb:
            text = fb.read()
        expected = '<md:derived-from url="{}"/>'.format(url)
        assert expected in text
