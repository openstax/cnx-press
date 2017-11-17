from pathlib import Path


here = Path(__file__).parent


def includeme(config):
    """Declaration of routing"""
    add_route = config.add_route
    add_route('ping', '/ping')

    s = config.registry.settings
    s['pyramid_swagger.exclude_paths'] = [
        '^/api-docs/?',
        '^/ping/?',
    ]
    s['pyramid_swagger.schema_file'] = 'swagger.yaml'
    s['pyramid_swagger.schema_directory'] = str(here / 'api-docs')
    config.include('pyramid_swagger')
