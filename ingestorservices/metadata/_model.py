import pyscicat

class Base:

    def __init__( self, scicat_model):
        self._scicat_model = scicat_model

    def __getattr__(self, name ):

        return getattr( self._scicat_model, name )

    def dict(self):
        return self._scicat_model.dict()


class Ownable(Base):

    def __init__(self, *args, **kwargs):
        super().__init__(pyscicat.model.Ownable( **kwargs ))


class Dataset(Base):

    def __init__(self, *args, **kwargs):
        super().__init__(pyscicat.model.Dataset( **kwargs ))
