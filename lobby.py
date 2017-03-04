from kivy.adapters.listadapter import ListAdapter
from kivy.app import App
from kivy.app import Widget
from kivy.core.window import Window
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.listview import ListItemButton
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.textinput import TextInput

from socketwraper import *
from socket_utils import *
from Go import *

class MyListAdapter(ListAdapter):
    '''
    List adapcter for list of pending games & live games. resposible for deciding the data to present in the list & handling list items clicks
    '''
    def __init__(self, **kwargs):
        '''
        Construcotr
        :param kwargs:
        '''
        self.listview_id = kwargs['listview_id']
        super(MyListAdapter, self).__init__(**kwargs)
        self.parent_class = kwargs['parent_class']


    def on_selection_change(self, *args):
        '''
        Called when a list item is selected
        :param args:
        :return:
        '''
        if(len(self.selection) > 0):
            print "list click:" , self.selection[0].text
            self.parent_class.handleListSelection(self.selection[0].text)
            self.parent_class.handleMatchAccepted(self.selection[0].text) # pass opponent name as parameter
        # for i in range(len(self.selection)):
        #         print self.selection[i].text
        # print "AA"


class LobbyScreen(Screen):
    '''
    A widget for the lobby Screen. Controlled by the ScreenManager
    '''
    players_list = ObjectProperty()

    LIST_MODES = {'available_matches':1, 'watch_matches':2}

    def __init__(self, **kwargs):
        '''
        Constructor
        :param kwargs:
        '''
        super(LobbyScreen, self).__init__(**kwargs)
        SocketWrapperSingleton.get().set_push_callback(self.push_callback)
        self.players_list.adapter = \
                        MyListAdapter(listview_id='players_list_view',
                        parent_class = self,
                        data=[],
                        allow_empty_selection=True,
                        cls=ListItemButton)
        self.available_matches_players = []
        self.watch_matches_players = []
        self.load_available_matches()
        self.list_mode = self.LIST_MODES['available_matches'] # available_matches / watch matches
        self.my_kwargs = kwargs



    def on_enter(self):
        '''
        Called when this screen is visisble
        :return:
        '''
        print "on_enter"
        self.load_available_matches()
        SocketWrapperSingleton.get().set_push_callback(self.push_callback)

    def on_leave(self):
        '''
        Called when this screen is no longer visible
        :return:
        '''
        pass

    def push_callback(self, push_message_dict):
        '''
        called when receives push message from server
        :param push_message_dict: a dictinoary containing push data
        :return:
        '''

        print "received push:", push_message_dict
        if push_message_dict['prefix'] == 'matchAccepted':
            self.go_to_go_screen(int(push_message_dict['size']),'black',push_message_dict['opponent'])
            # self.manager.add_widget(GoScreen(board_size=int(push_message_dict['size']), my_color = 'black',opponent_username = push_message_dict['opponent'],ui_testing = False,  name='goScreen'))
            # self.manager.current = "goScreen"

    def remove_all_go_screens(self):
        '''
        removes all Go screens from the screen manager
        :return:
        '''
        to_remove = []
        for c in self.manager.children:
            print "child:", c.name
            if isinstance(c, GoScreen):
                print "remove"
                to_remove.append(c)
        for c in to_remove:
            self.manager.remove_widget(c)

    def increment_go_screen_index(self):
        '''
        increments the current Go Screen Index at the screen manager singletone
        :return:
        '''
        if hasattr(self.manager, 'goScreenIndex'):
            self.manager.goScreenIndex+=1
        else:
            self.manager.goScreenIndex = 0

    def go_to_go_screen(self, size, color, opponent__username ):
        '''
        Switches to Go screen through the ScreenManager
        :param size:
        :param color:
        :param opponent__username:
        :return:
        '''
        #print "go to to screen" , self.manager
        # remove all Go screen instances from screen

        self.remove_all_go_screens()

        self.increment_go_screen_index()

        self.manager.add_widget(GoScreen(board_size=int(size), my_color=color,
                                         opponent_username=opponent__username, ui_testing=False,
                                         name='goScreen' + str(self.manager.goScreenIndex)))
        self.manager.current = "goScreen" + str(self.manager.goScreenIndex)

    def go_to_go_screen_spectate(self, board_state, size, players):
        '''
        Switches to go screen for spectating mode, using ScreenManager
        :param board_state:
        :param size:
        :param players:
        :return:
        '''
        self.remove_all_go_screens()

        self.increment_go_screen_index()

        self.manager.add_widget(GoScreen(board_size=int(size), my_color="empty",
                                         opponent_username="empty", ui_testing=False,
                                         name='goScreen' + str(self.manager.goScreenIndex), spectating = True, board_state = board_state))
        self.manager.current = "goScreen" + str(self.manager.goScreenIndex)

    def go_to_go_screen_ai(self):
        '''
        switches to GO screen for ai mode, using ScreenManager
        :return:
        '''
        self.remove_all_go_screens()

        self.increment_go_screen_index()

        self.manager.add_widget(GoScreen(ui_testing = True, ai = True,
                                         name='goScreen' + str(self.manager.goScreenIndex)))
        self.manager.current = "goScreen" + str(self.manager.goScreenIndex)

    def handleListSelection(self, selection_text):
        '''
        handles the selection of an item in the listview
        :param selection_text:
        :return:
        '''
        print "list selection!"
        if self.list_mode == self.LIST_MODES['available_matches']:
            self.handleMatchAccepted(selection_text)

        elif self.list_mode == self.LIST_MODES['watch_matches']:
            self.handleWatchMatch(selection_text)

            #self.__init__(**self.my_kwargs) # reset data

    def handleWatchMatch(self, match_title):
        '''
        when user wants to watch(spectate) a match
        :param match_title: the title of the match the user wants to spectate
        :return:
        '''
        def get_usernames_from_title(title):
            '''
            returns tuple of usernames who are playing the match from the math title
            :param title:
            :return:
            '''
            "title is in the format of: user1 VS user2, returns (user1, user2)"
            return (title[:title.index(" VS")],title[title.index("VS ")+len("VS "):] )
        players = get_usernames_from_title(match_title)

        def on_response(response):
            '''
            this is a callback, called when response from server for the sepctating reqeust is received
            :param response:
            :return:
            '''
            print "received request response:", response
            if response['status'] == "OK":
                self.go_to_go_screen_spectate(response['boardState'], int(response['size']), players)
                # print "manager.go_board_size ", int(response['size'])
                # to_remove = []
                # for screen in self.manager.children:
                #     if isinstance(screen, GoScreen):
                #         to_remove.append(screen)
                # for screen in to_remove:
                #     self.manager.remove_widget(screen)
                #self.go_to_go_screen(int(response['size']), 'white', response['opponent'])
                # self.manager.add_widget(GoScreen(board_size = int(response['size']), my_color = 'white',opponent_username = response['opponent'],ui_testing = False, name='goScreen'))
                # self.manager.current = "goScreen"
                # self.__init__(**self.my_kwargs) # reset data

        SocketWrapperSingleton.get().request_response(
            SocketUtils.incode_request({'prefix': 'watchMatch', 'user1': players[0], 'user2':players[1]}), 'watchMatch',
            on_response)

        pass

    def handleMatchAccepted(self, creator_username):
        '''
        Called when user accepted match with 'creator_username
        @:param creator_username: username of player that created the pending match
        '''

        def on_response(response):
            '''
            callback method from server, called when response for pending match accepeptance has been received
            :param response: dictionary of response daya
            :return:
            '''
            print "received request response:", response
            if response['status'] == "OK":
                print "manager.go_board_size ", int(response['size'])

                self.go_to_go_screen(int(response['size']), 'white', response['opponent'])

        SocketWrapperSingleton.get().request_response(SocketUtils.incode_request({'prefix': 'acceptMatch', 'creator': creator_username}), 'acceptMatch', on_response)

    def bAvailableMatches(self):
        '''
        called when user presses the available matches button. populates available matches in list view/
        :return:
        '''
        print "available matches"
        self.list_mode = self.LIST_MODES['available_matches']
        self.load_available_matches()

    def bWatchMatches(self):
        '''
        called when user presses the watch matches button. populates current live matches in list view/

        :return:
        '''
        print "watch matches"
        self.list_mode = self.LIST_MODES['watch_matches']
        self.load_matches_to_watch()

    def bCreateMatch(self):
        '''
        called when user clicks the create match button
        :return:
        '''
        print "create match"
        popup = None

        def create_online_game(arg):
            '''
            creates an online pending game request, based on inputed data in the popup
            :param arg:
            :return:
            '''
            print "client entered:" , size_input.text
            if popup:
                popup.dismiss()
            if not size_input.text.isdigit():
                return
            #send request to server to create match
            SocketWrapperSingleton.get().send_output(SocketUtils.incode_request({'prefix':'createMatch', 'size': int(size_input.text)}))

        def create_game_against_ai(arg):
            '''
            creates an offline game against the ai
            :param arg:
            :return:
            '''
            print "client entered:", size_input.text
            if popup:
                popup.dismiss()
            if not size_input.text.isdigit():
                return
            # open game against ai
            self.go_to_go_screen_ai()


        size_input = TextInput(input_type = 'number')

        online_button = Button(text = "Online")
        online_button.bind(on_press = create_online_game)

        ai_button = Button(text = "Against Computer")
        ai_button.bind(on_press=create_game_against_ai)

        box = BoxLayout(orientation = 'vertical')
        box.add_widget(size_input)
        box.add_widget(online_button)
        box.add_widget(ai_button)
        popup = Popup(title='Enter Game size',
                      content=box,
                      size_hint=(None, None), size=(200, 200))
        popup.open()

        # send match create reqeust to server
        # self.changer()

    def bRefresh(self):
        '''
        refreshes the matches data from server
        :return:
        '''
        print "bRefresh click"

        def on_response(response):
            '''
            callback from server, called when server returns available matches
            :param response:
            :return:
            '''
            print "response response:" , response
            self.available_matches_players = response['available']
            self.watch_matches_players = response['to_watch']
            self.load_available_matches()
            self.load_matches_to_watch()
            if self.list_mode == self.LIST_MODES['available_matches']:
                self.load_available_matches()
            else:
                self.load_matches_to_watch()
        SocketWrapperSingleton.get().request_response(SocketUtils.incode_request({'prefix': 'refresh'}), 'refresh', on_response)

    def load_available_matches(self):
        '''
        loads available matches in listview
        :return:
        '''
        print "load available matches"

        self.players_list.adapter.data = self.available_matches_players
        self.players_list._trigger_reset_populate()

    def load_matches_to_watch(self):
        '''
        loads watchable matches in listview
        :return:
        '''
        print "load matches to watch"

        self.players_list.adapter.data = self.watch_matches_players
        self.players_list._trigger_reset_populate()

    def changer(self, *args):
        '''
        changes curren screen of ScreenManger to the Go Screen
        :param args:
        :return:
        '''
        # print "changing to goScreen"
        self.manager.current = 'goScreen'


# class LobbyApp(App):
#     def build(self):
#         # return LobbyWidget()
#         my_screenmanager = ScreenManager()
#
#         lobbyScreen = LobbyScreen(name='lobbyScreen')
#         goScreen = GoScreen(name='goScreen')
#
#         def win_cb(window, width, height):
#             if(my_screenmanager.current == "goScreen"):
#                 goScreen.game.handleWindowResize()
#
#         Window.bind(on_resize=win_cb)
#
#         my_screenmanager.add_widget(lobbyScreen)
#         my_screenmanager.add_widget(goScreen)
#         return my_screenmanager
#
# if __name__ == "__main__":
#     LobbyApp().run()