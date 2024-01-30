import errno
import datetime
import fnmatch
import random
import shutil
import time
import json
import logging

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

import subprocess
import os

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
                   paths = self.root.glob( './*/*.md')
                   print(f"RetryWorker - Paths =   '{paths}'")
                   #paths = self.root.glob( './*/bagit.txt') 

                   for path in sorted(paths):
                       self.q_out.put( path )

                except Exception as e:
                    print(e)


class MyHandler( watchdog.events.FileSystemEventHandler ):
    '''MyHandler class is designed to handle file system events and specifically watches for the creation of bagit.txt files.'''
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

                #Ajay
                if fnmatch.fnmatch(path.name, '*.md'):
                #if path.name == 'bagit.txt':
                    #Ajay
                    print("RetryWorker - fnmatch.fnmatch(path.name, '*.md') TREU")

                    if path != self.last_created and datetime.datetime.now() - self.last_time > dt:
                        self.last_created = path
                        self.last_time = datetime.datetime.now()

                        self.signal.emit( evt.src_path )


class Producer( WorkerBase ):
    '''Producer class sets up file system monitoring using RetryWorker and MyHandler, creating workers, observing file system events,'''
    '''and managing threads to generate trigger events based on detected changes.'''
    ''' Generate trigger events using the RetryWorker and the MyHandler '''

    def __init__(self, q, path_spool = '/tmp/spool'):
        super().__init__()

        self.signal = core.Signal()
        self.count = 0
        self.q = q
        self.path_spool = pathlib.Path( path_spool )

    def run(self):

        path =  self.path_spool / 'bags' 
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


class HivePlugin( ingestorservices.plugin.PluginBase ):
    '''Wait for bagit events. Extract metadata from placeholder and bagit file before writing to backend '''

    #This method essentially initializes the HivePlugin object, creating threads for the producer and consumer, connecting signals, 
    # and setting up a GUI widget with properties and buttons for user interaction.
    def __init__(self, host_services):
        super().__init__(host_services)

        self.path_spool  = pathlib.Path('/tmp/spool')

        self.q = queue.Queue()
        
        self.producer = Producer(self.q)

        self.consumer = Consumer( self.q )

        #Sets up the signal-slot mechanism where the Consumer's sigDataAvailable signal is connected to the onDataAvailable method. 
        # This establishes a communication link between the consumer and the onDataAvailable method, meaning that 
        # whenever data is available in the consumer, it triggers the onDataAvailable method.
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


        prop_name = requireProperty( 'name', '' )
        prop_mandatory = requireProperty( 'mandatory1', '' )
        prop_user1 = requireProperty( 'user1', '' )
        prop_user2 = requireProperty( 'user2', '' )

        w = widgets.Widget.create()
        self.w = w

        vbox = widgets.VBoxLayout()

        label = widgets.Label.create('Hive plugin widget')
        vbox.addWidget( label )

        w.setLayout( vbox )

        self.btn = widgets.PushButton.create( 'Save Placeholder' )
        self.btn.clicked.connect( self.onRequestSavePlaceHolder )

        vbox.addWidget( self.btn )

        pg = services.properties.PropertyGroup( layout=services.properties.PropertyGroup.VERTICAL )
        pg.add( prop_name )
        pg.add( prop_mandatory )
        pg.add( prop_user1 )
        pg.add( prop_user2 )

        l =  services._property_group_2_layout( pg )

        vbox.addLayout( l )

        w.setLayout( vbox )


    def finish(self):
        self.producer.stop()
        self.consumer.stop()

        self.producer.join()
        self.consumer.join()


    def widget(self):
        return self.w

    def onRequestSavePlaceHolder(self):

        # onRequestSavePlaceHolder method updates the 'mandatory1' property, retrieves the 'name' property, logs a message, 
        # creates a dictionary from relevant properties, and saves this dictionary as a JSON file in the placeholder directory.
        prop = self.properties[  'mandatory1' ]
        prop.value = str(datetime.datetime.now())

        try:
            name = self.properties[ 'name'].value

            self.log('onRequestSavePlaceHolder %s' % name )

            j = {}
            j['name'] = name
            j['mandatory1']  =self.properties[ 'mandatory1'].value
            j['user1'] = self.properties[ 'user1'].value
            j['user2'] = self.properties[ 'user2'].value

            placeholder_path = self.path_spool / 'placeholder' 
            placeholder_path.mkdir( parents=True, exist_ok=True)

            path = placeholder_path / ('%s.json' % j['name'])
            with open( path, 'w') as f:
                json.dump( j, f )

        except:
            pass

    def onDataAvailable( self, *args ):
        # This method is called when data becomes available in the Consumer. It processes the bagit data and saves it as a dataset.
        host_services = self.host_services

        prop = self.properties[ 'mandatory1' ]
        prop.value = str(datetime.datetime.now() )

        #args[0] is the path of the bagit file
        bagit_path = pathlib.Path( args[0] )

        # Initialize an empty dictionary for merged JSON data
        # Initialize an empty dictionary for bagit JSON data
        j_sm = {}
        j_d = {}

        if bagit_path.exists():

            #extract data from bagit
            # bagit path : /tmp/spool/bags/bag8
            # bagit name : bag8
            path = bagit_path.parent
            name = path.name
            
            # get the name of the extracted json from markdown
            json_files = [file for file in os.listdir(path) if file.endswith('.json')]
            json_filename = None 
            for json_file in json_files:
                json_filename = json_file
                
            self.log( 'bagit path : %s' % path )
            self.log( 'bagit name : %s' % name )
            self.log( 'json_filename name : %s' % json_filename )

            #### -  Ajay Insert code to extract json from markdown file
           
            # Arguments to be passed to call markdown_json.py  to extract the json from markdown
            arguments_for_json_extract = [path, path]
            # Construct the command to call a.py with arguments
            command = ["python3", "markdown_json.py"] + arguments_for_json_extract

            # Use subprocess to call markdown_json.py
            subprocess.run(command)
            
            try:
                # Json extraction 
                #with open(path / (name + '.json'), 'r') as f:
                # added to get the json extracted from the markdown file
                with open(path / json_filename, 'r') as f:    
                    j_d = json.load( f )
                    #field1 = j_d['field1']
                    #field2 = j_d['field2']
                    #field3 = j_d['field3']
                    #field4 = j_d['field4']
                    #Ajay Rawat
                    owner = j_d['HIVE testing log'][0]['Operators']
                    print('*** OWNER')
                    print(owner[0])
                    ##
                    print(f"The Extracted JSON from Markdown is = {json_filename}")
            except Exception as e:
                print(e)
                pass

            ###### END #####

            # removed the logic and added above code to extracted json from the markdown file
            # try:
            #     # Json extraction 
            #     with open( path/'data/data.json', 'r' ) as f:
            #         j_d = json.load( f )
            #         #field1 = j_d['field1']
            #         #field2 = j_d['field2']
            #         #field3 = j_d['field3']
            #         #field4 = j_d['field4']

            # except Exception as e:
            #     print(e)
            #     pass

            #is there a placeholder?
            placeholder_id = name[3:]
            print(f"Place holder id = '{placeholder_id}'")

            try:
                placeholder_path = self.path_spool / 'placeholder' / ('%s.json' %placeholder_id )
                print(f"placeholder_path = '{placeholder_path}'")
                j_p = {}

                with open( placeholder_path, 'r' ) as f:
                    self.log(' Found placeholder : %s' % placeholder_path )

                    j_p = json.load( f )
                    print(" ----------The Placeholder JSON is as: ---------")
                    print(j_p)
                    #update tthe widget property
                    for name,value in j_p.items():

                        try:
                            p = self.properties[ name ]
                            p.value = value
                        except:
                            pass

                j_sm = { **j_d, **j_p }
                print(" ----------The Merged JSON is as: ---------")
                print(j_sm)

            except Exception as e:
                if e.errno == errno.ENOENT:
                    self.log(' No placeholder :  %s' % placeholder_path )
                else:
                    self.log(' %s' % str(e))

            self.log( j_sm )

            # Create an Ownable that will get reused for several other Model objects
            ownable = metadata.Ownable(ownerGroup="magrathea", createdBy=None, updatedBy=None, updatedAt=None, createdAt=None, instrumentGroup=None)

            name = 'bob' #HIVE testing log + date in the log line 4 change it format
            
            dataset = metadata.Dataset(
                    
                    #Ajay Rawat
                    #owner = ['HIVE testing log'][0]['Operators'][0],
                    owner="slartibartfast", #json
                    contactEmail="slartibartfast@magrathea.org", #dummy
                    creationLocation= 'magrathea',
                    creationTime=str(datetime.datetime.now()),
                    type="raw",
                    principalInvestigator="A. Mouse", # owner
                    sourceFolder='/foo/bar', # dummy
                    scientificMetadata=j_sm,
                    **ownable.dict()) # owner group

            # dataset_id = host_services.requestDatasetSave( str(name), dataset )

            # if dataset_id:
            #     shutil.rmtree( bagit_path.parent )

            #     try:
            #         placeholder_path.unlink()
            #     except:
            #         pass
            
            # Ajay Rawat
            # added to extract value from Json based on the key passed
    

class Factory:

    def __call__(self, host_services):

        plugin = HivePlugin(host_services)

        return plugin


@log_decorator
def register_plugin_factory( host_services ):

    factory = Factory()

    host_services.register_plugin_factory( 'metadata_plugin', 'HivePlugin',  factory )
