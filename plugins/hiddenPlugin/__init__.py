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

class Worker( threading.Thread):
    def __init__(self, host):
        super().__init__()
        self.host = host
        self.cond_stop = threading.Condition()


    def stop(self):
        with self.cond_stop:
            self.cond_stop.notify()

    def run(self):
        with self.cond_stop:
            while not self.cond_stop.wait(timeout=1):

                s = 'tick - %s' % str(datetime.datetime.now())

                self.host.log('%s' %  s )

                id_plugins = self.host.host_services.plugins

                plugin = id_plugins[ 'PropertyPlugin' ]

                p_f1 = plugin.properties[ 'field1' ]

                p_f1.value = s



class HiddenPlugin( ingestorservices.plugin.PluginBase ):

    def on_sig_changed(self, *args, **kwargs ):
        p = args[0]

        self.log('XXXX on_sig_changed %s:%s' % (p.name,str(p.value)) )

    def __init__(self, host_svcs):
        super().__init__(host_svcs)

        f1 = properties.Property( 'field1', 'value')
        f2 = properties.Property( 'field2', 'value')
        f3 = properties.Property( 'field3', 'value')

        for f in [ f1, f2, f3 ]:
            f.sig_changed.connect( self.on_sig_changed)
            self.properties[ f.name ] = f

        self.worker = Worker(self)
        self.worker.daemon = True
        self.worker.start()

    def join(self):
        print('hiddenPlugin join' )

        self.worker.join()

    def run(self):
        pass

    def finish(self):
        self.worker.stop()
        self.worker.join()


class HiddenFactory:

    def __call__(self, host_svcs):

        w = HiddenPlugin(host_svcs)

        return w


@log_decorator
def register_plugin_factory( host_svcs ):

    factory = HiddenFactory()

    host_svcs.register_plugin_factory( 'metadata_plugin', 'HiddenPlugin',  factory )
