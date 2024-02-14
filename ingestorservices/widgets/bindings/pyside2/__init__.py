from .... import widgets

import PySide2.QtCore as QtCore
from PySide2.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout, QComboBox, QTreeView, QSizePolicy, QTextEdit, QListWidget, QButtonGroup, QDialogButtonBox, QFrame

#class QLineEdit_(QLineEdit):
#
#    class Bridge( QtCore.QObject ):
#        signalSetText = QtCore.Signal(str)
#
#    def __init__(self):
#        super().__init__()
#
#        self._bridge = QLineEdit_.Bridge()
#
#        self._bridge.signalSetText.connect( self.setText )

class EventInspector( QtCore.QObject ):

    def __init__(self):
        super().__init__()
    def eventFilter( self, obj, event ):
        #print( 'eventfilter', obj, event )
        return super().eventFilter( obj, event )

class QWidget_(QWidget):
    def __init__(self):
        super().__init__()

class QLabel_( QLabel ):
    def __init__(self, s):
        super().__init__(s)

class QLineEdit_(QLineEdit):

    class Bridge( QtCore.QObject ):
        signalSetText = QtCore.Signal(str)
        signalTextChanged = QtCore.Signal(str)

        def slotSetText( self, s ):
            self.signalSetText.emit( s )

        def slotTextChanged( self, *args ):
            self.signalTextChanged.emit( *args )
            print('Brigdge text changed')

        

    def __init__(self):
        super().__init__()

        self._bridge = QLineEdit_.Bridge()

        self._bridge.signalSetText.connect( self.setText )

        #self.textChanged.connect( self.textChanged.emit )

class QPushButton_( QPushButton ):

    def __init__(self, label):
        super().__init__(label)



def createLayout( layout ):

    qtl = QHBoxLayout() if isinstance( layout, widgets.HBoxLayout ) else QVBoxLayout() 

    for item in layout.items:
        if isinstance( item, widgets.Widget ):
            qtw = createWidget( item )
            qtl.addWidget( qtw )
        elif isinstance( item, widgets.Layout ):
            qtl2 = createLayout( item )
            qtl.addLayout( qtl2 )

    return qtl


def createWidget( w ) -> QWidget:

    qt_widget = None

    if 0 and (isinstance( w, widgets.HBoxLayout) or isinstance( w, widgets.VBoxLayout)):
        if isinstance( w, widgets.HBoxLayout):
            qt_layout = QHBoxLayout()
        else:
            qt_layout = QVBoxLayout()

    elif isinstance( w, widgets.LineEdit ):

        qt_widget = QLineEdit_()
        w.signalSetText.connect( qt_widget._bridge.signalSetText.emit )

        qt_widget.textChanged.connect( w.textChanged.emit )
        #self._w.returnPressed.connect( self.returnPressed.emit )
        #self._bridge.signalSetText.connect( self._w.setText )
        w.signalSetText.connect( qt_widget._bridge.slotSetText )
        #self.signalSetText2.connect( self._w._bridge.signalSetText.emit )

        w.f_getText = lambda : qt_widget.text()

    elif isinstance( w, widgets.Label ):
        label = w.label
        qt_widget = QLabel( label )
    elif isinstance( w, widgets.PushButton ):
        print(w.label )
        qt_widget = QPushButton_( w.label)
        qt_widget.clicked.connect( w.clicked.emit )
    elif isinstance( w, widgets.Widget ):

        qt_widget = QWidget_()

        layout = w.getLayout()
        if layout:
            qt_layout = createLayout( layout )

            qt_widget.setLayout( qt_layout )

    else:
        print( 'Unrecognised' , w)

    if qt_widget:
        w.f_SetEnabled = lambda bVal : qt_widget.setEnabled( bVal )
        w.f_isEnabled = lambda : qt_widget.isEnabled()
        w.f_SetLayout = lambda layout : qt_widget.setLayout( layout._layout )

        qt_widget._internal_widget = w

    return qt_widget


