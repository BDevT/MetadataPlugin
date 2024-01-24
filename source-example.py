import dataclasses
import datetime
import time
import random
import json
import shutil
import pathlib
import tempfile

import bagit





@dataclasses.dataclass
class Data:
    field1 : int
    field2: float
    field3 : str
    field4 : str
    mandatory1 : str

    def next(self):
        self.field1 = random.randint(0,1)
        self.field2 = random.uniform( 0.0, 100.0 )
        self.field3 = str(datetime.datetime.now())
        self.field4 = [ 'cat', 'dog', 'rabbit' ][ random.randint(0,2) ]
        
        l =  [ 'copper', 'silver', 'iron', 'lead', 'titanium' ]
        self.mandatory1 = l[ random.randint(0,len(l)-1)  ]

    def to_json(self):
        j = {}
        j[ 'field1'] = self.field1
        j['field2'] = self.field2
        j['field3'] = self.field3
        j['field4'] = self.field4
        j['mandatory1'] = self.mandatory1
        return j

data = Data(0,0.0,"","", "")
running = True

spool_path = pathlib.Path( '/tmp/spool' )
bag_root = spool_path / 'bags'

nmax = 9
n = 0

while running:

    ns = range(1,10)
    for n in ns:

        time.sleep( 1.0 )

        path = bag_root / 'bag{0}'.format( n )

        data.next()

        print(data)

        try:
            shutil.rmtree( path )
        except:
            pass

        pathlib.Path( path ).mkdir( parents=True, exist_ok=True)

        try:

            with open( path / 'data.json', 'w') as f:
                j = data.to_json()
                json.dump( j, f)

            bag = bagit.make_bag( path )

        except Exception as e:
            print(e, path)


        running = False
    
