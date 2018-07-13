# -*- coding: utf-8 -*-
from pyramid.response import Response
from pyramid.view import view_config
from sqlalchemy.sql import text


@view_config(route_name='api_modules_id')
def api_modules_id(request):
    """Get list of revisions for a module given an id"""
    module_id_number = request.matchdict['id']
    module_id = f"m{module_id_number}"
    query_result = None
    query_string = ""
    with request.get_db_engine('common').begin() as db_conn:
        stmt = text(
            'SELECT moduleid, name, version, submitter, submitlog, authors '
            'FROM modules '
            'LIMIT 5'
        )
        query_result = db_conn.execute(stmt, module_id=module_id)
    for row in query_result:
        query_string += f"\n{row}"
    return Response(f"{module_id}\n{query_string}")
