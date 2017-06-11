def includeme(config):
    """Declaration of routing"""
    add_route = config.add_route
    add_route('ping', '/ping')
