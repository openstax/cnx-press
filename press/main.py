# -*- coding: utf-8 -*-
from pyramid.config import Configurator


def make_config():
    """Configurator factory"""
    config = Configurator()
    return config


def declare_routes(config):
    """Declaration of routing"""
    add_route = config.add_route


def configure(config):
    """Configure the Configurator object"""
    declare_routes(config)
    config.scan(ignore='press.tests')
    return config


def make_app(config=None):
    """WSGI application factory"""
    if config is None:
        config = make_config()
    configure(config)
    return config.make_wsgi_app()


def paste_app_factory(global_config, **settings):  # pragma: no cover
    """Paste application factory"""
    config = make_config()
    config.add_settings(settings=settings)
    return make_app(config)
