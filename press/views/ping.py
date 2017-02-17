# -*- coding: utf-8 -*-
from pyramid.response import Response
from pyramid.view import view_config


@view_config(route_name='ping')
def ping(request):
    """A ping and ack view for checking the service is up and running."""
    return Response('pong')
