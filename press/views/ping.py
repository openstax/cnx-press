# -*- coding: utf-8 -*-
from pyramid.response import Response
from pyramid.view import view_config


@view_config(route_name='ping', http_cache=0)
def ping(request):
    """A ping and ack view for checking the service is up and running."""
    return Response('pong')


@view_config(route_name='auth-ping', http_cache=0, permission='view')
def authedping(request):
    """Authenticated ping for testing the auth mechanism."""
    return Response('pong')


@view_config(route_name='publish-ping', http_cache=0, permission='publish')
def publish_ping(request):
    """Authenticated ping for testing the publish endpoint"""
    return Response('pong')
