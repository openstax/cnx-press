from pyramid.httpexceptions import HTTPUnauthorized, HTTPException, HTTPForbidden
from pyramid.security import forget
from pyramid.view import forbidden_view_config

@forbidden_view_config(renderer='json')
def forbidden_view(request):
    request.response.status = 401
    response = {'messages': [
    {'id': 5, 'message': 'Unauthorized', 'error': 'Nothing to see here.'}
    ]}
    return response
