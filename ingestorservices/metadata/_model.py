import pyscicat

class Base:

    def __init__( self, scicat_model):
        self._scicat_model = scicat_model

    def __getattr__(self, name ):

        return getattr( self._scicat_model, name )

    def dict(self,exclude_none=True):
        return self._scicat_model.dict(exclude_none=exclude_none)


class Ownable(Base):

    def __init__(self, *args, **kwargs):
        super().__init__(pyscicat.model.Ownable( **kwargs ))


class Dataset(Base):

    def __init__(self, *args, **kwargs):
        super().__init__(pyscicat.model.RawDataset( **kwargs ))
