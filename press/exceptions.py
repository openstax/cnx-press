

class AppStartUpWarning(Warning):
    """A warning message invoked during application startup.

    Usage: warnings.warn('ur msg', AppStartUpWarning)

    """


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
