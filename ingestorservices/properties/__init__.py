import logging

logger = logging.getLogger(__name__)

from . _property import PropertyGroup
from . _property import Property, ChoiceProperty, ButtonProperty, BoxProperty, PropertyBase
from .. import core

PropertyDict = core.TypeDict( str, PropertyBase )


class PropertyContainer:
    def __init__(self):
        super().__init__()
        self._properties = PropertyDict()

    @property
    def properties(self):
        return self._properties
