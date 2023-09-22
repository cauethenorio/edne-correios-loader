class BaseDneLoaderError(Exception):
    """
    Base exception for dne_correios_loader
    """


class DneResolverError(BaseDneLoaderError):
    """
    Error resolving DNE source
    """
