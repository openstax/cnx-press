from pyramid import httpexceptions
from pyramid.view import view_config
from sqlalchemy.sql import desc

from press.utils import convert_to_legacy_domain


def _lookup_latest_legacy_version(request, legacy_id):
    """Given the legacy id for content, lookup the latest version."""
    t = request.db_tables
    with request.get_db_engine('common').begin() as db_conn:
        results = db_conn.execute(
            t.latest_modules.select()
            .where(t.latest_modules.c.moduleid == legacy_id)
        )
        return getattr(results.fetchone(), 'version', None)


def _lookup_head_legacy_version(request, legacy_id):
    """Given the legacy id for content, lookup the very latest version."""
    t = request.db_tables
    with request.get_db_engine('common').begin() as db_conn:
        results = db_conn.execute(
            t.modules.select()
            .where(t.modules.c.moduleid == legacy_id)
            .order_by(desc('module_ident'))
        )
        return getattr(results.fetchone(), 'version', None)


def _redirect_to_legacy(request, id, version):
    path = request.route_path(
        'api.v1.versioned_content',
        id=id,
        ver=version,
    )
    domain = convert_to_legacy_domain(request.domain)
    scheme = request.scheme
    location = '{}://{}{}'.format(scheme, domain, path)
    return httpexceptions.HTTPFound(location=location)


@view_config(route_name='api.v3.collections',
             request_method=['GET'])
def redirect_collections_latest(request):
    # At this time this simply redirects to legacy*.cnx.org for content
    # with the 'latest' version specifier. Later implementations may
    # remove this code altogether.
    legacy_id = request.swagger_data['id']
    legacy_version = request.swagger_data['ver'].lower()
    if legacy_version in ('latest', 'head'):
        lookup_func = {
            'latest': _lookup_latest_legacy_version,
            'head': _lookup_head_legacy_version,
        }[legacy_version]
        queried_version = lookup_func(request, legacy_id)
        if queried_version is None:
            raise httpexceptions.HTTPNotFound()
        raise _redirect_to_legacy(request, legacy_id, queried_version)
    else:
        raise httpexceptions.HTTPNotFound()
