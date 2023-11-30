import weakref
import functools
import types
import logging

logger = logging.getLogger(__name__)

import PySide6.QtCore as QtCore
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout, QComboBox, QTreeView, QSizePolicy, QTextEdit, QListWidget, QButtonGroup, QDialogButtonBox, QFrame

from .. import core


class EventInspector( QtCore.QObject ):

    def __init__(self):
        super().__init__()
    def eventFilter( self, obj, event ):
        #print( 'eventfilter', obj, event )
        return super().eventFilter( obj, event )


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


def qtcreateWidget( c, *args, **kwargs ) -> QWidget:
    w = c( *args, **kwargs )
    return w

def _linkWidget( w, qtw ):

    def mouseMoveEvent( self, evt ):

        res = w.mouseMoveEvent()

        #if res:
        #    evt.accept()


    def moveEvent( self, evt ):

        res = w.moveEvent()
        #if res:
        #    evt.accept()

    def closeEvent( self, evt ):

        res = w.closeEvent()
        #if res:
        #    evt.accept()

    def keyPressEvent( self, evt ):

        res = w.keyPressEvent()
        evt.ignore()
        #if res:
        #    evt.accept()



    qtw.closeEvent = types.MethodType( closeEvent, qtw )
    qtw.mouseMoveEvent = types.MethodType( mouseMoveEvent, qtw )
    qtw.moveEvent = types.MethodType( moveEvent, qtw )
    qtw.keyPressEvent = types.MethodType( keyPressEvent, qtw )


    return 


#class _QWidget( QWidget ):
#    def __init__(self):
#        super().__init__()


class Widget( Object ):


#class Widget( Widgetbase ):

    @classmethod
    def create(cls, *args, **kwargs):
        w = cls( *args, **kwargs )
        w.initialise()
        return w

    def __init__(self ):

        super().__init__(  )

        self._w = None

    def internal_widget(self):
        return self._w

        #_linkWidget( self, self._w )

    def initialise( self ):
        w = QWidget()
        self._w = w

        #_linkWidget( self, self._w )
        return self

    def setEnable( self, val ):
        self._w.setEnable( val )

    def setLayout( self, layout ):
        self._w.setLayout( layout._layout )

    def isEnabled(self):
        return self._w.isEnabled()

    def setEnabled(self, val):
        self._w.setEnabled(val)

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

class Frame(Widget):

    @staticmethod
    def create():
        w = Frame()
        w.initialise()
        return w

    def __init__(self):

        super().__init__()


        #w = QFrame()
        #self._w = w


        #_linkWidget( self, self._w )

        #self.initialise( QFrame )
    def initialise( self ):
        w = QFrame()
        self._w = w
        return self


class Label(Widget):

    @staticmethod
    def create( label ):
        w = Label()
        w.initialise( label )
        return w

    def __init__(self):
        super().__init__()

        self._buddy = None

        #_linkWidget( self, self._w )

    def initialise( self, label ):

        w = QLabel( label )
        self._w = w
        return self

    def setBuddy( self, w ):

        self._buddy = w
        self._w.setBuddy( w._w )

    def buddy(self):
        return self._buddy

    def clear(self):
        self._w.clear()

    def text(self):
        return self._w.text()

    def setText(self, s):
        self._w.setText(s)

    def moveEvent( self, *args, **kwargs ):
        print('LABELMOVE' )


class LineEdit(Widget):

    class Bridge( QtCore.QObject ):
        signalSetText = QtCore.Signal(str)

    @staticmethod
    def create():
        w = LineEdit()
        w.initialise()
        return w

    def __init__(self):
        super().__init__()

        self.textChanged = self.register_signal()
        self.returnPressed = self.register_signal()

        self.ei = EventInspector()
        #self._w.installEventFilter( self.ei )
        self._bridge = LineEdit.Bridge()

    def initialise(self):
        self._w = QLineEdit()
        self._w.textChanged.connect( self.textChanged.emit )
        self._w.returnPressed.connect( self.returnPressed.emit )

        self._bridge.signalSetText.connect( self._w.setText )
        return self

    def setText(self, s):
        self._bridge.signalSetText.emit( s )

    def getText( self):
        return self._w.text()

class ComboBox(Widget):
    @staticmethod
    def create( label ):
        w =  ComboBox()
        w.initialise(  )
        return w

    def __init__(self):

        super().__init__( )

        self.activated = self.register_signal()
        self.currentIndexChanged = self.register_signal()


    def initialise(self):
        w = QComboBox()
        self._w = w

        #_linkWidget( self, self._w )

        self._w.activated.connect( self.activated.emit )
        self._w.currentIndexChanged.connect( self.currentIndexChanged.emit )
        return self

    def currentIndex(self):
        return self._w.currentIndex()

    def addItem(self, text, userData=None):
        self._w.addItem( text, userData=userData)

    def currentIndex(self):
        return self._w.currentIndex()

    def currentText(self):
        return self.curentText()

    def itemText(self, index):
        return self._w.itemText(index)

    def setItemText( self, index, text):
        self._w.setItemText( index, text)

    def setItemData( self, index, value ):
        self._w.setItemData( index, value )

    def removeItem(self, index):
        self._w.removeItem(index)

    def setCurrentIndex(self, index):
        self._w.setCurrentIndex( index)

    def setCurrentText(self, text):
        self._w.setCurrentText(text)

    def clear(self):
        self._w.clear()

class CheckBox(Widget):

    @staticmethod
    def create( label ):
        w =  CheckBox()
        w.initialise(  )
        return w

    def __init__(self, text):

        super().__init__ ( )

        #_linkWidget( self, self._w )

        self.stateChanged = self.register_signal()

    def initialise(self):
        w = QCheckBox(text)
        self._w = w

        self._w.stateChanged.connect( self.stateChanged )

        return self


    def checkState(self):
        return self._w.checkState()

    def setCheckState(self, state ):
        self.setCheckState( state )




class Layout:
    def __init__(self):
        self._layout = None

        self.widgets = []
        self.layouts = []

    def addLayout(self, layout):
        self._layout.addLayout( layout._layout )
        self.layouts.append( layout )

    def addWidget( self, w ):

        self._layout.addWidget( w._w )
        self.widgets.append( w )

#class _QPushButton( QPushButton ):
#    def __init__(self, label):
#        super().__init__(label)

class PushButton(Widget):

    class Bridge( QtCore.QObject ):
        signalSetText = QtCore.Signal(str)


    @staticmethod
    def create( label ):
        w =  PushButton()
        w.initialise( label )

        return w

    def __init__(self):

        super().__init__()

        self.clicked = self.register_signal()

    def initialise( self, label ):
        self._bridge = PushButton.Bridge()

        #self._bridge.signalSetText.connect( self._w.setText )

        w = QPushButton( label)
        self._w = w

        self._w.clicked.connect( self.clicked.emit )
        return self

    #def setText(self, s):
    #    self._bridge.signalSetText( s )
    #    #self._w.setText( s )


class VBoxLayout(Layout):
    def __init__(self):
        super().__init__()
        self._layout = QVBoxLayout()

class HBoxLayout(Layout):
    def __init__(self):
        super().__init__()
        self._layout = QHBoxLayout()





