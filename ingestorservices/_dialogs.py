import numbers

from functools import partial

from . import properties

from . widgets import Widget, Label, LineEdit, PushButton, HBoxLayout, VBoxLayout


def _on_widget_change( e, p, *args, **kwargs ):
    
    #print('WIDGET CHANGE', p.name, args, kwargs )
    if isinstance( p, properties.ButtonProperty ):
        #print( 'DO SOMETHING WITH BUTTON')
        p.sig_changed.emit()
        pass
    elif isinstance( p, properties.ChoiceProperty ):
        p.choice = args[0]
    else:
        _type_ = type(p._value)
        p.value = _type_( args[0] )



 
        

def _on_property_change_update_widget( p, e, *args, **kwargs ):
    #print('on_property_change',p.name)

    if isinstance(p, properties.ButtonProperty ):
        pass

    elif isinstance( p, properties.ChoiceProperty):
        print(p, p.choice, p.choices[ p.choice ] )
        #pass
    elif isinstance( p, properties.Property):

        if (isinstance( p.value, str) or isinstance( p.value, numbers.Number ) )and not isinstance(p.value, bool):# p.type == Type.Number:
            e.setText( str(p.value) )

            #e.textChanged.emit( str(p.value) )
        elif isinstance( p.value, bool ):# p.type == Type.Boolean:
            e.setCheckState(  PySide6.QtCore.Qt.CheckState.Checked if p.value else  PySide6.QtCore.Qt.CheckState.Unchecked )


       


#class _DialogBase(QDialog):
#    def __init__(self, services):
#        super().__init__()
#        self._services = services
#
#    def initialise(self):
#        return
#
#    @property
#    def services(self):
#        return self._services
#
#    def update(self, w, *args, **kwargs):
#        return

#class UserDialog( _DialogBase ):
#    def __init__(self, services):
#
#        super().__init__( services )
#        print('USER DLG __INIT__')
#        return 
def _property_group_2_layout( grp ):

    if grp.layout == properties.PropertyGroup.HORIZONTAL:
        g = HBoxLayout()
    else:
        g = VBoxLayout()

    ps = grp.propertys
    for i,x in enumerate(ps):
        w = None

        if isinstance( x, properties.PropertyGroup ):
            pass
            w = _property_group_2_layout( x )
        else:
            w = _property_2_layout( x )
        
        g.addLayout( w )

    return g

   
def _property_2_layout( p ):

    hbox = HBoxLayout()

    if isinstance( p, properties.ButtonProperty ):
        e = PushButton.create(p.name)
        f = partial( _on_widget_change, e, p)
        e.clicked.connect( f )
        e.f_clicked = f

        f = partial( _on_property_change_update_widget, p, e )
        p.f = f
        p.sig_changed.connect( f )

    else:

        label = Label.create( p.name )
        hbox.addWidget( label )
        e = None

        if isinstance( p, properties.ChoiceProperty ):

            e = ComboBox.create( 'combo' )
            print('44444', e )

            for c in p.choices:
                print( c )
                e.addItem( c )
                #e.insertItems( 0, p.choices )
            f = partial( _on_widget_change, e, p)
            e.setCurrentIndex( p.choice )
            e.currentIndexChanged.connect( f )

            f = partial( _on_property_change_update_widget, p, e )
            p.f = f
            p.sig_changed.connect( f )

        if isinstance( p, properties.Property ):
            if isinstance( p.value, str ):
                e = LineEdit.create()
                e.setText( p.value )
                #e = LineEdit( p.value )
                f = partial( _on_widget_change, e, p)
                p._on_widget_change = f
                e.textChanged.connect( f )

                f = partial( _on_property_change_update_widget, p, e )
                p._on_property_change_update_widget = f
                p.sig_changed.connect( f )

            elif isinstance( p.value, numbers.Number ) and not isinstance(p.value, bool):

                #if isinstance( p.value, numbers.Integral):
                #    v = QIntValidator()
                #else:
                #    v = QDoubleValidator()

                #e = LineEdit( str(p.value) )
                e = LineEdit.create()
                e.setText( str(p.value) )
                #e.setValidator( v )

                f = partial( _on_widget_change, e, p)
                p._on_widget_change = f
                e.textChanged.connect( f )

                f = partial( _on_property_change_update_widget, p, e )
                p._on_property_change_update_widget = f
                p.sig_changed.connect( f )

            elif isinstance( p.value, bool ):
                e = CheckBox( p.name )
                e.setCheckState( PySide6.QtCore.Qt.CheckState.Checked if p.value else PySide6.QtCore.Qt.CheckState.Unchecked )

                f = partial( _on_widget_change, e, p)
                e.stateChanged.connect( f )

            elif isinstance( p.value, list ):
                e = ComboBox()
                e.insertItems( 0, p.value )
                f = partial( _on_widget_change, e )
                e.currentIndexChanged.connect( f )

                f = partial( _on_property_change_update_widget, p, e )
                p.sig_changed.connect( f )

        #if e:
        #    if p.direction == Direction.Out:
        #        e.setReadOnly( True )
        #        e.setEnabled(False)

    if e:
        hbox.addWidget( e )

    #w.setLayout( hbox )

    return hbox





