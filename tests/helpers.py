from contextlib import contextmanager
from functools import wraps
from lxml import etree


def count_calls(func):
    """Counts the number of times a function was called.

    The original intend of this decorator is to count the number of times
    a requests_mock callback has been called. The internal logic of the
    callback uses the counter to either succeed or fail depending on how
    many times it has been called. The end result is a callback function
    that is able to simulate request retries.

    This annotates the function so that it has a `call_count` parameter
    that increments each time the function is called.

    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        wrapper.call_count += 1
        return func(*args, **kwargs)
    wrapper.call_count = 0
    return wrapper


@contextmanager
def element_tree_from_model(model):
    """Yields an ElementTree of the model's content that will write on
    changes on exit.

    """
    with model.file.open('rb') as fb:
        xml = etree.parse(fb)

    yield xml

    with model.file.open('wb') as fb:
        fb.write(etree.tounicode(xml).encode('utf8'))


def compare_legacy_tree_similarity(db_tree, test_tree):
    """Compare the two types of tree, one coming from the database using
    `tree_to_json_for_legacy` and the other using the tree structure
    provided by the `content_util` testing utility.

    """
    for i, v in enumerate(db_tree):
        if v['id'].startswith('col'):
            assert test_tree[i].title == v['title']
            compare_legacy_tree_similarity(v['contents'],
                                           test_tree[i].contents)
        else:
            node = test_tree[i]
            assert v['id'] == node.id
            assert v['title'] == node.title
            assert v['version'] == node.version_at


def retryable_timeout_request_mock_callback(func):
    """Makes a custom requests-mock callback function retryable by
    passing the try count to the wrapped callback as the ``tries``
    keyword argument.

    (According to the internet "retryable" is the correct spelling.)

    """

    @wraps(func)
    def wrapper(request, context):
        wrapper.tries.setdefault(request.url, 0)
        wrapper.tries[request.url] += 1
        return func(request, context, tries=wrapper.tries[request.url])
    wrapper.tries = {}

    return wrapper


def gen_element(namespace, tag, text, tail=None):
    from litezip.main import COLLECTION_NSMAP
    elem = etree.Element(
        '{{{}}}{}'.format(COLLECTION_NSMAP[namespace], tag),
        nsmap=COLLECTION_NSMAP)
    elem.text = text
    return elem
