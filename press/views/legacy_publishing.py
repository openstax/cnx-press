import logging
import zipfile

from litezip import parse_litezip, validate_litezip
from pyramid.view import view_config

from .. import events
from ..legacy_publishing import publish_litezip
from ..publishing import (
    discover_content_dir,
    expand_zip,
    persist_file_to_filesystem,
)


@view_config(route_name='api.v3.publications', request_method=['POST'],
             renderer='json')
def publish(request):
    uploaded_file = request.swagger_data['file']
    # TODO Check if the 'publisher' is an authenticated user.
    #      But not that they have rights to publish,
    #      that would be done in the processing of the publication request.
    # FIXME The publisher info should be coming out of the Session info.
    publisher = request.swagger_data['publisher']
    message = request.swagger_data['message']

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

    # Validate the litezip content
    validation_msgs = validate_litezip(litezip_struct)
    if validation_msgs:  # if it's not an empty list of messages
        request.response.status = 400
        return {'messages': [
            {'id': 2,
             'message': 'validation issue',
             'item': str(path.relative_to(litezip_dir)),
             'error': message,
             }
            for path, message in validation_msgs
        ]}

    start_event = events.LegacyPublicationStarted(
        litezip_struct,
        request,
    )
    request.registry.notify(start_event)

    with request.get_db_engine('common').begin() as db_conn:
        id_mapping = publish_litezip(litezip_struct, (publisher, message),
                                     db_conn)

    finish_event = events.LegacyPublicationFinished(
        id_mapping.values(),
        request,
    )
    request.registry.notify(finish_event)

    resp_data = []
    for src_id, (id, ver) in id_mapping.items():
        resp_data.append({
            'source_id': src_id,
            'id': id,
            'version': ver,
            'url': request.route_url('api.v1.versioned_content',
                                     id=id, ver=ver),
        })
    return resp_data
