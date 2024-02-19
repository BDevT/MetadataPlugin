import time
import datetime
import random
from functools import partial
import threading
import logging
import json

logger = logging.getLogger( __name__ )

import ingestorservices as services

import ingestorservices.properties as properties
#import ingestorservices.widgets as widgets
import ingestorservices.core as core
import ingestorservices.metadata as metadata
import ingestorservices.plugin

log_decorator = core.create_logger_decorator( logger )


class Step2Plugin( ingestorservices.plugin.PluginBase ):

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

    def initialise(self, *args, **kwargs):

        self.runId = kwargs['run']
        self.output_fname = kwargs.get(  'outputfile', '/tmp/run1.json' )

    def run(self):

        timeout=0.1

        data = {}

        tick = 0
        tick_max = 5
        
        while (not self.evt_stop.wait(timeout=timeout)) and tick < tick_max:

            s = 'tick - %s' % str(datetime.datetime.now())

            self.log('%s' %  s )

            id_plugins = self.host_services.plugins

            if 0:
                plugin = id_plugins[ 'PropertyPlugin' ]

                p_f1 = plugin.properties[ 'field1' ]

                p_f1.value = s

            data[tick] = s

            tick +=1 

        #write the metadata
        # Create an Ownable that will get reused for several other Model objects
        ownable = metadata.Ownable(ownerGroup="magrathea"
                                   , accessGroups=["deep_though"]
                                   , createdBy=None
                                   , updatedBy=None
                                   , updatedAt=None
                                   , createdAt=None
                                   , instrumentGroup=None)

        ownable = metadata.Ownable(ownerGroup="magrathea"
                                   , accessGroups=["deep_though"] )

        host_services = self.host_services

        prev_results = host_services.requestDatasetFind( {'scientificMetadata.step' : 1} )

        if prev_results:

            def f( ds ):
                val = ds['creationTime']
                return val

            _ = sorted( prev_results, key = f )

            ds_step1 = _[-1]

            self.log('FOUND PREV STEP1 %s' %  ds_step1['pid'] )

            j_sm_step1 = ds_step1['scientificMetadata']

            #get the previous step info
            j_sm = {}
            j_sm['run'] = self.runId
            j_sm['step'] = 2
            j_sm['step1'] = {}
            j_sm['step1']['scientificMetadata'] = j_sm_step1

            instrumentId='earth'
            instrumentId=None

            dataset = metadata.Dataset(
                path='/foo/bar',
                datasetName='step2',
                size=42,
                owner="slartibartfast",
                contactEmail="slartibartfast@magrathea.org",
                creationLocation= 'magrathea',
                creationTime=str(datetime.datetime.now()),
                instrumentId='ukri_instrument1',
                type="raw",
                proposalId="psi_proposal1",
                dataFormat="planet",
                principalInvestigator="A. Mouse",
                sourceFolder='/foo/bar',
                scientificMetadata= j_sm,
                sampleId="gargleblasterxxx",
                **ownable.dict(), )

            with open( self.output_fname, 'w') as f:
                json.dump( dataset.dict(), f )

            dataset_id = host_services.requestDatasetSave( dataset )


    def stop(self):
        self.evt_stop.set()

class Factory:

    def __call__(self, host_svcs):

        w = Step2Plugin(host_svcs)

        return w


@log_decorator
def register_plugin_factory( host_svcs ):

    factory = Factory()

    host_svcs.register_plugin_factory( 'metadata_plugin', 'step2Plugin',  factory )
