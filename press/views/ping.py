# -*- coding: utf-8 -*-
from pyramid.response import Response
from pyramid.view import view_config


@view_config(route_name='ping', http_cache=0)
def ping(request):
    """A ping and ack view for checking the service is up and running."""
    return Response('pong')


@view_config(route_name='auth-ping', permission='view')
def authedping(request):
    """Authenticated ping for testing the auth mechanism."""
    return Response('pong')
