import time
import datetime
import random
from functools import partial
import threading
import logging

logger = logging.getLogger( __name__ )

import ingestorservices as services

import ingestorservices.properties as properties
#import ingestorservices.widgets as widgets
import ingestorservices.core as core
import ingestorservices.metadata as metadata
import ingestorservices.plugin

log_decorator = core.create_logger_decorator( logger )


class EmptyPlugin( ingestorservices.plugin.PluginBase ):

    def __init__(self, host_svcs):
        super().__init__(host_svcs)

    def finish(self):
        pass


class EmptyFactory:

    def __call__(self, host_svcs):

        f = EmptyPlugin(host_svcs)

        return f


@log_decorator
def register_plugin_factory( host_svcs ):

    factory = EmptyFactory()

    host_svcs.register_plugin_factory( 'metadata_plugin', 'EmptyPlugin',  factory )
