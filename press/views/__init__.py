from pathlib import Path


here = Path(__file__).parent


def includeme(config):
    """Declaration of routing"""
    add_route = config.add_route
    add_route('ping', '/ping')

    add_route('api_modules_id', '/api/modules/{id}')

    add_route('api.v1.versioned_content', '/content/{id}/{ver}')

    add_route('api.v2.contents', '/contents/{ident_hash}')
    add_route('api.v2.resources', '/resources/{hash}')

    add_route('api.v3.publications', '/api/publish-litezip')

    s = config.registry.settings
    s['pyramid_swagger.exclude_paths'] = [
        '^/api-docs/?',
        '^/ping/?',
        '^/api/modules/?'
    ]
    s['pyramid_swagger.schema_file'] = 'swagger.yaml'
    s['pyramid_swagger.schema_directory'] = str(here / 'api-docs')
    config.include('pyramid_swagger')
