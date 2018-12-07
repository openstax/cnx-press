# -*- coding: utf-8 -*-
from pyramid.view import view_config


@view_config(renderer='string', route_name='ping', http_cache=0)
@view_config(renderer='string', route_name='api-ping', http_cache=0)
@view_config(renderer='string', route_name='auth-ping', http_cache=0,
             permission='view')
@view_config(renderer='string', route_name='publish-ping', http_cache=0,
             permission='publish')
@view_config(renderer='string', route_name='push-ping', http_cache=0,
             permission='manage')
def ping(request):
    """A ping and ack view for checking the service is up and running.

    There are multiple views to accommodate multiple paths
    and different permissions"""
    return 'pong {path}'.format(path=request.path)
