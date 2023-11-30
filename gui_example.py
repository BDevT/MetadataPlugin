import PySide6.QtCore as QtCore
#import PySide6.QtGui as QtGui
import PySide6.QtWidgets as QtWidgets

import os
import sys
#import json
import logging
import traceback
import collections

import ingestorservices as services
import ingestorservices.widgets as widgets
import ingestorservices.properties as properties
import ingestorservices.core as core

logger = logging.getLogger( __name__ )
log_decorator = core.create_logger_decorator( logger )

#import jsonschema
#https://github.com/leixingyu/jsonEditor/blob/master/main.py
import linecache

def PrintException():
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

    def __init__(self, f_login, f_logout):

        super().__init__()

        self._cbk_login = f_login
        self._cbk_logout = f_logout

        self.setupUI()

    @log_decorator
    def setupUI(self):

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
        user = args[0]
        
        self.btn_login.setEnabled( len(user) )

    @log_decorator
    def slotOnPwKeyPress(self, *args):
        logging.info( 'slotOnPwKeyPress : %s' % args )

    @log_decorator
    def slotOnBtnLogin(self, *args):
        
        user = self.user_edit.text()
        pw = self.pw_edit.text()

        url_root = 'http://localhost/api/v3'
        res = self._cbk_login( url_root, user, pw )

        if ERR_NONE == res:
            self.btn_logout.setEnabled( True )
            self.btn_login.setEnabled( False )

            self.user_edit.setEnabled( False )
            self.pw_edit.setEnabled( False )

    @log_decorator
    def slotOnBtnLogout(self, *args):

        res = self._cbk_logout()

        self.btn_logout.setEnabled( False )
        self.btn_login.setEnabled( True )

        self.user_edit.setEnabled( True )
        self.pw_edit.setEnabled( True )



def getProxyModel( node ):

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




class TextConsole( QtWidgets.QPlainTextEdit ):
    def __init__(self):
        super().__init__()
        self.setReadOnly( True )
        self.max_lines = 100
    
        self.setMaximumBlockCount( self.max_lines )

    def append( self, s ):

        self.appendPlainText( s )

# Subclass QMainWindow to customize your application's main window
class MainWindow(QtWidgets.QMainWindow):

    class QtBridge( QtCore.QObject ):
        signalLog = QtCore.Signal(str)

        def __init__(self):
            super().__init__()

    @log_decorator
    def logoutSciCat(self):
        self.host_services.logout()

    @log_decorator
    def loginSciCat(self, base_url, username, password ):
        res = self.host_services.login(base_url,  username, password )
        return res
        

    def __init__(self):
        super().__init__()

        self.host_services = services.HostServices( self )

        self.qtbridge = MainWindow.QtBridge()
        
        #start the plugins. This needs to be done before the UI is created
        self.host_services.start()

        self.setupUI()

    @log_decorator
    def closeEvent( self, *args, **kwargs ):
        self.host_services.finish()
                
    @log_decorator
    def setupUI(self):

        self.te = TextConsole()

        self.qtbridge.signalLog.connect( self.te.append )
        self.qtbridge.signalLog.connect( print )

        bridge = self.host_services.bridge

        self._fSignalLog = lambda s : self.qtbridge.signalLog.emit(s)
        bridge.signalLog.connect( self._fSignalLog )

        self.setWindowTitle("Example Ingestor App")

        login_widget = LoginWidget( self.loginSciCat, self.logoutSciCat)
        
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget( login_widget )

        host_services = self.host_services

        #host servoices starts the plugins.
        #Now see which plugins have a UI.
        try:

            for name, plugin in host_services.plugins.items():

                try:
                    widget = plugin.widget()
                    qtwidget = widget.internal_widget()

                    layout.addWidget( qtwidget )
                except Exception as e:

                    try:
                        l0 = widgets.VBoxLayout()

                        label = widgets.Label.create( name )
                        l0.addWidget( label )

                        pg = plugin.property_group()

                        l =  services._property_group_2_layout( pg )

                        l0.addLayout( l )
                        w = widgets.Widget.create()
                        w.setLayout( l0 )
                        qtw = w.internal_widget()

                        layout.addWidget( qtw )
                    except:
                        pass
                    
                if plugin:
                    self.host_services.log( 'Started %s' % plugin )

        except Exception as e:
            print(e)
            PrintException()

        layout.addWidget( self.te )

        container = QtWidgets.QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)



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


    try:
        log_lvl = log_lvl_map[ app_log_lvl ]
        logging.basicConfig( level=log_lvl )
    except Exception as e:
        logging.disable( logging.CRITICAL )


    app = QtWidgets.QApplication( sys.argv )

    window = MainWindow()
                                               
    window.show()
    app.exec()
