import datetime
import random
from functools import partial
import logging

logger = logging.getLogger(__name__)

import ingestorservices as services

import ingestorservices.properties as properties
#import ingestorservices.widgets as widgets
import ingestorservices.core as core
import ingestorservices.metadata as metadata
import ingestorservices.plugin

log_decorator = core.create_logger_decorator( logger )


class PropertyPlugin( ingestorservices.plugin.PluginBase ):

    def property_group(self):
        return self.g

    def on_sig_changed(self, *args, **kwargs ):
        p = args[0]

        self.log('on_sig_changed %s:%s' % (p.name, str(p.value)) )

    def __init__(self, host_svcs):
        super().__init__(host_svcs)

        self.g = properties.PropertyGroup()

        self.f1 = properties.Property( 'field1', 'value')
        self.f2 = properties.Property( 'field2', 'value')
        self.f3 = properties.Property( 'field3', 'value')
        self.hidden = properties.Property( 'field4', 'value')

        public_properties = [ self.f1, self.f2, self.f3 ]
        for p in public_properties:
            p.sig_changed.connect( self.on_sig_changed)

            self.g.add( p )

            self.properties[ p.name ] = p

    def run(self):
         pass

    def finish(self):
        pass


class PluginFactory:

    def __call__(self, host_svcs):

        w = PropertyPlugin(host_svcs)

        return w


@log_decorator
def register_plugin_factory( host_svcs ):

    factory = PluginFactory()

    host_svcs.register_plugin_factory( 'metadata_plugin', 'PropertyPlugin',  factory )
