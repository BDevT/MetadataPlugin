"""
This module defines the PegasusPlugin class, which inherits from the `ingestorservices.plugin.PluginBase` class.

The PegasusPlugin ingests data from text files and populates metadata fields based on the content.

This module implements a plugin for extracting metadata from tex files and submitting it to a backend system.

Classes:

- WorkerBase: A base class for worker threads that provides a stop() method.
- RetryWorker: A worker that periodically checks for text files in a spool path and puts their paths into a queue.
- MyHandler: This class handles file system events, specifically watching for creation of text files with the desired extension and emitting a signal with the file path under specific conditions.
- Producer: A producer thread that uses a RetryWorker to generate trigger events.
- Consumer: A consumer thread that receives event paths from a queue and emits a signal with the retrieved data.
- PegasusPlugin: A plugin that extracts metadata from text files and writes it to a backend.
- Factory: A factory that creates instances of the PegasusPlugin.

Functions:

- register_plugin_factory(host_services): Registers the PegasusPlugin factory with the host services.
"""
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
    """
    Base class for worker threads used in the PegasusPlugin.

    This class extends threading.Thread to provide a common interface for worker threads.
    
    Provides a method `stop()` that notifies any threads waiting on a condition (`cond_stop`) 
    that a change has occurred, potentially used to indicate that the thread should stop its execution.
    """
    def __init__(self):
        """
        Initializes the base worker thread.
        """
        super().__init__()
        self.cond_stop = threading.Condition()

    def stop(self):
        """
        Sets the stop event for the worker thread, signaling it to stop.
        """
        with self.cond_stop:
            self.cond_stop.notify()

class RetryWorker( WorkerBase ):
    """
    Worker thread that monitors a directory for new data files and puts them into a queue.

    It puts their paths into a specified queue (q_out) for further processing, all while waiting for a signal to stop its execution.
    """
    def __init__(self, path, q_out):
        """
        Initializes the RetryWorker.

        Args:
            path (pathlib.Path): The path to the directory to monitor.
            q_out (queue.Queue): The queue to put discovered data file paths into.
        """ 
        super().__init__()

        self.root = path
        self.q_out = q_out


    def run(self):
        """
        Main loop of the RetryWorker.

        Continuously checks the monitored directory for new data files and puts them
        into the output queue. Stops when the stop event is set.
        """
        with self.cond_stop:
            while not self.cond_stop.wait(timeout=1):

                try:
                   # get the path of the text file here
                   paths = self.root.glob( './*/*.out')
                   for path in sorted(paths):
                       self.q_out.put( path )

                except Exception as e:
                    print(e)

"""
The MyHandler class inherited from watchdog.events.FileSystemEventHandler.

It monitors a directory for file creation events and emits a signal 
when a specific type of file is created after a debounced delay.
"""
class MyHandler( watchdog.events.FileSystemEventHandler ):
    """
    Custom file system event handler that reacts to file creation events with a debounced signal.

    Inherits from watchdog.events.FileSystemEventHandler and provides customized behavior for specific events.

    Attributes:
        signal (core.Signal): A signal object used to emit events when a relevant file is created.
        last_created (pathlib.Path, optional): The path to the last created file that met the criteria. Defaults to None.
        last_time (datetime.datetime): The timestamp of the last file creation event that met the criteria. Defaults to datetime.datetime.min.
    """
    signal = core.Signal()
    def __init__(self, *args, **kwargs ):
        """
        Initializes the MyHandler object.

        Args:
            *args: Arguments passed to the parent class (FileSystemEventHandler) constructor.
            **kwargs: Keyword arguments passed to the parent class (FileSystemEventHandler) constructor.
        """
        super().__init__( *args, **kwargs )
        self.last_created = None
        self.last_time = datetime.datetime.min

    def on_any_event(self, evt):
        """
        Handles any file system event received by the handler.

        Checks if the event is a 'created' event for a file ending in '.out' and implements debouncing logic.
        If the conditions are met, emits a signal with the source path of the created file.

        Args:
            evt (watchdog.events.FileSystemEvent): The file system event object.
        """
        path = pathlib.Path(evt.src_path)
        dt = datetime.timedelta(milliseconds=500)

        if evt.event_type == 'created':
                if fnmatch.fnmatch(path.name, '*.out'):
                    if path != self.last_created and datetime.datetime.now() - self.last_time > dt:
                        self.last_created = path
                        self.last_time = datetime.datetime.now()

                        self.signal.emit( evt.src_path )


class Producer( WorkerBase ):
    """
    Worker thread that monitors a queue for new Markdown file paths and passes them to the consumer.
    
    Producer class for file system monitoring and trigger event generation.
    """
    '''Producer class sets up file system monitoring using RetryWorker and MyHandler, creating workers, observing file system events,'''
    '''and managing threads to generate trigger events based on detected changes.'''
    ''' Generate trigger events using the RetryWorker and the MyHandler '''

    def __init__(self, q, path_spool = './data'):
        """
        Initializes the Producer.

        Args:
            q (queue.Queue): The queue to receive file paths from.
            path_spool (str, optional): The directory to create the "pegasus" subdirectory in. Defaults to "./data".
        """
        super().__init__()

        self.signal = core.Signal()
        self.count = 0
        self.q = q
        self.path_spool = pathlib.Path( path_spool )

    def run(self):
        """
        Main loop of the Producer.

        Creates a "pegasus" subdirectory in the specified path spool and starts a RetryWorker
        to monitor that directory. Continuously checks the input queue for new paths and
        signals the consumer when a new path is available. Stops when the stop event is set.
        """
        path =  self.path_spool / 'pegasus' 
        path.mkdir( parents=True, exist_ok=True)

        retry_worker = RetryWorker( path, self.q )
        retry_worker.daemon = True
        retry_worker.start()

        evt_handler = MyHandler()
        
        #when evt_handler emits a signal, onNewFiles method will be called.
        evt_handler.signal.connect( self.onNewFiles )

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

    def onNewFiles(self, path):
        """
        Emits a signal when a new text (file) is available.

        Args:
            path (pathlib.Path): The path to the new Hive data.
        """
        self.q.put( path )

class Consumer( WorkerBase ):
    """
    Worker thread that receives Markdown file paths from the producer and processes them.

    Consumer class is designed to continuously run in a thread, checking the input queue for data. 
    When data is available in the queue, it emits a signaln (sigDataAvailable) with the retrieved data 
    and proceeds with further tasks if any, continually checking the queue for more data to process.
    """
    def __init__(self, q_in ):
        """
        Initializes the Consumer.

        Args:
            q_in (queue.Queue): The queue to receive Markdown file paths from.
        """
        super().__init__()
        self.q_in = q_in
        self.count = 0

        self.sigDataAvailable = core.Signal()

    def run(self):
        """
        Main loop of the Consumer.

        Continuously checks the input queue for new paths. When a path is available,
        it retrieves it, emits a signal with the path, and marks the task as done in the queue.
        Stops when the stop event is set.
        """
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
        print("Submitting dataset to backend")

class Factory:

    def __call__(self, host_services):

        plugin = PegasusPlugin(host_services)

        return plugin


@log_decorator
def register_plugin_factory( host_services ):

    factory = Factory()

    host_services.register_plugin_factory( 'metadata_plugin', 'PegasusPlugin',  factory )