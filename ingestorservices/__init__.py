import collections
import importlib
import pkgutil
import datetime

from collections import namedtuple

import logging

logger = logging.getLogger(__name__)

from . _filters import Property, _and_, _or_, _where_
from . client import MyMetadataClient

from . import core
from . import plugin
from . import properties

from . _dialogs import _property_2_layout, _property_group_2_layout

log_decorator = core.create_logger_decorator( logger )

PluginDict = core.TypeDict( str, plugin.PluginBase )

class PluginRegistry:

    def __init__(self, host_services):
        self.id_plugins = PluginDict()

    @property
    def plugins(self):
        return self.id_plugins

class HostServices:

    class Bridge:
        def __init__(self):
            self.signalLog = core.Signal()

    @log_decorator
    def register_plugin_factory( self, identifier, label, handler ):
        try:
            logger.info('register_plugin : {} {} {}'.format ( identifier, label, str(handler) ))

            plugin_instance = handler( self )
            self._pluginRegistry.plugins[ label ] = plugin_instance

        except Exception as e:
            print('AAAAAAAAAAAAAAAAAAAAAAAAAAAAA', e)

    @log_decorator
    def unregister_plugin( self, identifier ):

        plugins = self.plugins

        if identifier in plugins:
            plugin_instance = plugins[ identifier ]
            plugin_instance.finish()
            del plugins[ identifier ] 


    def __init__( self, host ):
        super().__init__()

        self.bridge = HostServices.Bridge()

        self._host = host
        self._scicat = None

        self._pluginRegistry = PluginRegistry(self)

    def login( self, base_url, username, password):

        # Create a client object. The account used should have the ingestor role in SciCat
        self._scicat = MyMetadataClient(base_url=base_url,
                username=username,
                password=password)

        return 1 if self._sciact == None else 0

    def logout(self):
        self._sciact = None



    @log_decorator
    def start(self):

            #discover the plugins
            try:
                _path=['plugins']

                for finder, name, ispkg in pkgutil.iter_modules(path=_path, prefix='plugins.'):
                    try:
                        _ = importlib.import_module( name, 'plugins.' )

                        _.register_plugin_factory(self)
                    except Exception as e:
                        print('XXXXXXXXXXXXXXXXX',e)

            except Exception as e:
                print(e)

    @log_decorator
    def requestDatasetSave(self, name, ds):
        scicat = self._scicat
        dataset_id = None
    
        try:
            dataset_id = scicat.upload_new_dataset( ds )

            self.log( 'Ingested : %s' % dataset_id )

        except Exception as e:
            self.log('Failed to ingest : EXCEPTION %s' % str(e))


        return dataset_id

    def log(self, s, *args):

        now = datetime.datetime.now()

        self.bridge.signalLog.emit( '%s : <%s> %s' % (str(now), self.__class__.__name__, str(s) ) )

    @property
    def plugins(self):
        return self._pluginRegistry.plugins

    @log_decorator
    def finish(self):
        for name, plugin in self.plugins.items():
            plugin.finish()

            self.log( 'Finished %s' % plugin.__class__.__name__ )
        self.plugins.clear()




