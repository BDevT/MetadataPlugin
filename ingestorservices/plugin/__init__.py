import logging
import threading

logger = logging.getLogger( __name__ )

from .. import properties
from .. import core

log_decorator = core.create_logger_decorator( logger )


class PluginBase:

    def __init__(self, host_services ):

        self.host_services = host_services

        self._properties = properties.PropertyDict()

    def initialise(self, *args, **kwargs):
        pass

    def start(self):
        self.t = threading.Thread( target=self.run )
        self.t.start()

    @log_decorator
    def log(self, s : str ):

        _ = '<%s> : %s' % (self.__class__.__name__, str(s) )

        self.host_services.log( _.rstrip() )

    @property
    def properties(self):
        return self._properties

    def stop(self):
        pass

    def join(self):
        self.t.join()



