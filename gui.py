"""
This module provides functionality for creating a GUI application for managing metadata plugins.

Classes:
    - LoginWidget: A widget for logging in and out of the application.
    - TextConsole: A widget for displaying console-like text output.
    - MainWindow: The main window of the application.

Functions:
    - getProxyModel: Returns a proxy model for a given model.
    - myprint: A function for printing output.
"""
import PySide2.QtCore as QtCore
#import PySide2.QtGui as QtGui
import PySide2.QtWidgets as QtWidgets

import os
import sys
#import json
import argparse
import logging
import traceback
import collections
import urllib.parse
import pathlib
import collections

import ingestorservices as services
import ingestorservices.widgets as widgets
import ingestorservices.properties as properties
import ingestorservices.core as core

import ingestorservices.widgets.bindings.pyside2 as bindings

logger = logging.getLogger( __name__ )
log_decorator = core.create_logger_decorator( logger )

#import jsonschema
#https://github.com/leixingyu/jsonEditor/blob/master/main.py
import linecache

def PrintException():
    """
    Prints and logs an exception with its traceback information.

    Used for informative error handling during program execution.
    """
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print( 'EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj))
    traceback.print_exc() 


ERR_NONE = 0

class LoginWidget( QtWidgets.QWidget ):
    """
    Login widget class for user authentication.

    Provides UI elements for entering username and password, and emits signals for login and logout actions.
    """
    def __init__(self, f_login, f_logout):
        """
        Constructor for the LoginWidget class.

        Args:
            f_login (callable): Callback function to handle login action.
            f_logout (callable): Callback function to handle logout action.
        """
        super().__init__()

        self._cbk_login = f_login
        self._cbk_logout = f_logout

        self.setupUI()

    @log_decorator
    def setupUI(self):
        """
        Sets up the user interface for the login widget.

        Creates and arranges UI elements like labels, input fields, and buttons.
        """
        self.user_edit = QtWidgets.QLineEdit()
        #self.user_label = QLabel('User')
        #self.user_label.setBuddy( self.user_edit )

        self.user_edit.textChanged.connect( self.slotOnUserKeyPress )

        self.pw_edit = QtWidgets.QLineEdit()
        self.pw_edit.setEchoMode( QtWidgets.QLineEdit.Password )
        #self.pw_label = QLabel('Password')
        #self.pw_label.setBuddy( self.pw_edit )

        self.pw_edit.textChanged.connect( self.slotOnPwKeyPress )

        layout = QtWidgets.QVBoxLayout() 
        form = QtWidgets.QFormLayout()

        #form.addRow( self.user_label, self.user_edit )
        form.addRow( 'User', self.user_edit )
        form.addRow( 'Password', self.pw_edit )

        hbox = QtWidgets.QHBoxLayout()
        btn_login = QtWidgets.QPushButton( 'Login'  )
        btn_logout = QtWidgets.QPushButton( 'Logout'  )

        btn_logout.setEnabled( False )
        btn_login.setEnabled( False )

        btn_login.clicked.connect( self.slotOnBtnLogin )
        btn_logout.clicked.connect( self.slotOnBtnLogout )

        hbox.addWidget( btn_logout )
        hbox.addWidget( btn_login )

        self.btn_login = btn_login
        self.btn_logout = btn_logout

        form.addRow( hbox )

        layout.addLayout( form )

        self.setLayout(layout)

    @log_decorator
    def slotOnUserKeyPress(self, *args):
        """
        Enables the login button when the user enters a username.

        Args:
            user (str): The username entered in the QLineEdit.
        """
        user = args[0]
        
        self.btn_login.setEnabled( len(user) )

    @log_decorator
    def slotOnPwKeyPress(self, *args):
        """
        Logs information about slotOnPwKeyPress being called with the provided arguments.

        Args:
            args (tuple): Arguments passed to the slot.
        """
        logging.info( 'slotOnPwKeyPress : %s' % args )

    @log_decorator
    def slotOnBtnLogin(self, *args):
        """
        Attempts to log in the user using the provided callback function.

        If successful, enables the logout button and disables the login button. Disables both input fields.
        Otherwise, the behavior is not specified in the current code.

        Args:
            args (tuple): Arguments passed to the slot (usually empty).
        """
        print(args)
        
        user = self.user_edit.text()
        pw = self.pw_edit.text()
        #scicat_host = self.scicat_server

        #SCICAT_HOST='SCICAT_HOST'

        #scicat_host = os.getenv( SCICAT_HOST, 'http://localhost' ) 

        #o = urllib.parse.urlsplit( scicat_host )

        #if not o.scheme:
        #    print('AAAAAAAAAAA')
        #    o = urllib.parse.urlsplit( scicat_host, scheme='http' )
        #    scicat_host = o.geturl()
        #    print(scicat_host )
        #else:
        #    print('BBBBBBBBB')
            
        #namedtuple to match the internal signature of urlunparse
        #UrlComponents = collections.namedtuple(
        #    typename='UrlComponents', 
        #    field_names=['scheme', 'netloc', 'path',  'query', 'fragment'])

        #c = UrlComponents(scheme=o.scheme, netloc=o.netloc,query='', path=o.path, fragment='')
        #url = urllib.parse.urlunsplit( c ) 

        #print(o)
        #print(c)
        #print(url)
        ##print(2, scicat_host )
        #url_root = urllib.parse.urljoin( scicat_host, 'api/v3' )
        url_root='badurl'
        res = self._cbk_login( user, pw )

        if ERR_NONE == res:
            self.btn_logout.setEnabled( True )
            self.btn_login.setEnabled( False )

            self.user_edit.setEnabled( False )
            self.pw_edit.setEnabled( False )

    @log_decorator
    def slotOnBtnLogout(self, *args):
        """
        Attempts to log out the user using the provided callback function.

        If successful, enables the login button and disables the logout button. Enables both input fields.
        Otherwise, the behavior is not specified in the current code.

        Args:
            args (tuple): Arguments passed to the slot (usually empty).
        """
        res = self._cbk_logout()

        self.btn_logout.setEnabled( False )
        self.btn_login.setEnabled( True )

        self.user_edit.setEnabled( True )
        self.pw_edit.setEnabled( True )



def getProxyModel( node ):
    """
    Creates and returns a proxy model for a given model.

    The created proxy model acts as an intermediary layer for filtering and sorting data from the original model.

    Args:
        node: The model node for which to create the proxy model.

    Returns:
        QtCore.QSortFilterProxyModel: The configured proxy model.
    """
    model = QJsonModel( node )

    # proxy model
    proxyModel = QtCore.QSortFilterProxyModel()
    proxyModel.setSourceModel( model )
    proxyModel.setDynamicSortFilter(False)
    proxyModel.setSortRole(QJsonModel.sortRole)
    proxyModel.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
    proxyModel.setFilterRole(QJsonModel.filterRole)
    proxyModel.setFilterKeyColumn(0)

    return proxyModel

def myprint( *args, **kwargs ):
    """
    Prints the provided arguments with formatting options.

    This function takes any number of positional and keyword arguments, and prints
    them using the `print` function along with specified keyword arguments.

    Args:
        *args (tuple): A tuple of positional arguments to be printed.
        **kwargs (dict): Keyword arguments used for formatting the output.
            See the documentation of the `print` function for supported keywords.

    Returns:
        None
    """
    print( *args )


class TextConsole( QtWidgets.QPlainTextEdit ):
    """
    **TextConsole class**

    This class provides a widget that displays text in a console-like format. It inherits from the `QPlainTextEdit` class of PySide2 and offers read-only functionality with a limited number of displayed lines.

    **Attributes:**

    * `max_lines` (int): The maximum number of lines to display in the text console.

    **Methods:**

    * `__init__(self)`: Initializes the `TextConsole` object.
    * `append(self, s)`: Appends a string `s` to the text console.
    """
    def __init__(self):
        """
        Initializes the `TextConsole` object.

        Sets the text console to read-only and establishes a maximum number of lines for display.
        """
        super().__init__()
        self.setReadOnly( True )
        self.max_lines = 100
    
        self.setMaximumBlockCount( self.max_lines )

    def append( self, s ):
        """
        Appends a string `s` to the text console.

        This method adds the provided string to the end of the displayed text, maintaining the maximum line limit.
        """
        self.appendPlainText( s )

# Subclass QMainWindow to customize your application's main window
class MainWindow(QtWidgets.QMainWindow):
    """
    The main window of the application, responsible for user interface elements
    and managing the interaction with IngestorServices framework.

    This class initializes the login widget, sets up the main UI layout, and
    handles communication with plugins and the SciCat server.
    """
    class QtBridge( QtCore.QObject ):
        """
        Internal class to bridge signals between the HostServices bridge
        and the main window for logging purposes.

        Emits a `signalLog` signal whenever a log message is received.
        """
        signalLog = QtCore.Signal(str)

        def __init__(self):
            super().__init__()

    @log_decorator
    def logoutSciCat(self):
        """Logs out of the SciCat server using the `HostServices` instance."""
        self.host_services.logout()

    @log_decorator
    def loginSciCat(self, username, password ):
        """
        Logs in to the SciCat server using the `HostServices` instance.

        Constructs the full URL using the provided server address and
        performs the login operation.

        Args:
            username (str): Username for login.
            password (str): Password for login.

        Returns:
            int: Result code from the login operation (0 for success).
        """
        #res = self.host_services.login(base_url,  username, password )
        scicat_host = self.scicat_server 

        url_root = self.scicat_server 

        if not url_root.endswith('/' ):
            url_root = url_root + '/'

        url = url_root + 'api/v3' 
        res = self.host_services.login( url,  username, password )

        return res

    def __init__(self, server='localhost'):
        """
        Constructor for the `MainWindow` class.

        Initializes essential attributes like `scicat_server`, `host_services`,
        and `qtbridge`, and starts/initializes all loaded plugins.

        Args:
            server (str, optional): SciCat server address (default: 'localhost').
        """
        super().__init__()

        self.scicat_server = server

        self.host_services = services.HostServices()

        self.qtbridge = MainWindow.QtBridge()
        
        #start the plugins. This needs to be done before the UI is created
        self.host_services.load_plugins()
        
        for name, plugin in self.host_services.plugins.items():
            plugin.initialise()

            plugin.start()

        self.setupUI()

    @log_decorator
    def closeEvent( self, *args, **kwargs ):
        """
        Stops all plugins before closing the window.
        """
        self.host_services.stop_plugins()
                
    @log_decorator
    def setupUI(self):
        """
        Sets up the main user interface layout for the application.
        """
        self.te = TextConsole()

        self.qtbridge.signalLog.connect( self.te.append )
        self.qtbridge.signalLog.connect( print )

        bridge = self.host_services.bridge

        self._fSignalLog = lambda s : self.qtbridge.signalLog.emit(s)
        bridge.signalLog.connect( self._fSignalLog )

        self.setWindowTitle("Example Ingestor App")

        login_widget = LoginWidget( self.loginSciCat, self.logoutSciCat)
        
        qtlayout = QtWidgets.QVBoxLayout()
        qtlayout.addWidget( login_widget )

        host_services = self.host_services
        try:

            for name, plugin in host_services.plugins.items():

                try:
                    widget = plugin.widget()
                    qtwidget = bindings.createWidget( widget )

                    qtlayout.addWidget( qtwidget )
                except Exception as e:
                    print(name)

                    try:
                        l0 = widgets.VBoxLayout()

                        label = widgets.Label.create( name )
                        l0.addWidget( label )

                        pg = plugin.property_group()
                        l =  services._property_group_2_layout( pg )
                        l0.addLayout( l )


                        w = widgets.Widget.create()
                        w.setLayout( l0 )

                        qtw = bindings.createWidget( w )

                        qtlayout.addWidget( qtw )
                    except Exception as e:
                        print(e)
                        pass
                    
                if plugin:
                    plugin.log( 'Started %s' % plugin )

        except Exception as e:
            print(e)
            PrintException()

        qtlayout.addWidget( self.te )

        qtcontainer = QtWidgets.QWidget()
        qtcontainer.setLayout(qtlayout)

        self.setCentralWidget(qtcontainer)

if __name__ == '__main__':

    ENV_LOG_LVL = 'LOG_LEVEL'

    LOG_LVL_NONE = 'NONE'
    LOG_LVL_NOTSET = 'NOTSET'
    LOG_LVL_INFO = 'INFO'
    LOG_LVL_DEBUG = 'DEBUG'
    LOG_LVL_WARN = 'WARN'
    LOG_LVL_ERROR = 'ERROR'
    LOG_LVL_CRITICAL = 'CRITICAL'

    log_lvl_map = {}
    log_lvl_map[ LOG_LVL_NOTSET ] = logging.NOTSET
    log_lvl_map[ LOG_LVL_INFO ] = logging.INFO
    log_lvl_map[ LOG_LVL_DEBUG ] = logging.DEBUG
    log_lvl_map[ LOG_LVL_WARN ] = logging.WARN
    log_lvl_map[ LOG_LVL_CRITICAL ] = logging.CRITICAL
    log_lvl_map[ LOG_LVL_ERROR ] = logging.ERROR

    app_log_lvl = os.getenv( ENV_LOG_LVL, LOG_LVL_NONE )


    parser = argparse.ArgumentParser(
        prog='MetadataHost',
        description='Metadata plugin host')

    parser.add_argument('--host', default='localhost')

    args = parser.parse_args()

    try:
        """
        Sets up logging configuration based on the specified log level.
        """
        log_lvl = log_lvl_map[ app_log_lvl ]
        logging.basicConfig( level=log_lvl )
    except Exception as e:
        logging.disable( logging.CRITICAL )


    app = QtWidgets.QApplication( sys.argv )

    window = MainWindow( args.host)
                                               
    window.show()
    app.exec_()
