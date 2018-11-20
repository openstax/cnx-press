# -*- coding: utf-8 -*-
from pyramid.response import Response
from pyramid.view import view_config


@view_config(renderer='text', route_name='ping', http_cache=0)
@view_config(route_name='api-ping', http_cache=0)
@view_config(route_name='auth-ping', http_cache=0, permission='view')
@view_config(route_name='publish-ping', http_cache=0, permission='publish')
def ping(request):
    """A ping and ack view for checking the service is up and running.

    There are multiple views to accommodate multiple paths
    and different permissions"""
    return Response('pong {path}'.format(path=request.path),
                    content_type='text/plain')
