import kivy
# kivy.require("1.8.0")

from random import randint
import sys

from kivy.properties import NumericProperty, ReferenceListProperty, BooleanProperty, ObjectProperty, ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.textinput import TextInput
from kivy.vector import Vector

from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.graphics import Rectangle, Color
from math import sqrt
import thread
import time

#from lobby import *
import NeuralNetwork
from ai.GoGame_Logic import GoGame_Logic
from ai.MCTS import MCTS
from ai.policies import Go_Simulator, Go_NN_expansion_policy, Go_NN_rollout_policy
from ai.policies import Go_random_expantion_policy
from ai.policies import Go_random_rollout_policy

from socket_utils import *
from socketwraper import *
import Queue
from NeuralNetwork import *
from subprocess import Popen, PIPE, STDOUT



class BoardState:
    "Represents a state of a go board in a game"
    def __init__(self, size):
        '''
        constructor
        :param self:
        :param size: size of the board
        :return:
        '''
        self.size = size
        self.board = [[0 for x in xrange(size)] for y in xrange(size)]
        self.prevStates = [] #stack of previous states of board (to undo moves and check for ko)
        self.turn = 1
        self.move_num = 1

    def copy_board(self):
        '''

        :param self:
        :return: a deep copy of the this boards state
        '''
        copy_board = BoardState(self.size)
        for row in xrange(self.size):
            for col in xrange(self.size):
                copy_board.board[row][col] = self.board[row][col]
        copy_board.turn = self.turn
        return copy_board


    def count_score(self):
        '''
        counts score in current board state

        :return: tuple: 0=>black score, 1=>white score, 3=> board of territory
        '''

        board_teritory = [[0 for x in xrange(self.size)] for y in xrange(self.size)] # 0=>a stone on board, 1=> black territory, 2=> white territory, 3=> mutual territory
        black_teritory = 0
        white_teritory = 0

        for i in xrange(self.size):
            for j in xrange(self.size):

                if(board_teritory[i][j] == 0 and self.board[i][j] == 0): #  if point hasn't been counted before & is empty
                    territory = self.get_territory(i, j, board_teritory)
                    black_teritory += territory[0]
                    white_teritory += territory[1]

        #print black_teritory
        #print white_teritory
        #for line in board_teritory:
         #   print line

        return (black_teritory, white_teritory, board_teritory)

    def get_territory(self, row, col, board_teritory = None):
        '''
        counts territory in given pos
        :param row:
        :param col:
        :param board_territory 2d array. if given, will be filled with territory of each player
        :return: tuple: 0=>black territory, 1=>white territory
        '''


        q = Queue.Queue()
        q.put((row,col))
        touched_black = False
        touched_white = False

        visited_stones = []
        visited_stones.append((row,col))
        territory_stones = []
        # BFS search
        while not q.empty():
            val = q.get()

            if self.board[val[0]][val[1]] != 0:
                if self.board[val[0]][val[1]] == 1 :  #black
                    touched_black = True
                if self.board[val[0]][val[1]] == 2:  #white
                    touched_white = True
            else:
                territory_stones.append(val)
                directions = [(val[0]+1,val[1]), (val[0]-1,val[1]), (val[0],val[1]+1), (val[0],val[1]-1)]
                for pos in directions:
                    if self.validPoint(pos) and (not (pos in visited_stones)):
                        q.put(pos)
                        visited_stones.append(pos)

        # mark visited stones in

        if touched_black and touched_white: # mutual territory
            for stone in visited_stones:
                if self.board[stone[0]][stone[1]] == 0:
                    if not board_teritory is None:
                        board_teritory[stone[0]][stone[1]] = 3
            return (0,0)
        if touched_black: # if territory only touched black
            for stone in visited_stones:
                if self.board[stone[0]][stone[1]] == 0:
                    if not board_teritory is None:
                        board_teritory[stone[0]][stone[1]] = 1
            return (len(territory_stones), 0)
        if touched_white: # if territory only touched white
            for stone in visited_stones:
                if self.board[stone[0]][stone[1]] == 0:
                    if not board_teritory is None:
                        board_teritory[stone[0]][stone[1]] = 2
            return (0, len(territory_stones))

        return (0,0)

    def playMove(self, point):
        '''

        :param point: point to attempt move at [row, col]

        :return: list:
                0 => boolean if move succeeded
                1 => list of captured stones as a result of this move
        '''

        # if there's already a stone in this position
        if(self.board[point[0]][point[1]] != 0):
            return [False, "Invalid move"]

        # if move is suicidal
        if self.is_move_suicidal(point, self.turn):
            return [False, "Invalid move: suicide"]

        #if move is ko
        if self.is_move_ko(point, self.turn):
            return [False, "Invalid move: ko"]

        self.board[point[0]][point[1]] = self.turn
        self.turn = (self.turn % 2) + 1


        # erase captured stones from the board
        captured = self.getCapturedStones(point, (self.turn % 2) + 1)
        for pos in captured:
            self.board[pos[0]][pos[1]] = 0

        self.add_board_state_to_stack()
        self.move_num += 1
        #return [True, []]
        #print "captured stones:" , captured
        return [True, captured]

    def play_pass_move(self):
        '''
        make a pass move
        :param self:
        :return:
        '''
        self.turn = self.otherPlayer(self.turn)

    def getCapturedStones(self, point, player):
        '''

        :param point: point of move that was made
        :param player: player that made that move
        :return: list of positions [row, col] of captured enemy stones
        '''

        captured = []

        down = (point[0] - 1, point[1])
        up = (point[0] + 1, point[1])
        right = (point[0], point[1] + 1)
        left = (point[0], point[1] - 1)

        for direc in [down, up, right, left]:
            if (self.validPoint(direc) and self.board[direc[0]][direc[1]] == self.otherPlayer(player)):
                group_dir = self.getGroup(direc)
                if (self.group_captured(group_dir)):
                    captured += group_dir

        # convert to set to avoid duplicates in the list (if a group could be captured from two directions it would appear twice in the list)
        return list(set(captured))

    def otherPlayer(self, player):
        '''

        :param player: current player
        :return: num of other player
        '''
        return (player%2) + 1

    def getGroup(self, point, player = None, group = None):
        '''
        returns group at given position

        recursive method

        :param point: point of a stone in the group
        :return: list of positions of stones in the group
        '''

        if group == None:
            group = []

        if(player == None):
            player = self.board[point[0]][point[1]]
            #group = [point]

        if((not self.validPoint(point)) or self.board[point[0]][point[1]] != player or (point in group)):
            return group

        group = group + [point]
       # print "added " , point, "to lst"
        down = (point[0]-1,point[1])
        up = (point[0]+1,point[1])
        right = (point[0],point[1]+1)
        left = (point[0],point[1]-1)

        for dir in [down, up, right, left]:
            if(dir not in group):
                group = self.getGroup(dir,player, group)

        return group

    def validPoint(self, point):
        '''

        :param self:
        :param point: a tuple that represents a point (row,col)
        :return: True if point is valid in the board, otherwise false
        '''
        return point[0] >= 0 and point[0] < self.size and point[1] >= 0 and point[1] < self.size

    def group_captured(self, group):
        '''
        checks if given group is dead
        :param group: list of positions of stones in the group
        :return: True if group is dead, otherwise False
        '''

        #if a stone in the group has a liberty left - then the group is alive
        for pos in group:
            if(self.count_liberties(pos) > 0):
                return False

        return True

    def count_liberties(self, pos):
        '''

        :param pos: position of a stone on the board
        :return: number of liberties of that SINGLE stone - without counting liberties of the group it's in
        '''

        if(self.board[pos[0]][pos[1]] == 0):
            raise Exception("count_liberties exception: no stone in given position")

        down = (pos[0] - 1, pos[1])
        up = (pos[0] + 1, pos[1])
        right = (pos[0], pos[1] + 1)
        left = (pos[0], pos[1] - 1)

        liberties = [ 1 if self.validPoint(o_pos) and self.board[o_pos[0]][o_pos[1]] == 0 else 0 for o_pos in [down, up, right, left]]
        return sum(liberties)

    def is_move_suicidal(self, point, turn):
        '''

        :param self:
        :param point: tuple of a point on the board
        :param turn: player who's turn it is
        :return: True if given move is a suicide move - it will self-kill a group of the same player's stones without killing any stones of the other player
        '''
        copy = self.copy_board()
        copy.board[point[0]][point[1]] = self.turn
        if (copy.group_captured(copy.getGroup(point))):  # if there's a possibility for a suicide move
            # erase captured stones from the copy board
            captured = copy.getCapturedStones(point, copy.turn)
            for pos in captured:
                copy.board[pos[0]][pos[1]] = 0
            # if stone is still dead - then move is suicidal
            if copy.group_captured(copy.getGroup(point)):
                return True
        return False

    def add_board_state_to_stack(self):
        '''
        adds current board state to stack of previous moves
        :return:
        '''
        copy = [[x for x in row] for row in self.board]
        self.prevStates.append(copy)

    @staticmethod
    def board_state_equal(state1, state2):
        '''

        :param state1: board state one - list of lists
        :param state2: board state two - list of lists
        :return: True if board states are equal, otherwise False
        '''
        "returns true if both board states are equal"
        if(len(state1) != len(state2)):
            return False
        for row in xrange(len(state1)):
            for col in xrange(len(state1[row])):
                if(state1[row][col] != state2[row][col]):
                    return False
        return True

    def is_move_ko(self, point, player):
        '''
        returns True if move is illegal ko move.
        A Ko move is a move that restores the board the the state it had been in two turn ago -
        effectively calncelling the opponents move. Without the ko rule, Go games could go on forever
        :param point: position of move
        :param player: player that makes the move
        :return: True if move is ko, otherwise False
        '''
        if(len(self.prevStates) < 2):
            return False
        copy = self.copy_board()
        copy.board[point[0]][point[1]] = player
        # erase captured stones from the board
        captured = copy.getCapturedStones(point, copy.turn)
        for pos in captured:
            copy.board[pos[0]][pos[1]] = 0
        if BoardState.board_state_equal(copy.board, self.prevStates[-2]):
            return True
        return False

    def turn_color(self):
        '''

        :param self:
        :return: String of the current player color whos turn it is
        '''
        return "Black" if self.turn == 1 else "White"

    def to_nn_input_arr(self):
        '''

        :param self:
        :return: a list made of this board that servers as an input for the Neural Network
        '''
        def getInputDataIndex(row, col, player, turn):
            player_off_set = 0
            if player != 0:
                if player == turn:
                    player_off_set = 1
                else:
                    player_off_set = 2
            row = self.size - row - 1
            return (row * self.size + col) * 3 + player_off_set

        inputs = [0 for x in xrange((self.size * self.size * 3))]
        for i in xrange(len(self.board)):
            for j in xrange(len(self.board[0])):
                inputs[getInputDataIndex(i, j, self.board[i][j], self.turn)] = 1.0

        return inputs

    @classmethod
    def createFromJson(cls, str_json):
        '''
        Creates a BoardState from JSON
        :param cls: caling class
        :param str_json: Json encoded data for the board state
        :return: a BoardState object made from the decoded JSON
        '''

        data = json.loads(str_json)
        instance = BoardState(1)
        instance.size = int(data['size'])
        instance.board = data['board']
        instance.turn = int(data['turn'])
        return instance

    def is_legal(self, move):
        '''

        :param self:
        :param move: tuple of move on board
        :return: True if move i lgeal, otherwise False
        '''
        return self.board[move[0]][move[1]] == 0 and not self.is_move_suicidal(move, self.turn) and not self.is_move_ko(move, self.turn)

    def is_filling_self_eye(self, move):
        '''
       :param self:
       :param move: tuple of move om board
       :return: True if move is filling an eye of a player's group, otherwise False
       '''
        territory = self.get_territory(move[0], move[1])
        if territory[self.turn-1] != 0:
            return True
        return False

class StoneWidget(Widget):
    '''
    A widget for a Go stone
    '''
    R = NumericProperty(0)
    G = NumericProperty(0)
    B = NumericProperty(0)
    size = NumericProperty(30.0)
    def __init__(self, row, col, x, y, player, size, **kwargs):
        '''
        constructor
        :param row: row of the stone
        :param col:  column of the stone
        :param x:  x position of the stone
        :param y: y position of the stone
        :param player: player this stone belongs to
        :param size: size of the stone
        :param kwargs:
        '''
        super(StoneWidget, self).__init__(**kwargs)

        self.row = row
        self.col = col
        self.x = x
        self.y = y
        self.size = size
        if(player == 1): #black
            self.R = 0
            self.G = 0
            self.B = 0
        else: #white
            self.R = 1
            self.G = 1
            self.B = 1

class SmallStoneWidget(StoneWidget):
    '''
    A small stone - also a pointer to a position on the board
    '''
    def __init__(self,row, col, x, y, player, size,  **kwargs):
        '''
        constructor
        :param row: row of the stone
        :param col:  column of the stone
        :param x:  x position of the stone
        :param y: y position of the stone
        :param player: player this stone belongs to
        :param size: size of the stone
        :param kwargs:
        '''
        super(SmallStoneWidget, self).__init__(row, col, x, y, player, size, **kwargs)

class StonePointer(Widget):
    '''
        A pointer to a position on the board
        '''
    R = NumericProperty(0)
    G = NumericProperty(0)
    B = NumericProperty(0)
    size = NumericProperty(30.0)
    def __init__(self, x, y, player, size, **kwargs):
        '''
                constructor

                :param x:  x position of the stone
                :param y: y position of the stone
                :param player: player this stone belongs to
                :param size: size of the stone
                :param kwargs:
                '''
        super(StonePointer, self).__init__(**kwargs)

        self.x = x
        self.y = y
        self.size = size
        if(player == 1): #black
            self.R = 1
            self.G = 1
            self.B = 1
        else: #white
            self.R = 0
            self.G = 0
            self.B = 0

class LineWidget(Widget):
    '''
    A widget for a line inside the go board
    '''
    WIDTH = 2
    startX = NumericProperty(0)
    startY = NumericProperty(0)
    sizeX = NumericProperty(0)
    sizeY = NumericProperty(0)

    def __init__(self, isVertical, startX, startY, length, **kwargs):
        '''

        :param isVertical: True if line is vertical, False if line is horizontal
        :param startX: x position of starting point
        :param startY: y position of starting point
        :param length: length of line
        :param kwargs:
        '''
        super(LineWidget, self).__init__(**kwargs)
        self.startX = startX
        self.startY = startY
        if isVertical:
            self.sizeX = self.WIDTH
            self.sizeY = length
        else:
            self.sizeX = length
            self.sizeY = self.WIDTH



class GoGame(BoxLayout):
    '''
    A layout that encapsulates the go bard
    '''
    sides_margin = NumericProperty(10)

    label_text = ObjectProperty("Sample \n Text")
    label_fontsize = NumericProperty(30)

    go_board_widget = ObjectProperty()
    go_info_widget = ObjectProperty()

    territory_button = ObjectProperty()
    pass_button = ObjectProperty()
    resign_button = ObjectProperty()
    chat_text_input = ObjectProperty()
    chat_text_box = ObjectProperty()
    def __init__(self,  **kwargs):
        '''
        Constructor
        :param kwargs:
        '''
        super(GoGame, self).__init__(**kwargs)
        #print "go game ctor"
        self.init_data(**kwargs)
        self.b_return_to_lobby = Button(text="Back to Lobby", size_hint=(1, 0.1))
        self.b_rematch = Button(text="Rematch", size_hint=(1, 0.1))
        #self.handleWindowResize()
        self.kwargs = kwargs


        self.chat_text_input.bind(on_text_validate=self.on_chat_enter)

    def on_chat_enter(self,instance):
        '''
        Called when user presses Enter in the chat
        '''
        if not self.ui_testing:
            SocketWrapperSingleton.get().send_output(SocketUtils.incode_request({'prefix':'chat', 'message':SocketWrapperSingleton.get().username + ":" + self.chat_text_input.text}))
            self.add_to_chat(SocketWrapperSingleton.get().username + ":" + self.chat_text_input.text)
        else:
            self.add_to_chat(self.chat_text_input.text)
        self.chat_text_input.text = ""
        #append text to chat

    def add_to_chat(self, message):
        '''
        Adds message to chat log
        :param message: message to be added
        '''
        self.chat_text_box.text += "[color=000000]" + message +"[/color]\n"



    def init_data(self, **kwargs):
        '''
        A help-method for the constructor. initiates member variables from data in kwargs
        :param kwargs: hold data for member variables to be instantiated
        '''
        self.spectating = True if 'spectating' in kwargs else False

        self.ui_testing = True if ('ui_testing' in kwargs and kwargs['ui_testing']) else False
        if not self.ui_testing:
            SocketWrapperSingleton.get().set_push_callback(self.push_callback)

        if self.spectating:
           # self.boardState.board = json.loads(kwargs['boardState'])['board']
           self.handle_spectating_init(**kwargs)
          # self.boardState = BoardState.createFromJson(kwargs['board_state'])
        else:
            self.boardState = BoardState(kwargs['board_size'] if 'board_size' in kwargs else 5)


        if self.ui_testing and not self.spectating:
            self.boardState = BoardState(9)
        if 'initial_board_state' in kwargs:
            self.boardState.board = kwargs['initial_board_state']
        self.opponent_username = kwargs['opponent_username'] if not self.ui_testing else 'other'
        if not self.ui_testing:
            self.color_num = 1 if kwargs['my_color'] == 'black' else 2
        else:
            self.color_num = 1

        self.showing_territory = False
        self.end_game = False
        self.b_return_to_lobby = Button(text="Back to Lobby", size_hint=(1, 0.1))
        self.b_rematch = Button(text="Rematch", size_hint=(1, 0.1))
        self.stone_pointer = None
        self.passed_prev_turn = False  # if opponent passed his move in the previous turn
        self.end_game_by_resignation = 0
        self.change_screen_func = kwargs['change_screen_func']

        self.ai = kwargs['ai'] if 'ai' in kwargs else False
        self.neural_network = None
        if self.ai:
            pass

        # extra dirty fix
        if not self.ui_testing:
            self.delayExecThreaded(self.handleWindowResize, .7)
            self.delayExecThreaded(self.handleWindowResize, 1)


    def handle_spectating_init(self, **kwargs):
        '''
        special initialization method called when user is spectating a game
        :param kwargs:
        :return:
        '''
        self.boardState = BoardState.createFromJson(kwargs['board_state'])
        self.go_info_widget.remove_widget(self.pass_button)
        self.go_info_widget.remove_widget(self.resign_button)


    def push_callback(self, push_message_dict):
        '''
        A callback method that's called when user receives a push message from the server
        :param push_message_dict: a dictionary that containes the data received in the push message from the server
        :return:
        '''
        if push_message_dict['prefix'] == 'makeMove':
            self.make_move((int(push_message_dict['row']), int(push_message_dict['col'])))
        elif push_message_dict['prefix'] == 'makePassMove':
            self.make_pass_move()
        elif push_message_dict['prefix'] == 'makeResignMove':
            self.end_game_by_resignation = self.boardState.otherPlayer(self.color_num)
            self.handle_end_game()
        elif push_message_dict['prefix'] == 'chat':
            self.add_to_chat(push_message_dict['message'])
    def delayExec(self, *kwargs):
        '''
        delays execution of a function - BLOCKS THREAD
        :param kwargs:
                    0 => function to execute
                    1 => time for delay in seconds
                    2...n => arguments for function
        '''
        time.sleep(float(kwargs[1]))
        if len(kwargs) > 2:
            kwargs[0](kwargs[2:])
        else:
            kwargs[0]()

    def delayExecThreaded(self, *kwargs):
        '''
                delays execution of a function - on a different thread
                :param kwargs:
                            0 => function to execute
                            1 => time for delay in seconds
                            2...n => arguments for function
        '''
        thread.start_new_thread(self.delayExec, kwargs)

    def getTouchPoint(self, x, y):
        '''
        converts user's touch to a point on the board: (x,y) -> (row, col)
        :param x: x press on board
        :param y: y press on board
        :return: list:
                0 => row on grid for this press
                1 => col on grid for this press
        '''
        x-=self.sides_margin
        y-=self.sides_margin

        row = float(y) / self.spacing
        col = float(x) / self.spacing

        row = int(round(row))
        col = int(round(col))
        return (row,col)


    def make_move(self, point):
        '''
        Makes a move in the game
        :param point: point for the move to be played at
        '''
        self.showing_territory = False
        self.passed_prev_turn = False
        self.hide_territory()
        "plays given move with graphic output"
        move_info = self.boardState.playMove(point)

        #print move_info

        stones_widgets = []
        for widget in self.go_board_widget.children:
                if isinstance(widget, StoneWidget):
                    #print widget.row, widget.col
                    stones_widgets.append(widget)
        #print "*"*10
        if (move_info[0]):  # if move is legal
            self.addStoneWidget(self.boardState.otherPlayer(self.boardState.turn), point)
            # remove all captured stones
            CAPTURE_ANIMATION = False
            delay_anim_counter = 0.0
            for widget in stones_widgets:
                #print widget.row, widget.col
                for point in move_info[1]:
                    if (widget.row == point[0] and widget.col == point[1]):
                       # print "removing", point
                        # self.delayExec(self.remove_widget, delay_anim_counter + 0.1, widget)
                        # have a delay before removing the stone for animation
                        if CAPTURE_ANIMATION:
                            thread.start_new_thread(self.remove_widget_after, (widget, delay_anim_counter))
                            delay_anim_counter += 0.1
                        else:
                            self.go_board_widget.remove_widget(widget)


        self.update_hud()
        self.boardState.count_score()


    def bOnPass(self):
        '''
        Called when user presses the 'pass' button
        :return:
        '''
        self.make_pass_move()
        if not self.ui_testing:
            SocketWrapperSingleton.get().send_output(SocketUtils.incode_request({'prefix':'makePassMove'}))
    def make_pass_move(self):
        '''
        Makes a pass move in the game
        '''
        self.boardState.play_pass_move()
        self.update_hud()

        if not self.passed_prev_turn:
            self.passed_prev_turn = True
            if self.ai:
                thread.start_new_thread(self.ai_make_move, ())
        else: #End game
            self.handle_end_game()

    def handle_end_game(self):
        '''
        called when a game ends. Handles Score counting, declaring the winner and sends data to user's containing the winner
        '''
        self.end_game = True
        territory = self.boardState.count_score()

        self.show_territory(territory[2])
        #update HUD text
        if not self.ui_testing:
            username_black = SocketWrapperSingleton.get().username if self.color_num == 1 else self.opponent_username
            username_white = SocketWrapperSingleton.get().username if self.color_num == 2 else self.opponent_username
        else:
            username_black = 'me'
            username_white = 'other'
        if self.end_game_by_resignation == 0:
            winner = username_black if territory[0] > territory[1] else username_white
            if(territory[0] == territory[1]):
                winner = "TIE"
        else:  # game ended by resignation
            if self.end_game_by_resignation == 1: # black resigned
                winner = username_white
            else: # white resigned
                winner = username_black
            winner += " (Resignation)"

        HUD_TEXT = "[color=000000]%s[/color] [color=ff0000]VS[/color] [color=ffffff]%s[/color] \n Winner: %s \n Black: %d \n White: %d " % (username_black, username_white, winner, territory[0], territory[1])
        self.label_text = HUD_TEXT
        self.label_fontsize = int(self.go_info_widget.width * 0.1)

        self.showing_territory = True

        if(self.b_rematch not in self.go_info_widget.children):
            self.go_info_widget.add_widget(self.b_rematch,1)
            self.go_info_widget.add_widget(self.b_return_to_lobby,2)
            self.go_info_widget.remove_widget(self.pass_button)
            self.go_info_widget.remove_widget(self.territory_button)
            self.go_info_widget.remove_widget(self.resign_button)


    def hide_territory(self):
        '''
        hides the territory marks from the board
        '''
        to_remove = []
        for child in self.go_board_widget.children:
            if isinstance(child, SmallStoneWidget):
                to_remove.append(child)

        for child in to_remove:
            self.go_board_widget.remove_widget(child)

    def show_territory(self, territory_board = None):
        '''
        shows territory marks on the board
        :param territory_board: a board (list of lists) containing the territory of each player
        '''
        if territory_board is None:
            territory_board = self.boardState.count_score()[2]
        stone_size = 10.0
        for i in xrange(len(territory_board)):
            for j in xrange(len(territory_board)):
                if(1<=territory_board[i][j]<=2):
                    self.go_board_widget.add_widget(
                        SmallStoneWidget(i, j, self.sides_margin + self.spacing * j - stone_size / 2.0,
                                    self.sides_margin + self.spacing * i - stone_size / 2.0, territory_board[i][j], stone_size))

    def bOnResign(self):
        '''
        called when user presses the resign button
        '''
        self.end_game_by_resignation = self.color_num
        self.handle_end_game()

        if not self.ui_testing:
            SocketWrapperSingleton.get().send_output(SocketUtils.incode_request({'prefix':'makeResignMove'}))

    def rematch(self):
        '''
        called when user presses the rematch button
        :return:
        '''
        pass # todo

    def return_to_lobby(self):
        '''
        changes scree to lobby screen (through the ScreenManager
        :return:
        '''
        self.change_screen_func("lobbyScreen")

    def get_considerable_moves(self, board_string, NUM_OF_SIMULATIONS):
        '''
        :param board_string: a string the encodes the board data
        :param NUM_OF_SIMULATIONS: number of allcated simulations for MCTS
        :return: a list of considerable moves by the AI (decided by the Neural Network - expantion policy)
        '''
        p = Popen(['java', '-jar', 'getMove.jar', board_string, str(2), str(NUM_OF_SIMULATIONS), "1"], stdout=PIPE, stderr=STDOUT)
        moves = []
        for line in p.stdout:
            move = []
            while line != "":
                if "," in line:
                    move.append(int(line[:line.index(",")]))
                    line = line[line.index(",")+1:]
                else:
                    move.append(int(line))
                    line = ""
            moves.append(move)
        return moves
    def show_ai_considerable_moves(self, considerable_moves):
        '''
        shows considrable moves by ai on the board
        :param considerable_moves: list of considerable moves
        '''
        self.clear_moves_marking()
        for move in considerable_moves:
            print move

            if len(move) == 3:
                print "!!!"
                s = StonePointer(self.sides_margin + self.spacing * move[1] - 17 / 2.0,
                                                             self.sides_margin + self.spacing * move[0] - 17 / 2.0,
                                                             self.boardState.turn, 20)
                s.R = 0
                self.go_board_widget.add_widget(s)
            else:
                self.go_board_widget.add_widget(StonePointer(self.sides_margin + self.spacing * move[1] - 17 / 2.0,
                                                             self.sides_margin + self.spacing * move[0] - 17 / 2.0,
                                                             self.boardState.turn, 20))
    def clear_moves_marking(self):
        '''
        clears moves marking from the board
        '''
        to_remove = []
        for child in self.go_board_widget.children:
            if isinstance(child, StonePointer):
                to_remove.append(child)
        for thing in to_remove:
            self.go_board_widget.remove_widget(thing)

    def ai_make_move(self):
        '''
        executes a move that's decided by the AI
        '''
        NUM_OF_SIMULATIONS = 20
        board_string = ""
        for row in self.boardState.board:
            for val in row:
                board_string+=str(val)
                board_string+=","
            board_string += "|"
        #print board_string

        #get considerable moves
        consirable_moves = self.get_considerable_moves(board_string, NUM_OF_SIMULATIONS)
        self.show_ai_considerable_moves(consirable_moves)
        p = Popen(['java', '-jar', 'getMove.jar', board_string, str(2), str(NUM_OF_SIMULATIONS), "0"], stdout=PIPE, stderr=STDOUT)
        last_line = ""
        for line in p.stdout:
            last_line = line
            print line
        row = int(last_line[0:last_line.index(',')])
        col = int(last_line[last_line.index(',')+1:])
        self.make_move((row,col))
        self.clear_moves_marking()

    def on_touch_down(self, touch):
        '''
        Called when user touches the screen
        :param touch: point the user touched
        '''

        if self.end_game:
            if (self.b_rematch.collide_point(touch.x, touch.y)):
                self.rematch()
            elif(self.b_return_to_lobby.collide_point(touch.x, touch.y)):
                self.return_to_lobby()
            elif (self.chat_text_input.collide_point(touch.x, touch.y)):
                self.chat_text_input.on_touch_down(touch)
            return

        if(self.go_board_widget.collide_point(touch.x, touch.y) and not self.spectating):
            point = self.getTouchPoint(touch.x, touch.y)

            # if didn't press something in board
            if 0<=point[0] < self.boardState.size and 0<=point[1] < self.boardState.size:

                #print "point played:", point

                if (self.ui_testing) or self.color_num == self.boardState.turn: # if this is my turn
                    # update move in AI
                    self.make_move(point)
                    # update move to server
                    if not self.ui_testing:
                        SocketWrapperSingleton.get().send_output(SocketUtils.incode_request({'prefix':'makeMove', 'row':point[0], 'col':point[1]}))
                    if self.ai:
                        thread.start_new_thread(self.ai_make_move, ())
                        #self.delayExecThreaded(self.ai_make_move, 0.01, ())



        elif (self.territory_button.collide_point(touch.x, touch.y)):
            if self.showing_territory:
                self.hide_territory()
            else:
                self.show_territory()

            self.showing_territory = not self.showing_territory

        elif (not self.spectating and self.pass_button.collide_point(touch.x, touch.y)):
            self.bOnPass()


        elif (not self.spectating and self.resign_button.collide_point(touch.x, touch.y)):
            self.bOnResign()

        elif (self.chat_text_input.collide_point(touch.x, touch.y)):
            self.chat_text_input.on_touch_down(touch)

        return False
    def remove_widget_after(self, widget, seconds):
        '''
        removes widget after given amount of time
        :param widget: widgegt to be removed
        :param seconds: time to wait before removement
        '''
        time.sleep(seconds)
        self.remove_widget(widget)

    def initLineWidgets(self):
        '''
        draws line widgets of board on the Go Board widget
        '''
        sides_margin = self.sides_margin
        width = self.width - self.go_info_widget.width
        height = self.height
        width = min(width,height)
        height = min(width,height)
        self.spacing = float(width-(sides_margin*2)) / self.boardState.size
        spacing = self.spacing
        #print spacing
        for row in xrange(self.boardState.size):
            self.go_board_widget.add_widget(LineWidget(False, sides_margin, sides_margin + row * spacing, width - sides_margin * 2 - spacing))

        for col in xrange(self.boardState.size):
            self.go_board_widget.add_widget(LineWidget(True, sides_margin + col * spacing, sides_margin, height - sides_margin * 2 - spacing))

    def clear_widgets_in_go_board(self):
        '''
        clears all widgets in go board widgets
        '''
        self.go_board_widget.clear_widgets()

    def update_label_pos(self):
        '''
        updates position of players usernmaes according to screen size
        '''
        self.label_x = self.sides_margin + self.boardState.size * self.spacing
        self.label_top = self.sides_margin + self.boardState.size * self.spacing

    def update_hud(self):
        '''
        updates the HUD (players usernames, score, option ETC) depending on current game state
        :return:
        '''
        if not self.ui_testing:
            username_black = SocketWrapperSingleton.get().username if self.color_num == 1 else self.opponent_username
            username_white = SocketWrapperSingleton.get().username if self.color_num == 2 else self.opponent_username
        else:
            username_black = 'me'
            username_white = 'other'
        HUD_TEXT = "[color=000000]%s[/color] [color=ff0000]VS[/color] [color=ffffff]%s[/color] \n Turn: %s \n Move: %d " % (username_black, username_white, self.boardState.turn_color(), self.boardState.move_num)
        self.label_text = HUD_TEXT
        self.label_fontsize = int(self.go_info_widget.width * 0.1)

    def handleWindowResize(self):
        '''
        adjusts to screen resize
        '''
        self.clear_widgets_in_go_board()

        self.initLineWidgets()
        self.drawStonesBasedOnBoard()

        self.update_hud()

        if self.end_game:
            self.handle_end_game()


    def drawStonesBasedOnBoard(self):
        '''
        Draws go stones widgets based on current game state
        '''
        for row in xrange(self.boardState.size):
            for col in xrange(self.boardState.size):
                if(self.boardState.board[row][col] != 0):
                    self.addStoneWidget(self.boardState.board[row][col], (row, col))

    def addStoneWidget(self, player, pos):
        '''
        adds a go stone widget at a given positon
        :param player: player the stone belongs to
        :param pos: position to add stone at
        '''
        stone_size = float(float(self.spacing))
        self.go_board_widget.add_widget(StoneWidget(pos[0], pos[1], self.sides_margin + self.spacing * pos[1] - stone_size / 2.0, self.sides_margin + self.spacing * pos[0] - stone_size / 2.0, player, stone_size))

        if self.stone_pointer:
            self.go_board_widget.remove_widget(self.stone_pointer)
        self.stone_pointer = StonePointer(self.sides_margin + self.spacing * pos[1] - stone_size / 2.0, self.sides_margin + self.spacing * pos[0] - stone_size / 2.0,player, stone_size)
        self.go_board_widget.add_widget(self.stone_pointer)


class GoScreen(Screen):
    '''
    Widget that represents the screen of the go playing part of the application. Invoked by the ScreenManager.
    '''
    def __init__(self, **kwargs):
        '''
        Constructor
        :param kwargs: contains data for specific initialization of the go game screen
        '''
        super(GoScreen, self).__init__(**kwargs)

        self.kwargs = kwargs
        self.init_game()

    def init_game(self):
        '''
        initializes data for the go game
        '''
        self.kwargs['change_screen_func'] = self.change_screen_to_lobby
        self.game = GoGame(**self.kwargs)  # GoGame(board_size = kwargs['board_size'])
        self.add_widget(self.game)
        self.ui_testing = True if ('ui_testing' in self.kwargs and self.kwargs['ui_testing']) else False

        def win_cb(window, width, height):
            #if (not self.ui_testing and self.manager.current == ("goScreen"+str(self.manager.goScreenIndex))):
            #print "window resize"

            if (self.manager is not None) and self.manager.current == ("goScreen"+str(self.manager.goScreenIndex)):
                self.game.handleWindowResize()

        Window.bind(on_resize=win_cb)
        #print "window resize binded"

    def on_enter(self):
        '''
        called when this screen comes to the foreground of the application (visible)
        '''
        if(self.game.end_game):
            self.remove_widget(self.game)
            self.init_game()



    def on_leave(self):
        ''' called when screen is no longer visible'''
        pass

    def change_screen_to_lobby(self, name):
        '''
        changes screen back to the lobby screen, through the ScreenManager
        :param name: name of the lobby screen (not crucial)
        '''
        self.manager.current = 'lobbyScreen'


class GoApp(App):
    '''
    The go app for standalone, offline go playing against computer - without need for Server
    '''
    def build(self):
        '''
        builds go app
        :return:
        '''
        # screen = GoScreen(ui_testing = True, ai = False, initial_board_state =
        # [[1, 0, 2, 2, 1, 1, 2, 1, 1], [2, 2, 1, 1, 1, 2, 2, 1, 1], [2, 2, 1, 0, 0, 1, 0, 0, 2],
        #  [2, 2, 1, 1, 1, 0, 2, 0, 0], [2, 1, 0, 1, 1, 2, 2, 1, 1], [0, 1, 1, 2, 1, 1, 2, 1, 1],
        #  [2, 2, 2, 2, 2, 2, 2, 1, 0], [0, 2, 0, 1, 0, 1, 0, 2, 1], [2, 2, 1, 2, 2, 0, 1, 1, 0]]
        # # [[0, 0, 2, 0, 1, 1, 2, 1, 1], [2, 2, 1, 1, 1, 2, 2, 1, 1], [2, 2, 1, 0, 0, 1, 0, 0, 2],
        # #  [2, 2, 1, 1, 1, 0, 2, 0, 0], [2, 1, 0, 1, 1, 2, 2, 1, 1], [0, 1, 1, 2, 1, 1, 2, 1, 1],
        # #  [2, 2, 2, 2, 2, 2, 2, 1, 0], [0, 2, 0, 1, 0, 1, 0, 2, 1], [2, 2, 1, 2, 2, 0, 1, 1, 0]]
        # # [[1, 1, 0, 1, 1, 1, 1, 2, 2], [1, 1, 1, 1, 1, 2, 1, 2, 0], [0, 1, 1, 1, 2, 2, 2, 2, 2],
        # #  [1, 1, 1, 1, 2, 1, 2, 2, 2], [1, 2, 1, 1, 1, 1, 2, 2, 0], [2, 2, 1, 2, 2, 2, 2, 2, 2],
        # #  [0, 2, 2, 2, 2, 2, 2, 2, 0], [2, 2, 2, 0, 2, 2, 2, 0, 2], [2, 2, 0, 2, 2, 2, 0, 2, 0]]

                        #  )
        screen = GoScreen(ui_testing = True, ai = True)
        def win_cb(window, width, height):
            '''
            called when window resizes
            :param window: window that has been resized
            :param width: new width
            :param height: new height
            '''
            screen.game.handleWindowResize()

        Window.bind(on_resize=win_cb)
        return screen


if __name__ == "__main__":
    GoApp().run()