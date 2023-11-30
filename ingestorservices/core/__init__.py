
import collections
import logging

logger = logging.getLogger( __name__ )

from . _signal import Signal

def create_logger_decorator( logger ):
    def log_function( fn ):
        def wrapper( *args, **kwargs):

            logger.debug( '%s( %s, %s : START' % (fn.__name__, args, kwargs) )

            out = fn( *args, **kwargs )

            logger.debug( '%s( %s, %s : END' % (fn.__name__, args, kwargs) )

            return out

        return wrapper
    return log_function


def TypeList(item_type : type):
    class _TypeList(collections.UserList):
        def __init__(self, initial_data=None):
            super().__init__(initial_data if initial_data else [])
            self.item_type = item_type

            if not all(isinstance(item, item_type) for item in self.data):
                raise TypeError(f"Initial data must be of type {item_type.__name__}")

            def append(self, value):
                if isinstance(value, self.item_type):
                    super().append(value)
                else:
                    raise TypeError(f"Only {self.item_type.__name__} is allowed in this list.")

    return _TypeList
       
def TypeDict( key_type : type, value_type : type ):
    class _TypeDict(collections.UserDict):
        def __init__(self, initial_data=None):
            super().__init__(initial_data if initial_data else {})
            self.key_type = key_type
            self.value_type = value_type

            if not all(isinstance(key, key_type) and isinstance(value, value_type) for key, value in self.data.items()):
                raise TypeError(f"Initial data must have keys of type {key_type.__name__} "
                                f"and values of type {value_type.__name__}")

        def __setitem__(self, key, value):
            self._validate_type(key, value)
            super().__setitem__(key, value)

        def _validate_type(self, key, value):
            if not isinstance(key, self.key_type) or not isinstance(value, self.value_type):
                raise TypeError(f"Keys must be of type {self.key_type.__name__}, "
                                f"and values must be of type {self.value_type.__name__}")

    return _TypeDict

class RWDict( collections.UserDict ):
    pass

class RODict(collections.UserDict):
         
    # Function to stop deletion
    # from dictionary
    def __del__(self):
        raise RuntimeError("Deletion not allowed")

    # Function to stop pop from 
    # dictionary
    def pop(self, s = None):
        raise RuntimeError("Deletion not allowed")

    # Function to stop popitem 
    # from Dictionary
    def popitem(self, s = None):
        raise RuntimeError("Deletion not allowed")




