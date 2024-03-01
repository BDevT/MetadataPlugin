import datetime
import fnmatch
import json
import logging

from plugins.hivedevPlugin.extract import convert_md_to_json

logger = logging.getLogger( __name__ )

import ingestorservices as services
import ingestorservices.widgets as widgets
import ingestorservices.core as core
import ingestorservices.metadata as metadata
import ingestorservices.plugin

log_decorator = core.create_logger_decorator( logger )

import threading
import queue
import pathlib

#import watchdog.observers
#import watchdog.events
#from scitacean.testing.docs import setup_fake_client
#from scitacean import Client, Dataset

class WorkerBase( threading.Thread):
    '''WorkerBase class serves as a base for other classes and provides a method stop() that notifies any threads waiting on a condition (cond_stop)'''
    '''that a change has occurred, potentially used to indicate that the thread should stop its execution.'''
    def __init__(self):
        super().__init__()
        self.evt_stop = threading.Event()

    def stop(self):
        
            self.evt_stop.set()


class RetryWorker( WorkerBase ):
    '''RetryWorker class periodically checks for bagit files in a specified directory (root) and puts their paths into a queue (q_out)'''
    '''for further processing, all while waiting for a signal to stop its execution.'''
    '''Periodically check for bagit files in spool path'''

    def __init__(self, path, q_out):

        super().__init__()

        self.root = path
        self.q_out = q_out


    def run(self):
            while not self.evt_stop.wait(timeout=1):

                try:
                   # get the path of the markdown file here - Ajay
                   paths = self.root.glob( './*/*.md')
                   for path in sorted(paths):
                       self.q_out.put( path )

                except Exception as e:
                    print(e)



class Producer( WorkerBase ):
    '''Producer class sets up file system monitoring using RetryWorker and MyHandler, creating workers, observing file system events,'''
    '''and managing threads to generate trigger events based on detected changes.'''
    ''' Generate trigger events using the RetryWorker and the MyHandler '''

    def __init__(self, q, path_spool = './data'):
        super().__init__()

        self.signal = core.Signal()
        self.count = 0
        self.q = q
        self.path_spool = pathlib.Path( path_spool )

    def run(self):

        path =  self.path_spool / 'hive' 
        path.mkdir( parents=True, exist_ok=True)

        retry_worker = RetryWorker( path, self.q )
        retry_worker.daemon = True
        retry_worker.start()

        #evt_handler = MyHandler()
        
        #when evt_handler emits a signal, onNewBagit method will be called.
        #evt_handler.signal.connect( self.onNewBagit )

        #observer = watchdog.observers.Observer()

        #Configures the observer to watch the path directory recursively for events and associates it with evt_handler.
        #observer.schedule( evt_handler, path, recursive=True )

        #observer.start()

        while not self.evt_stop.wait(timeout=1):
            pass

        #observer.stop()
        retry_worker.stop() 
        retry_worker.join()

    def onNewBagit(self, path):
        self.q.put( path )

class Consumer( WorkerBase ):
    '''Consumer class is designed to continuously run in a thread, checking the input queue for data. When data is available in the queue, it emits a signal'''
    '''(sigDataAvailable) with the retrieved data and proceeds with further tasks if any, continually checking the queue for more data to process.'''
    
    '''Recieve event paths '''

    def __init__(self, q_in ):

        super().__init__()
        self.q_in = q_in
        self.count = 0

        self.sigDataAvailable = core.Signal()

    def run(self):
            while not self.evt_stop.wait(timeout=1):
                                     
                self.count += 1

                try:
                    res = self.q_in.get( block=True, timeout=0.2)
                    
                    self.sigDataAvailable.emit( res )

                    self.q_in.task_done()
                except queue.Empty:
                    pass


class HivePlugin( ingestorservices.plugin.PluginBase ):
    '''Wait for events. Extract metadata from placeholder and file before writing to backend '''

    def __init__(self, host_services):
        super().__init__(host_services)
        self.path_spool  = pathlib.Path('./data/hive')
        self.q = queue.Queue()
        self.producer = Producer(self.q)
        self.consumer = Consumer( self.q )
        self.consumer.sigDataAvailable.connect( self.onDataAvailable )

        for t in [self.consumer, self.producer]:
            #t.daemon = True
            t.start()

        print('HIVE1')

        def requireProperty( name, value ):

            try:
                prop = self.properties( name )
            except Exception as e:

                prop = services.properties.Property( name, value )

                self.properties[ prop.name ] = prop

            return prop

        def boxProperty( name, value ):
            try:
                prop = self.properties( name )
            except Exception as e:
                prop = services.properties.Property( name, value )
                self.properties[ prop.name ] = prop

            return prop

        prop_owner = requireProperty( 'Owner', '' )
        prop_ownerGroup = requireProperty( 'Owner group', '' )
        prop_principleInvestigator = requireProperty( 'Principal Investigator', '' )
        prop_email = requireProperty( 'Contact email', '' )
        prop_sourceFolder = requireProperty( 'Data source', '' )
        prop_creationDate = requireProperty( 'Date', '' )
        prop_location = requireProperty( 'Location', '' )

        print('HIVE2')
        prop_experimentData = boxProperty( 'Experiment data', '' )

        print('HIVE4')

        w = widgets.Widget.create()
        self.w = w

        vbox = widgets.VBoxLayout()

        pg = services.properties.PropertyGroup( layout=services.properties.PropertyGroup.VERTICAL )
        pg.add( prop_owner )
        pg.add( prop_ownerGroup )
        pg.add( prop_principleInvestigator )
        pg.add( prop_email )
        pg.add( prop_sourceFolder )
        pg.add( prop_creationDate)
        pg.add( prop_location )
        pg.add( prop_experimentData )
        mainMetadataLayout =  services._property_group_2_layout( pg )
        vbox.addLayout(mainMetadataLayout)

        # Add submit button
        self.btn = widgets.PushButton.create('Submit')
        self.btn.clicked.connect(self.onSubmitRequest)
        vbox.addWidget(self.btn)

        w.setLayout( vbox )

        print('HIVE6')

    def run(self):
        print('RUNNNING')
        for t in [self.consumer, self.producer]:
            #t.daemon = True
            t.join()




    def stop(self):
        self.producer.stop()
        self.consumer.stop()

        self.producer.join()
        self.consumer.join()


    def widget(self):
        return self.w

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

    def onSubmitRequest(self):
        dataSet = Dataset(
            owner=self.properties['Owner'].value,
            owner_group=self.properties['Owner group'].value,
            principal_investigator=self.properties['Principal Investigator'].value,
            contact_email=self.properties['Contact email'].value,
            source_folder=self.properties['Data source'].value,
            creation_time=self.properties['Date'].value,
            creation_location=self.properties['Location'].value,
            meta=json.loads(self.properties['Experiment data'].value),
            type="raw"
        )

        print(dataSet)

class Factory:

    def __call__(self, host_services):

        plugin = HivePlugin(host_services)

        return plugin


@log_decorator
def register_plugin_factory( host_services ):

    factory = Factory()

    host_services.register_plugin_factory( 'metadata_plugin', 'HivePlugin',  factory )
