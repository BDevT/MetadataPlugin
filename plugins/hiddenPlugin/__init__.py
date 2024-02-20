import time
import datetime
import random
from functools import partial
import threading
import logging

logger = logging.getLogger( __name__ )

import ingestorservices as services

import ingestorservices.properties as properties
import ingestorservices.core as core
import ingestorservices.metadata as metadata
import ingestorservices.plugin

log_decorator = core.create_logger_decorator( logger )

class HiddenPlugin( ingestorservices.plugin.PluginBase ):

    def on_sig_changed(self, *args, **kwargs ):
        p = args[0]

        self.log('XXXX on_sig_changed %s:%s' % (p.name,str(p.value)) )

    def __init__(self, host_svcs):
        super().__init__(host_svcs)

        self.evt_stop = threading.Event()

        f1 = properties.Property( 'field1', 'value')
        f2 = properties.Property( 'field2', 'value')
        f3 = properties.Property( 'field3', 'value')

        for f in [ f1, f2, f3 ]:
            f.sig_changed.connect( self.on_sig_changed)
            self.properties[ f.name ] = f

    def run(self):

        while not self.evt_stop.wait(timeout=1.0):

            s = 'tick - %s' % str(datetime.datetime.now())

            self.log('%s' %  s )

            id_plugins = self.host_services.plugins

            plugin = id_plugins[ 'PropertyPlugin' ]

            p_f1 = plugin.properties[ 'field1' ]

            p_f1.value = s


    def stop(self):
        self.evt_stop.set()
        super().stop()


class HiddenFactory:

    def __call__(self, host_svcs):

        w = HiddenPlugin(host_svcs)

        return w


@log_decorator
def register_plugin_factory( host_svcs ):

    factory = HiddenFactory()

    host_svcs.register_plugin_factory( 'metadata_plugin', 'HiddenPlugin',  factory )
