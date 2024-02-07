import datetime
import fnmatch
import json
import logging

from plugins.pegasusdevPlugin.extract import extractPegasus
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

import watchdog.observers
import watchdog.events

class WorkerBase( threading.Thread):
    '''WorkerBase class serves as a base for other classes and provides a method stop() that notifies any threads waiting on a condition (cond_stop)'''
    '''that a change has occurred, potentially used to indicate that the thread should stop its execution.'''
    def __init__(self):
        super().__init__()
        self.cond_stop = threading.Condition()

    def stop(self):
        
        with self.cond_stop:
            self.cond_stop.notify()


class RetryWorker( WorkerBase ):
    '''RetryWorker class periodically checks for bagit files in a specified directory (root) and puts their paths into a queue (q_out)'''
    '''for further processing, all while waiting for a signal to stop its execution.'''
    '''Periodically check for bagit files in spool path'''

    def __init__(self, path, q_out):

        super().__init__()

        self.root = path
        self.q_out = q_out


    def run(self):
        with self.cond_stop:
            while not self.cond_stop.wait(timeout=1):

                try:
                   # get the path of the markdown file here - Ajay
                   paths = self.root.glob( './*/*.out')
                   for path in sorted(paths):
                       self.q_out.put( path )

                except Exception as e:
                    print(e)


class MyHandler( watchdog.events.FileSystemEventHandler ):
    '''MyHandler class is designed to handle file system events and specifically watches for the creation of files.'''
    '''When a new bagit.txt file is created and the specified conditions are met, it emits a signal with the file's path.'''
    '''Watch for creation of bagit files using FileSystemEvents'''

    signal = core.Signal()
    def __init__(self, *args, **kwargs ):
        super().__init__( *args, **kwargs )
        self.last_created = None
        self.last_time = datetime.datetime.min

    def on_any_event(self, evt):
        path = pathlib.Path(evt.src_path)
        dt = datetime.timedelta(milliseconds=500)

        if evt.event_type == 'created':
                if fnmatch.fnmatch(path.name, '*.out'):
                    if path != self.last_created and datetime.datetime.now() - self.last_time > dt:
                        self.last_created = path
                        self.last_time = datetime.datetime.now()

                        self.signal.emit( evt.src_path )


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

        path =  self.path_spool / 'pegasus' 
        path.mkdir( parents=True, exist_ok=True)

        retry_worker = RetryWorker( path, self.q )
        retry_worker.daemon = True
        retry_worker.start()

        evt_handler = MyHandler()
        
        #when evt_handler emits a signal, onNewBagit method will be called.
        evt_handler.signal.connect( self.onNewBagit )

        observer = watchdog.observers.Observer()

        #Configures the observer to watch the path directory recursively for events and associates it with evt_handler.
        observer.schedule( evt_handler, path, recursive=True )

        observer.start()

        with self.cond_stop:
            while not self.cond_stop.wait(timeout=1):
                pass

        observer.stop()
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
        with self.cond_stop:
            while not self.cond_stop.wait(timeout=1):
                                     
                self.count += 1

                try:
                    res = self.q_in.get( block=True, timeout=0.2)
                    
                    self.sigDataAvailable.emit( res )

                    self.q_in.task_done()
                except queue.Empty:
                    pass


class PegasusPlugin( ingestorservices.plugin.PluginBase ):
    '''Wait for events. Extract metadata from placeholder and file before writing to backend '''

    def __init__(self, host_services):
        super().__init__(host_services)
        self.path_spool  = pathlib.Path('./data/pegasus')
        self.q = queue.Queue()
        self.producer = Producer(self.q)
        self.consumer = Consumer( self.q )
        self.consumer.sigDataAvailable.connect( self.onDataAvailable )

        for t in [self.consumer, self.producer]:
            t.daemon = True
            t.start()

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
                prop = services.properties.BoxProperty( name, value )
                self.properties[ prop.name ] = prop

            return prop

        prop_owner = requireProperty( 'Owner', '' )
        prop_ownerGroup = requireProperty( 'Owner group', '' )
        prop_investigator = requireProperty( 'Investigator', '' )
        prop_email = requireProperty( 'Contact email', '' )
        prop_creationDate = requireProperty( 'Date', '' )        
        prop_sourceFolder = requireProperty( 'Data source', '' )
        prop_inputDataset = requireProperty( 'Experimental source', '' )
        prop_software = requireProperty( 'Software', '' )
        prop_experimentData = boxProperty( 'Simulation data', '' )

        w = widgets.Widget.create()
        self.w = w

        vbox = widgets.VBoxLayout()

        pg = services.properties.PropertyGroup( layout=services.properties.PropertyGroup.VERTICAL )
        pg.add( prop_owner )
        pg.add( prop_ownerGroup )
        pg.add( prop_investigator )
        pg.add( prop_email )
        pg.add( prop_creationDate)
        pg.add( prop_sourceFolder )
        pg.add( prop_inputDataset )
        pg.add( prop_software )
        pg.add( prop_experimentData )
        mainMetadataLayout =  services._property_group_4_layout( pg )
        vbox.addLayout(mainMetadataLayout)

        # Add submit button
        self.btn = widgets.PushButton.create('Submit')
        self.btn.clicked.connect(self.onSubmitRequest)
        vbox.addWidget(self.btn)

        w.setLayout( vbox )


    def finish(self):
        self.producer.stop()
        self.consumer.stop()

        self.producer.join()
        self.consumer.join()


    def widget(self):
        return self.w

    def onDataAvailable( self, *args ):
        filePath = pathlib.Path( args[0] )

        if filePath.exists():
            jsonFileRaw = extractPegasus(filePath.absolute())
            jsonFileDict = json.loads(jsonFileRaw)

            propOwner = self.properties[ 'Owner' ]
            propOwner.value = 'PEGASUS'

            propOwnerGroup = self.properties[ 'Owner group' ]
            propOwnerGroup.value = 'PEGASUS'

            propInvestigator = self.properties[ 'Investigator' ]
            propInvestigator.value = 'PEGASUS'

            propEmail = self.properties[ 'Contact email' ]
            propEmail.value = 'pegasus@ukaea.uk'

            propDate = self.properties[ 'Date' ]
            dateRun = jsonFileDict['Stats'][0]['execution_info']['date_run']
            propDate.value = datetime.datetime.strptime(dateRun, "%m/%d/%Y").strftime("%d/%m/%Y")

            propDataSource = self.properties[ 'Data source' ]
            propDataSource.value = '/path/to/data'

            propDataInput = self.properties[ 'Experimental source' ]
            propDataInput.value = '/path/to/data'

            propDataSoftware = self.properties[ 'Software' ]
            propDataSoftware.value = 'ANSYS Mechanical'

            propExperimentData = self.properties[ 'Simulation data' ]
            propExperimentData.value = jsonFileRaw

    def onSubmitRequest(self):
        dataset = metadata.Dataset(
            owner=self.properties['Owner'].value,
            ownerGroup=self.properties['Owner group'].value,
            investigator=self.properties['Investigator'].value,
            contactEmail=self.properties['Contact email'].value,
            sourceFolder=self.properties['Data source'].value,
            inputDataset=[self.properties['Experimental source'].value],
            usedSoftware=[self.properties['Software'].value],
            creationTime=self.properties['Date'].value,
            scientificMetadata=json.loads(self.properties['Simulation data'].value),
            type="derived")
        
        print('Submitting dataset:', dataset.__dict__)

class Factory:

    def __call__(self, host_services):

        plugin = PegasusPlugin(host_services)

        return plugin


@log_decorator
def register_plugin_factory( host_services ):

    factory = Factory()

    host_services.register_plugin_factory( 'metadata_plugin', 'PegasusPlugin',  factory )