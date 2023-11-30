
from pyscicat.client import encode_thumbnail, ScicatClient

from typing import Optional

from . _filters import Property, _where_, _and_, _or_
import json

class MyMetadataClient( ScicatClient ):
    """Responsible for communicating with the Scicat Catamel server via http"""

    def __init__(
            self,
            base_url: str,
            token: str = False,
            username: str = None,
            password: str = None,
            timeout_seconds: int = None,
            ):

        super().__init__( base_url, token, username, password, timeout_seconds )

    #https://loopback.io/doc/en/lb3/Where-filter.html
    def samples_query( self, *args ):
        query = {}

        query.update( _where_( *args ) )

        j_query = json.dumps( query )

        endpoint = f"Samples?filter={j_query}"

        res = self._call_endpoint( cmd="get"
                , endpoint=endpoint, operation="Samples", allow_404=True )

        return res


    def samples_get( self, like_sampleId ) -> Optional[dict] :

        sampleId = Property('sampleId')

        res = self.samples_query( sampleId.like( like_sampleId ) )

        return res

    def dataset_query( self, *args ):
        query = {}

        query.update( _where_( *args ) )

        j_query = json.dumps( query )

        endpoint = f"Datasets?filter={j_query}"

        res = self._call_endpoint( cmd="get"
                , endpoint=endpoint, operation="Datasets", allow_404=True )

        return res



