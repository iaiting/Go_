import socket
import sys
from thread import *
import time
import Queue
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from socketwraper import SocketWrapper
from socketwraper import SocketWrapperSingleton
from lobby import *
from socket_utils import *
from instructions import InstructionsScreen
from kivy.lang import Builder
Builder.load_file('lobby.kv')
Builder.load_file('instructions.kv')
Builder.load_file('go.kv')

class MyScreenManager(ScreenManager):
    '''
    The screen Manager. Responsible for switching between screens, represented by widgets, in the application. extends the default ScreenManager provided by Kivy.
    '''
    def __init__(self, **kwargs):

        super(MyScreenManager, self).__init__(**kwargs)

        # def on_current(self, instance, value):
        #     super(MyScreenManager, self).on_current(instance, value)
        #     #print "child on_current!!!!!!@@@!!@"
        #     screen = self.get_screen(value)
        #     if not screen:
        #         return
        #     if screen == self.current_screen:
        #         return
        #
        #     self.transition.stop()
        #
        #     previous_screen = self.current_screen
        #     self.current_screen = screen
        #     self.current_screen.on_transition_in()
        #     if previous_screen:
        #         self.transition.screen_in = screen
        #         self.transition.screen_out = previous_screen
        #         self.transition.start(self)
        #         previous_screen.on_transition_out()
        #     else:
        #         self.real_add_widget(screen)
        #         screen.pos = self.pos
        #         self.do_layout()
        #         screen.dispatch('on_pre_enter')
        #         screen.dispatch('on_enter')


class LoginScreen(Screen):
    '''
    A widget representing the login screen. enables the user to login to his Go account, or view instructions for the game.
    '''
    username_input = ObjectProperty("hello")

    def __init__(self, **kwargs):
        '''
        Constructor
        :param kwargs:
        '''
        """
        @type server_handler SocketWrapper
        """
        super(LoginScreen, self).__init__(**kwargs)
        # self.server_handler = server_handler
        self.username_callback = kwargs['username_callback']

    def on_transition_in(self):
        '''
        Called when login screen is visible
        :return:
        '''
        print "main in"
    def on_transition_out(self):
        '''
        Called when login screen is no longer visible
        :return:
        '''
        print "main out"

    def goto_lobby(self):
        '''
        switches to lobby screen using the ScreenManager
        :return:
        '''
        #print "switching to lobby, username:" , self.username_input.text
        self.username_callback(self.username_input.text) # to update window title to username
        # callback
        def on_response(response):
            '''
            Callback from server, called with response from server for user's login attempt
            :param response: dictinoary with response info
            :return:
            '''
            print "received request response:", response
            if response['status'] == "OK":
                self.manager.current = "lobbyScreen"


        # self.server_handler.request_response("#login#username" + self.username_input.text,"#login", on_response)
        # self.server_handler.request_response(SocketUtils.incode_request({'prefix':'login', 'username':self.username_input.text}), 'login', on_response)
        SocketWrapperSingleton.get().request_response(SocketUtils.incode_request({'prefix':'login', 'username':self.username_input.text}), 'login', on_response)
        print "send request response for server"

    def goto_instructions(self):
        '''
        switches to instructions screen using ScreenManager
        :return:
        '''
        print "goto instructions"
        self.manager.current = "instructionsScreen"

class MainApp(App):
    '''
    The main Application class
    '''
    def build(self):
        '''
        builds and returns the main application widget
        :return: The screenManager, will show the current screen at any given moment
        '''
        # return LobbyWidget()

        my_screenmanager = ScreenManager()
        loginScreen = LoginScreen(username_callback = self.on_username , name = "loginScreen")
        lobbyScreen = LobbyScreen(name='lobbyScreen')
        # goScreen = GoScreen(name='goScreen')

        # def win_cb(window, width, height):
        #     if(my_screenmanager.current == "goScreen"):
        #         goScreen.game.handleWindowResize()
        #
        # Window.bind(on_resize=win_cb)

        my_screenmanager.add_widget(loginScreen)
        my_screenmanager.add_widget(lobbyScreen)
        my_screenmanager.add_widget(InstructionsScreen(name = "instructionsScreen"))

        # my_screenmanager.add_widget(goScreen)
        return my_screenmanager

    def on_username(self, username):
        '''
        called when user enters his/hers username. updates user's username in Sever's wrapper singleton.
        :param username:
        :return:
        '''
        SocketWrapperSingleton.get().username = username
        self.title = str(username)


# connect to server
IP = '127.0.0.1'
PORT = 8888
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.connect((IP, PORT))
SocketWrapperSingleton.get(server_socket) #init singleton
if __name__ == "__main__":
    MainApp().run()