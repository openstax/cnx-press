from contextlib import contextmanager
from functools import wraps
from lxml import etree


@contextmanager
def element_tree_from_model(model):
    """Yields an ElementTree of the model's content that will write on
    changes on exit.

    """
    with model.file.open('rb') as fb:
        xml = etree.parse(fb)

    yield xml

    with model.file.open('wb') as fb:
        fb.write(etree.tostring(xml))


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


def retryable_timeout_request_mock_callback(f):
    """Makes a custom requests-mock callback function retryable by
    passing the try count to the wrapped callback as the ``tries``
    keyword argument.

    (According to the internet "retryable" is the correct spelling.)

    """

    @wraps(f)
    def wrapper(request, context):
        wrapper.tries.setdefault(request.url, 0)
        wrapper.tries[request.url] += 1
        return f(request, context, tries=wrapper.tries[request.url])
    wrapper.tries = {}

    return wrapper
