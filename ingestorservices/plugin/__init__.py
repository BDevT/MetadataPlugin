import logging

logger = logging.getLogger( __name__ )

from .. import properties
from .. import core

log_decorator = core.create_logger_decorator( logger )

class PluginBase:

    def __init__(self, host_services ):
        super().__init__()

        self.host_services = host_services

        self._properties = properties.PropertyDict()

    @log_decorator
    def log(self, s : str ):

        _ = '<%s> : %s' % (self.__class__.__name__, str(s) )

        self.host_services.log( _.rstrip() )

    @property
    def properties(self):
        return self._properties

