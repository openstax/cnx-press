
class LegacyPublicationStarted:
    """Happens when a legacy publication has started

    :param models: a sequence of litezip models to be published
    :type models: sequence

    """

    def __init__(self, models):
        self.models = models


class LegacyPublicationFinished:
    """Happens when a legacy publication has finished

    :param ids: a pairing of moduleid and major & minor version
    :type models: sequence of tuples containing the module and a sequence
                  of the major and minor version

    """

    def __init__(self, ids):
        self.ids = ids
