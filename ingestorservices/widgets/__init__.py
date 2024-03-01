import weakref
import functools
import types
import logging

logger = logging.getLogger(__name__)

from .. import core

from .bindings import pyside2


class Object:

    def __init__(self):

        self._signals = []

    def block_signals( self, boolean : bool ):
        for signal in self._signals:
            signal.block = boolean

    def register_signal( self ):

        signal = core.Signal()

        self._signals.append( signal )

        return signal


class Widget( Object ):

    @classmethod
    def create(cls, *args, **kwargs):
        w = cls( *args, **kwargs )
        w.initialise()
        return w

    def __init__(self ):

        super().__init__(  )
        self.layout = None

        #self._w = None

        self.f_SetEnabled = None
        self.f_SetLayout = None
        self.f_isEnabled = None

    def initialise( self ):
        return

        return self

    def setLayout( self, layout ):
        self.layout = layout

    def getLayout(self):
        return self.layout

    def isEnabled(self):
        return self.f_isEnabled()

    def setEnabled(self, val):
        self.f_SetEnabled( val )

    def moveEvent( self, *args, **kwargs ):
        print( 'WIDGETMOVE', self, args, kwargs )

        return True

    def mouseMoveEvent( self, *args, **kwargs ):
        print( 'WIDGETMOUSEMOVE', self, args, kwargs )

        return True

    def closeEvent( self, *args, **kwargs ):
        print('CLOSE')
        return True

    def keyPressEvent( self, *args, **kwargs ):
        print('KEYPRESS', self, args)
        return True



    #def eventFilter( self, *args, **kwargs ):
    #    print('filter', args, kwargs )

    #def closeEvent( self, *args, **kwargs ):

#class Frame(Widget):
#
#    @staticmethod
#    def create():
#        w = Frame()
#        w.initialise()
#        return w
#
#    def __init__(self):
#
#        super().__init__()
#
#
#        #w = QFrame()
#        #self._w = w
#
#
#        #_linkWidget( self, self._w )
#
#        #self.initialise( QFrame )
#    def initialise( self ):
#        w = QFrame()
#        self._w = w
#        return self


class Label(Widget):

    @staticmethod
    def create( label ):
        w = Label()
        w.initialise( label )
        return w

    def __init__(self):
        super().__init__()
        self.label = ""

        self._buddy = None

    def initialise( self, label ):

        self.label = label

        return self

    def setBuddy( self, w ):

        self._buddy = w

    def buddy(self):
        return self._buddy

    def clear(self):
        self.label = ""
        #self._w.clear()

    def text(self):
        return self.label

    def setText(self, s):
        self.label = s
        #self._w.setText(s)

    def moveEvent( self, *args, **kwargs ):
        print('LABELMOVE' )

class LineEdit(Widget):

    @staticmethod
    def create( *args, **kwargs):
        w = LineEdit()
        w.initialise()
        return w

    def __init__(self):
        super().__init__()

        self.textChanged = self.register_signal()
        self.returnPressed = self.register_signal()

        self.signalSetText = self.register_signal()

        self.f_getText = None

        #self.ei = EventInspector()
        #self._w.installEventFilter( self.ei )
        #self._bridge = LineEdit.Bridge()

    def initialise(self):
        #self._w = bindings.pyside6.createWidget( self )

        return self

    def setText(self, s):
        #self._bridge.signalSetText.emit( s )
        self.signalSetText.emit( s )

    def getText( self):
        print('#NNNNNNNNN')
        return self.f_getText()

class TextEdit( Widget ):
    @staticmethod
    def create( *args, **kwargs):
        w = TextEdit()
        w.initialise()
        return w

    def __init__(self):
        super().__init__()

        self.textChanged = self.register_signal()
        self.returnPressed = self.register_signal()

        self.signalSetText = self.register_signal()

        self.f_getText = None

    def initialise(self):
        return self

    def setText(self, s):
        self.signalSetText.emit( s )

    def getText( self):
        return self.f_getText()


#class ComboBox(Widget):
#    @staticmethod
#    def create( label ):
#        w =  ComboBox()
#        w.initialise(  )
#        return w
#
#    def __init__(self):
#
#        super().__init__( )
#
#        self.activated = self.register_signal()
#        self.currentIndexChanged = self.register_signal()
#
#
#    def initialise(self):
#        w = QComboBox()
#        self._w = w
#
#        #_linkWidget( self, self._w )
#
#        self._w.activated.connect( self.activated.emit )
#        self._w.currentIndexChanged.connect( self.currentIndexChanged.emit )
#        return self
#
#    def currentIndex(self):
#        return self._w.currentIndex()
#
#    def addItem(self, text, userData=None):
#        self._w.addItem( text, userData=userData)
#
#    def currentIndex(self):
#        return self._w.currentIndex()
#
#    def currentText(self):
#        return self.curentText()
#
#    def itemText(self, index):
#        return self._w.itemText(index)
#
#    def setItemText( self, index, text):
#        self._w.setItemText( index, text)
#
#    def setItemData( self, index, value ):
#        self._w.setItemData( index, value )
#
#    def removeItem(self, index):
#        self._w.removeItem(index)
#
#    def setCurrentIndex(self, index):
#        self._w.setCurrentIndex( index)
#
#    def setCurrentText(self, text):
#        self._w.setCurrentText(text)
#
#    def clear(self):
#        self._w.clear()

#class CheckBox(Widget):
#
#    @staticmethod
#    def create( label ):
#        w =  CheckBox()
#        w.initialise(  )
#        return w
#
#    def __init__(self, text):
#
#        super().__init__ ( )
#
#        #_linkWidget( self, self._w )
#
#        self.stateChanged = self.register_signal()
#
#    def initialise(self):
#        w = QCheckBox(text)
#        self._w = w
#
#        self._w.stateChanged.connect( self.stateChanged )
#
#        return self
#
#
#    def checkState(self):
#        return self._w.checkState()
#
#    def setCheckState(self, state ):
#        self.setCheckState( state )




class Layout:
    def __init__(self):
        self.items = []

    def addLayout(self, layout):
        self.items.append( layout )

    def addWidget( self, w ):
        self.items.append( w )

class PushButton(Widget):

    @staticmethod
    def create( label ):
        w =  PushButton()
        w.initialise( label )

        return w

    def __init__(self):

        super().__init__()

        self.clicked = self.register_signal()

    def initialise( self, label ):

        self.label = label

        return self

    #def setText(self, s):
    #    self._bridge.signalSetText( s )
    #    self._w.setText( s )


class VBoxLayout(Layout):
    def __init__(self):
        super().__init__()

class HBoxLayout(Layout):
    def __init__(self):
        super().__init__()





