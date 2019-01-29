import logging
import zipfile

from litezip import parse_litezip
from pyramid.view import view_config

from .. import events
from ..legacy_publishing import push_litezip
from ..publishing import (
    discover_content_dir,
    expand_zip,
    persist_file_to_filesystem,
)
from ..utils import (
    convert_version_tuple_to_version_string,
    convert_version_to_legacy_version
)


@view_config(route_name='api.v3.push', request_method=['POST'],
             renderer='json', http_cache=0, permission='manage')
def push(request):
    uploaded_file = request.swagger_data['file']
    # TODO Check if the 'publisher' is an authenticated user.
    #      But not that they have rights to publish,
    #      that would be done in the processing of the publication request.
    # FIXME The publisher info should be coming out of the Session info.
    publisher = request.swagger_data['publisher']
    message = 'press push copy'

    # TODO Check upload size... HTTP 413

    # Check if it's a valid zipfile.
    if not zipfile._check_zipfile(uploaded_file):
        request.response.status = 400
        return {'messages': [
            {'id': 1,
             'message': 'The given file is not a valid zip formatted file.'},
        ]}
    # Reset the file to the start.
    uploaded_file.seek(0)

    upload_filepath = persist_file_to_filesystem(uploaded_file)
    logging.debug('write upload to: {}'.format(upload_filepath))
    litezip_dir = expand_zip(upload_filepath)
    litezip_dir = discover_content_dir(litezip_dir)

    # Parse the litezip to a data type structure.
    litezip_struct = parse_litezip(litezip_dir)

    start_event = events.LegacyCopyStarted(
        litezip_struct,
        request,
    )
    request.registry.notify(start_event)

    with request.get_db_engine('common').begin() as db_conn:
        ids = push_litezip(litezip_struct, (publisher, message), db_conn)
    finish_event = events.LegacyCopyFinished(
        ids,
        request,
    )
    request.registry.notify(finish_event)

    resp_data = []
    for id, ver in ids:
        version_string = convert_version_tuple_to_version_string(ver)
        legacy_version = convert_version_to_legacy_version(ver)
        resp_data.append({
            'source_id': id,
            'id': id,
            'version': version_string,
            'legacy_version': legacy_version,
            'url': request.route_url('api.v1.versioned_content',
                                     id=id, ver=legacy_version),
        })
    return resp_data
