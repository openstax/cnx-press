
class LegacyPublicationStarted:
    """Happens when a legacy publication has started

    :param models: a sequence of litezip models to be published
    :type models: sequence
    :param request: the request object
    :type request: :class:`pyramid.request.Request`

    """

    def __init__(self, models, request):
        self.models = models
        self.request = request


class LegacyCopyStarted(LegacyPublicationStarted):
    pass


class LegacyPublicationFinished:
    """Happens when a legacy publication has finished

    :param ids: a pairing of moduleid and major & minor version
    :type ids: sequence of tuples containing the module and a sequence
               of the major and minor version
    :param request: the request object
    :type request: :class:`pyramid.request.Request`

    """

    def __init__(self, ids, request):
        self.ids = ids
        self.request = request


class LegacyCopyFinished(LegacyPublicationFinished):
    pass
