"""
This module provides functionality for running plugins.

Classes:
    - keyvalue: An argparse action to handle key-value pairs as command-line arguments.

Functions:
    - main(): The main entry point for running the plugin.
"""
import  argparse
import pkgutil
#import time
import requests
import sys

import ingestorservices

# create a keyvalue class 
class keyvalue(argparse.Action): 
    """
    An argparse action to handle key-value pairs as command-line arguments.
    """
    # Constructor calling 
    def __call__( self , parser, namespace, 
                 values, option_string = None): 
        setattr(namespace, self.dest, dict()) 

        for value in values: 
            # split it into key and value 
            key, value = value.split('=') 
            # assign into dictionary 
            getattr(namespace, self.dest)[key] = value 


if __name__ == '__main__':
    """
    The main entry point for running the plugin.
    """
    parser = argparse.ArgumentParser(
                            prog='PluginRunner',
                            description='Runs a pluigin')

    parser.add_argument('path')

    #adding an arguments  
    parser.add_argument('--kwargs',  nargs='*', action = keyvalue, default={}) 

    args = parser.parse_args()

    url='http://localhost/api/v3'
    uid='ingestor'
    password='aman'

    plugin_path = args.path

    try:
        host_services = ingestorservices.HostServices()
        host_services.bridge.signalLog.connect( print )
        host_services.login( url, uid, password )
    except requests.exceptions.ConnectionError as e:
        print('Failed to login')
        print(e)
    except Exception as e:
        print(type(e), e)

    host_services.log(args)

    host_services.load_plugins(paths=[plugin_path])

    for name, plugin in host_services.plugins.items():
        plugin.initialise( **args.kwargs )
        plugin.start()

    for name, plugin in host_services.plugins.items():
        plugin.join()