class BaseDneLoaderError(Exception):
    """
    Base exception for edne_correios_loader
    """


class DneResolverError(BaseDneLoaderError):
    """
    Error resolving DNE source
    """
