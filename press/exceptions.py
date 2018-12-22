class StaleVersion(Exception):
    """Raised when checked out version is older than published version"""
    def __init__(self, checked_out_version, current_version, item):
        self.checked_out_version = checked_out_version
        self.current_version = current_version
        self.item = item


class Unchanged(Exception):
    """Raised when checked out version is older than published version"""
    def __init__(self, model):
        self.model = model


class CollectionChanged(Exception):
    """Raised when checked out version is older than published version"""
    def __init__(self, collection):
        self.collection = collection
