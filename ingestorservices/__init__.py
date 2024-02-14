import collections
import importlib
import pkgutil
import datetime
import json

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

import threading


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
            self.log( '%s : %s' % (self, e) )

    @log_decorator
    def unregister_plugin( self, identifier ):

        plugins = self.plugins

        if identifier in plugins:
            plugin_instance = plugins[ identifier ]
            plugin_instance.finish()
            del plugins[ identifier ] 


    def __init__( self ):
        super().__init__()

        self.bridge = HostServices.Bridge()

        self._scicat = None

        self._pluginRegistry = PluginRegistry(self)

    def login( self, base_url, username, password):

        # Create a client object. The account used should have the ingestor role in SciCat
        self.log( 'LOGIN %s %s' %( base_url, username) )

        self._scicat = MyMetadataClient(base_url=base_url,
                username=username,
                password=password)

        return 1 if self._scicat == None else 0

    def logout(self):
        self._scicat = None

    @log_decorator
    def load_plugins(self, paths=None):

            #discover the plugins
            try:
                _paths = paths if paths else [ 'plugins']

                for x in _paths:
                    _path=[x]

                    for finder, name, ispkg in pkgutil.iter_modules(path=_path, prefix=x+'.'):

                        try:
                            _ = importlib.import_module( name,x+'.' )

                            _.register_plugin_factory(self)
                        except Exception as e:
                            self.log( self, '%s load_plugins %e',( self, e) )

            except Exception as e:
                print(e)

    @log_decorator
    def requestDatasetFind( self, filter_fields ):
        scicat = self._scicat

        try:
            results = scicat.datasets_get_many( filter_fields=filter_fields )
            return results
        except Exception as e:
            print(e)


    @log_decorator
    def requestDatasetSave(self, ds):
        scicat = self._scicat
        dataset_id = None

        try:
            dataset_id = scicat.upload_new_dataset( ds )

            self.log( 'Ingested : %s' % dataset_id )

        except Exception as e:
            self.log( '%s : Failed to ingest : EXCEPTION %s' % (self, str(e)) )


        return dataset_id

    def log(self, s, *args):

        now = datetime.datetime.now()

        self.bridge.signalLog.emit( '%s : <%s> %s' % (str(now), self.__class__.__name__, str(s) ) )

    @property
    def plugins(self):
        return self._pluginRegistry.plugins

    @log_decorator
    def join_plugins( self ):
        for name, plugin in self.plugins.items():
            plugin.join()

    @log_decorator
    def stop_plugins(self):
        for name, plugin in self.plugins.items():
            plugin.stop()




