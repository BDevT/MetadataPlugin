import errno
import datetime
import random
import time
import json
import logging
import shutil

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
    def __init__(self):
        super().__init__()
        self.cond_stop = threading.Condition()

    def stop(self):
        
        with self.cond_stop:
            self.cond_stop.notify()


class RetryWorker( WorkerBase ):
    '''Periodically check for bagit files in spool path'''

    def __init__(self, path, q_out):

        super().__init__()

        self.root = path
        self.q_out = q_out


    def run(self):
        with self.cond_stop:
            while not self.cond_stop.wait(timeout=1):

                try:
                   paths = self.root.glob( './*/bagit.txt') 

                   for path in sorted(paths):
                       self.q_out.put( path )

                except Exception as e:
                    print(e)


class MyHandler( watchdog.events.FileSystemEventHandler ):
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

                if path.name == 'bagit.txt':
                    if path != self.last_created and datetime.datetime.now() - self.last_time > dt:
                        self.last_created = path
                        self.last_time = datetime.datetime.now()

                        self.signal.emit( evt.src_path )


class Producer( WorkerBase ):
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

        evt_handler.signal.connect( self.onNewBagit )

        observer = watchdog.observers.Observer()
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


class ExamplePlugin( ingestorservices.plugin.PluginBase ):
    '''Wait for bagit events. Extract metadata from placeholder and bagit file before writing to backend '''

    def __init__(self, host_services):
        super().__init__(host_services)

        self.path_spool  = pathlib.Path('/tmp/spool')

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


        prop_name = requireProperty( 'name', '' )
        prop_mandatory = requireProperty( 'mandatory1', '' )
        prop_user1 = requireProperty( 'user1', '' )
        prop_user2 = requireProperty( 'user2', '' )

        w = widgets.Widget.create()
        self.w = w

        vbox = widgets.VBoxLayout()

        label = widgets.Label.create('Example plugin widget')
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

    def run(self):
        pass


    def finish(self):
        self.producer.stop()
        self.consumer.stop()

        self.producer.join()
        self.consumer.join()


    def widget(self):
        return self.w

    def onRequestSavePlaceHolder(self):

        print('SAVEXXXXXXXXX')

        prop = self.properties[  'mandatory1' ]
        prop.value = str(datetime.datetime.now() )

        try:
            name = self.properties[ 'name'].value

            print('NAME:%s:'%name )

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
        print('DATAXXXXXXX')
        host_services = self.host_services

        prop = self.properties[ 'mandatory1' ]
        prop.value = str(datetime.datetime.now() )

        bagit_path = pathlib.Path( args[0] )

        j_sm = {}
        j_d = {}

        if bagit_path.exists():

            #extract data from bagit

            path = bagit_path.parent
            name = path.name

            self.log( 'bagit path : %s' % path )

            try:

                with open( path/'data/data.json', 'r' ) as f:
                    j_d = json.load( f )
                    #field1 = j_d['field1']
                    #field2 = j_d['field2']
                    #field3 = j_d['field3']
                    #field4 = j_d['field4']

            except Exception as e:
                print(e)
                pass

            #is there a placeholder?
            placeholder_id = name[3:]

            print('NAMEXXXXXXXX', placeholder_id )

            try:
                placeholder_path = self.path_spool / 'placeholder' / ('%s.json' %placeholder_id )

                j_p = {}

                with open( placeholder_path, 'r' ) as f:

                    self.log(' Found placeholder : %s' % placeholder_path )

                    j_p = json.load( f )

                    #update tthe widget property
                    for name,value in j_p.items():

                        try:
                            p = self.properties[ name ]
                            p.value = value
                        except:
                            pass

                j_sm = { **j_d, **j_p }


            except Exception as e:
                if e.errno == errno.ENOENT:
                    self.log(' No placeholder :  %s' % placeholder_path )
                else:
                    self.log(' %s' % str(e))

            self.log( j_sm )

            # Create an Ownable that will get reused for several other Model objects
            ownable = metadata.Ownable(ownerGroup="magrathea", accessGroups=["deep_though"], createdBy=None, updatedBy=None, updatedAt=None, createdAt=None, instrumentGroup=None)

            name = 'bob'

            print('SSSSSS')
            ownable_dict = ownable.dict()
            print('FFFFFFf')

            dataset = metadata.Dataset(
                    path='/foo/bar',
                    datasetName=str(name),
                    size=42,
                    owner="slartibartfast",
                    contactEmail="slartibartfast@magrathea.org",
                    creationLocation= 'magrathea',
                    creationTime=str(datetime.datetime.now()),
                    type="raw",
                    instrumentId="earth",
                    proposalId="deepthought",
                    dataFormat="planet",
                    principalInvestigator="A. Mouse",
                    sourceFolder='/foo/bar',
                    scientificMetadata= j_sm,
                    sampleId="gargleblaster",
                    version='1'
                    ,validatationStatus=1
                    ,**ownable.dict())

            print('TRY1', name, dataset, host_services)
            dataset_id = host_services.requestDatasetSave( dataset )

            print('TRY2', dataset_id)

            if dataset_id:
                shutil.rmtree( bagit_path.parent )

                try:
                    placeholder_path.unlink()
                except:
                    pass


class Factory:

    def __call__(self, host_services):

        plugin = ExamplePlugin(host_services)

        return plugin


@log_decorator
def register_plugin_factory( host_services ):

    factory = Factory()

    host_services.register_plugin_factory( 'metadata_plugin', 'ExamplePlugin',  factory )
