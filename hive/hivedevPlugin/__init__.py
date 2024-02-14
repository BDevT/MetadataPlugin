import datetime
import json
import logging
import pyscicat
import time
import threading
import pathlib
import shutil

from .extract import convert_md_to_json

logger = logging.getLogger( __name__ )

import ingestorservices as services
import ingestorservices.widgets as widgets
import ingestorservices.core as core
import ingestorservices.metadata as metadata
import ingestorservices.plugin

log_decorator = core.create_logger_decorator( logger )


class HivePlugin( ingestorservices.plugin.PluginBase ):
    '''Wait for events. Extract metadata from placeholder and file before writing to backend '''

    def __init__(self, host_services):
        super().__init__(host_services)

        self.evt_stop = threading.Event()

        self.path_spool  = pathlib.Path('./data/hive')
        self.host_services = host_services

        def requireProperty( name, value ):

            try:
                prop = self.properties[ name ]
            except Exception as e:

                prop = services.properties.Property( name, value )

                self.properties[ prop.name ] = prop

            return prop

        def boxProperty( name, value ):
            try:
                prop = self.properties[ name ]
            except Exception as e:

                try:
                    prop = services.properties.Property( name, value )
                    self.properties[ prop.name ] = prop
                except Exception as e:
                    print(e)

            return prop

        prop_owner = requireProperty( 'Owner', '' )
        prop_ownerGroup = requireProperty( 'Owner group', '' )
        prop_principleInvestigator = requireProperty( 'Principal Investigator', '' )
        prop_email = requireProperty( 'Contact email', '' )
        prop_sourceFolder = requireProperty( 'Data source', '' )
        prop_creationDate = requireProperty( 'Date', '' )
        prop_location = requireProperty( 'Location', '' )
        prop_experimentData = boxProperty( 'Experiment data', '' )

        pg = services.properties.PropertyGroup( layout=services.properties.PropertyGroup.VERTICAL )
        pg.add( prop_owner )
        pg.add( prop_ownerGroup )
        pg.add( prop_principleInvestigator )
        pg.add( prop_email )
        pg.add( prop_sourceFolder )
        pg.add( prop_creationDate)
        pg.add( prop_location )
        pg.add( prop_experimentData )

    def run(self):
        while not self.evt_stop.wait(timeout=1):

            try:
               # get the path of the markdown file here - Ajay
               paths = list(self.path_spool.glob( './*.md'))
               for path in sorted(paths):

                   self.onDataAvailable( path )

            except Exception as e:
                print(e)


    def stop(self):
        self.evt_stop.set()

    def onDataAvailable( self, *args ):
        filePath = pathlib.Path( args[0] )

        if filePath.exists():
            jsonFileRaw = convert_md_to_json(filePath.read_text())

            jsonFileDict = json.loads(jsonFileRaw)

            propOwner = self.properties[ 'Owner' ]
            propOwner.value = jsonFileDict['HIVE testing log'][0]['Operators'][0]

            propOwnerGroup = self.properties[ 'Owner group' ]
            propOwnerGroup.value = 'HIVE'

            propPrincipleInvestigator = self.properties[ 'Principal Investigator' ]
            propPrincipleInvestigator.value = jsonFileDict['HIVE testing log'][0]['Operators'][0]

            propEmail = self.properties[ 'Contact email' ]
            propEmail.value = propOwner.value.replace(" ", "").lower() + '@ukaea.uk'

            propSourceFolder = self.properties[ 'Data source' ]
            propSourceFolder.value = jsonFileDict['HIVE testing log'][0]['Sample Name']

            propDate = self.properties[ 'Date' ]
            propDateStr = jsonFileDict['HIVE testing log'][0]['Date']
            propDate.value = datetime.datetime.strptime(propDateStr, '%Y%m%d').date().strftime('%d/%m/%Y')

            propLocation = self.properties[ 'Location' ]
            propLocation.value = 'FTF'

            propExperimentData = self.properties[ 'Experiment data' ]
            combined_data = {
                'Summary': jsonFileDict['Summary'],
                'Pulses': jsonFileDict['Pulses'],
                'Issues': jsonFileDict['Issues']
            }

            combined_json_string = json.dumps(combined_data, indent=2)
            propExperimentData = self.properties['Experiment data']
            propExperimentData.value = combined_json_string

            self.onSubmitRequest()

            try:
                shutil.move( filePath, pathlib.Path('/tmp') / filePath.name )
            except Exception as e:
                print(e)

            print('Data recieved')

    def onSubmitRequest(self):
        try:
            dataset = pyscicat.model.RawDataset(
                datasetName='myhive',
                owner=self.properties['Owner'].value,
                ownerGroup=self.properties['Owner group'].value,
                principalInvestigator=self.properties['Principal Investigator'].value,
                contactEmail=self.properties['Contact email'].value,
                sourceFolder=self.properties['Data source'].value,
                creationTime=self.properties['Date'].value,
                creationLocation=self.properties['Location'].value,
                scientificMetadata=json.loads(self.properties['Experiment data'].value),
                type="raw")
            
            print('Submitting dataset:', dataset.__dict__)
            res = self.host_services.requestDatasetSave( dataset )
            print(res)
        except Exception as e:
            print(e)

class Factory:

    def __call__(self, host_services):
        plugin = HivePlugin(host_services)

        return plugin


@log_decorator
def register_plugin_factory( host_services ):

    factory = Factory()

    host_services.register_plugin_factory( 'metadata_plugin', 'HivePlugin',  factory )
