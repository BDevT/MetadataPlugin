class Property:
    def __init__(self, name):
        self.name = name

    def gt( self, value ):
        return { self.name : {'gt' : value} }

    def gte( self, value ):
        return {self.name:{'gte' : value} }

    def lt( self, value ):
        return {self.name:{'lt' : value} }

    def lte( self, value ):
        return {self.name:{'lte' : value} }

    def ne(self, value):
        return {self.name:{'ne' : value}}

    def eq(self, value):
        return {self.name:{'eq' : value}}

    def inq(self, *args):
        return {self.name:{'inq' : list(args) }}

    def like( self, value ):
        return { self.name : {'like' : value} }


def _and_( *args ):
    s = [ x for x in args ]
    return { 'and' : s }

def _or_( *args ):
    s = [ x for x in args ]
    return { 'or' : s }

def _where_( *args ):

    w = {}
    for arg in args:
        w.update( arg )

    return {'where' : w}



