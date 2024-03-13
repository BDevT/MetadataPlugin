"""
This module defines the HivePlugin class, which inherits from the `ingestorservices.plugin.PluginBase` class.

The HivePlugin ingests data from Markdown files and populates metadata fields based on the content.

This module implements a plugin for extracting metadata from Markdown files and submitting it to a backend system.

Classes:

- WorkerBase: A base class for worker threads that provides a stop() method.
- RetryWorker: A worker that periodically checks for Markdown files in a spool path and puts their paths into a queue.
- MyHandler: This class handles file system events, specifically watching for creation of markdown files with the desired extension and emitting a signal with the file path under specific conditions.
- Producer: A producer thread that uses a RetryWorker to generate trigger events.
- Consumer: A consumer thread that receives event paths from a queue and emits a signal with the retrieved data.
- HivePlugin: A plugin that extracts metadata from Markdown files and writes it to a backend.
- Factory: A factory that creates instances of the HivePlugin.

Functions:

- register_plugin_factory(host_services): Registers the HivePlugin factory with the host services.
"""
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

import watchdog.observers
import watchdog.events

class WorkerBase( threading.Thread):
    """
    Base class for worker threads used in the HivePlugin.

    This class extends threading.Thread to provide a common interface for worker threads.
    
    Provides a method `stop()` that notifies any threads waiting on a condition (`cond_stop`) 
    that a change has occurred, potentially used to indicate that the thread should stop its execution.
    """
    def __init__(self):
        """
        Initializes the base worker thread.
        """
        super().__init__()
        self.evt_stop = threading.Event()

    def stop(self):
        """
        Sets the stop event for the worker thread, signaling it to stop.
        """
        self.evt_stop.set()


class RetryWorker( WorkerBase ):
    """
    Worker thread that monitors a directory for new Markdown files and puts them into a queue.

    It puts their paths into a specified queue (q_out) for further processing, all while waiting for a signal to stop its execution.
    """
    def __init__(self, path, q_out):
        """
        Initializes the RetryWorker.

        Args:
            path (pathlib.Path): The path to the directory to monitor.
            q_out (queue.Queue): The queue to put discovered Markdown file paths into.
        """
        super().__init__()

        self.root = path
        self.q_out = q_out


    def run(self):
         """
        Main loop of the RetryWorker.

        Continuously checks the monitored directory for new Markdown files and puts them
        into the output queue. Stops when the stop event is set.
        """
         while not self.evt_stop.wait(timeout=1):

            try:
                # get the path of the markdown file here - Ajay
                paths = self.root.glob( './*/*.md')
                for path in sorted(paths):
                    self.q_out.put( path )

            except Exception as e:
                print(e)

class MyHandler( watchdog.events.FileSystemEventHandler ):
    """
    MyHandler class is designed to handle file system events and specifically watches for the creation of files.
    
    When a new markdown file is created and the specified conditions are met, it emits a signal with the file's path.

    This class utilizes FileSystemEvents to monitor file creation and emits a signal only under specific conditions:
     - The created file must have a `.md` extension (configurable through filename matching).
     - There must be a minimum time gap (default 500 milliseconds) between emitting signals for subsequent file creations.
    """
    signal = core.Signal()
    def __init__(self, *args, **kwargs ):
        """
        Constructor for MyHandler class.
        Args:
            *args: Arguments to be passed to the base class constructor (FileSystemEventHandler).
            **kwargs: Keyword arguments to be passed to the base class constructor (FileSystemEventHandler).
        """
        super().__init__( *args, **kwargs )
        self.last_created = None
        self.last_time = datetime.datetime.min

    def on_any_event(self, evt):
        """
        Handles all file system events.

        This method is called for any file system event that occurs within the watched directory.
        It checks for 'created' events and filters them based on file extension and time gap.

        Args:
            evt: A FileSystemEvent object representing the file system event.
        """
        path = pathlib.Path(evt.src_path)
        dt = datetime.timedelta(milliseconds=500)

        if evt.event_type == 'created':
                if fnmatch.fnmatch(path.name, '*.md'):
                    if path != self.last_created and datetime.datetime.now() - self.last_time > dt:
                        self.last_created = path
                        self.last_time = datetime.datetime.now()

                        self.signal.emit( evt.src_path )

class Producer( WorkerBase ):
    """
    Worker thread that monitors a queue for new Markdown file paths and passes them to the consumer.
    
    Producer class for file system monitoring and trigger event generation.
    """
    def __init__(self, q, path_spool = './data'):
        """
        Initializes the Producer.

        Args:
            q (queue.Queue): The queue to receive file paths from.
            path_spool (str, optional): The directory to create the "hive" subdirectory in. Defaults to "./data".
        """
        super().__init__()

        self.signal = core.Signal()
        self.count = 0
        self.q = q
        self.path_spool = pathlib.Path( path_spool )

    def run(self):
        """
        Main loop of the Producer.

        Creates a "hive" subdirectory in the specified path spool and starts a RetryWorker
        to monitor that directory. Continuously checks the input queue for new paths and
        signals the consumer when a new path is available. Stops when the stop event is set.
        """
        path =  self.path_spool / 'hive' 
        path.mkdir( parents=True, exist_ok=True)

        retry_worker = RetryWorker( path, self.q )
        retry_worker.daemon = True
        retry_worker.start()

        evt_handler = MyHandler()
        
        #when evt_handler emits a signal, onNewBagit method will be called.
        evt_handler.signal.connect( self.onNewFiles )

        observer = watchdog.observers.Observer()

        #Configures the observer to watch the path directory recursively for events and associates it with evt_handler.
        observer.schedule( evt_handler, path, recursive=True )
        observer.start()

        while not self.evt_stop.wait(timeout=1):
            pass

        observer.stop()
        retry_worker.stop()
        retry_worker.join()

    def onNewFiles(self, path):
        """
        Emits a signal when a new Hive (file) is available.

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
        while not self.evt_stop.wait(timeout=1):
                                     
            self.count += 1

            try:
                res = self.q_in.get( block=True, timeout=0.2)
                    
                self.sigDataAvailable.emit( res )

                self.q_in.task_done()
            except queue.Empty:
                pass

"""
The HivePlugin class is a plugin for the IngestorServices framework.

It waits for events, extracts metadata from Markdown files, and writes the metadata to a backend.

This class:
  - Starts producer and consumer threads to process Markdown files.
  - Defines properties for capturing user input and storing extracted metadata.
  - Creates a user interface widget for interacting with the plugin.
  - Defines callbacks for processing data and submitting the final dataset.
"""
class HivePlugin( ingestorservices.plugin.PluginBase ):
    """
    Waits for events, extracts metadata from Markdown files, and writes the metadata to a backend.
    """
    def __init__(self, host_services):
        """
        Initializes the HivePlugin.

        Args:
            host_services (ingestorservices.host.HostServices): The host services object providing access
                to framework functionalities.
        """
        super().__init__(host_services)

        self.path_spool  = pathlib.Path('./data/hive')
        self.q = queue.Queue()
        self.producer = Producer(self.q)
        self.consumer = Consumer(self.q)
        self.consumer.sigDataAvailable.connect(self.onDataAvailable)

        for t in [self.consumer, self.producer]:
            #t.daemon = True
            t.start()

        # Helper functions for creating and managing properties
        def requireProperty( name, value ):
            """
            Attempts to get a property from the plugin's properties. If the property doesn't exist,
            creates a new one with the provided name and value.

            Args:
                name (str): The name of the property.
                value (str): The initial value of the property.

            Returns:
                services.properties.Property: The retrieved or created property.
            """
            try:
                prop = self.properties( name )
            except Exception as e:

                prop = services.properties.Property( name, value )

                self.properties[ prop.name ] = prop

            return prop

        def boxProperty( name, value ):
            """
            Ensure a property exists or create a new one.
            Args:
                name (str): The name of the property.
                value (str): The initial value of the property.

            Returns:
                services.properties.Property: The created property.
            """
            try:
                prop = self.properties( name )
            except Exception as e:
                prop = services.properties.Property( name, value )
                self.properties[ prop.name ] = prop

            return prop
        
        # Define properties for user input and extracted metadata
        prop_owner = requireProperty( 'Owner', '' )
        prop_ownerGroup = requireProperty( 'Owner group', '' )
        prop_principleInvestigator = requireProperty( 'Principal Investigator', '' )
        prop_email = requireProperty( 'Contact email', '' )
        prop_sourceFolder = requireProperty( 'Data source', '' )
        prop_creationDate = requireProperty( 'Date', '' )
        prop_location = requireProperty( 'Location', '' )
        prop_experimentData = boxProperty( 'Experiment data', '' )

        w = widgets.Widget.create()
        self.w = w

        vbox = widgets.VBoxLayout()

        # Create a property group to display and manage properties
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

    def run(self):
        """
        Runs the plugin.
        """
        for t in [self.consumer, self.producer]:
            #t.daemon = True
            t.join()

    def stop(self):
        """
        Stops the plugin.
        """
        self.producer.stop()
        self.consumer.stop()

        self.producer.join()
        self.consumer.join()


    def widget(self):
        """
        Returns the plugin's widget.

        Returns:
            The plugin's widget.
        """
        return self.w

    def onDataAvailable( self, *args ):
        """
        Handles available data.

        Args:
            args: Variable length argument list.
        """
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
        """
        Handles submit request.
        """
        print("Submitting dataset to backend")

class Factory:
    """
    Factory class that creates instances of the HivePlugin.
    """
    def __call__(self, host_services):
        """
        Creates and returns an instance of the HivePlugin.

        Args:
            host_services (IngestorServices): The host IngestorServices instance.

        Returns:
            HivePlugin: An instance of the HivePlugin class.
        """
        plugin = HivePlugin(host_services)

        return plugin

@log_decorator
def register_plugin_factory( host_services ):
    """
    Registers the HivePlugin factory with the host services.

    This function creates a `Factory` instance, which provides the `HivePlugin` class,
    and registers it with the host services using the `register_plugin_factory` method.
    The plugin is registered as a 'metadata_plugin' of type 'HivePlugin'.

    Args:
        host_services (object): An object representing the host services framework.
    """
    factory = Factory()

    host_services.register_plugin_factory( 'metadata_plugin', 'HivePlugin',  factory )