import Queue
import json
from Game import Game

#NOT USED SINCE AI MOVED TO JAVA JAR
class GoGame_Logic(Game):

    def __init__(self, size):
        self.size = size
        self.board = [[0 for x in xrange(size)] for y in xrange(size)]
        self.prevStates = [] #stack of previous states of board (to undo moves and check for ko)
        self.turn = 1
        self.move_num = 1

    def copy(self):
       # print "COPIES BOARD"
        copy_game = GoGame_Logic(self.size)
        for row in xrange(self.size):
            for col in xrange(self.size):
                copy_game.board[row][col] = self.board[row][col]
        copy_game.turn = self.turn
        copy_game.prevStates = [x for x in self.prevStates]
        return copy_game

    def get_size(self):
        return self.size

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

       # print black_teritory
      #  print white_teritory
      #   for line in board_teritory:
      #       print line

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
            #print "bfs with:" , val

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

    def makeMove(self, player = None, move = None):
        '''

        :param move: point to attempt move at [row, col]

        :return: list:
                0 => boolean if move succeeded
                1 => list of captured stones as a result of this move
        '''
      #  print "playMove in point:", point

        if player is None:
            player  = self.turn

        self.turn = player

        # if there's already a stone in this position
        if(self.board[move[0]][move[1]] != 0):
            return [False, "Invalid move"]

        # if move is suicidal
        if self.is_move_suicidal(move, self.turn):
            return [False, "Invalid move: suicide"]

        #if move is ko
        if self.is_move_ko(move, self.turn):
            return [False, "Invalid move: ko"]

        self.board[move[0]][move[1]] = self.turn
        self.turn = (self.turn % 2) + 1


        # erase captured stones from the board
        captured = self.getCapturedStones(move, (self.turn % 2) + 1)
        for pos in captured:
            self.board[pos[0]][pos[1]] = 0

        self.add_board_state_to_stack()
        self.move_num += 1
        #return [True, []]
        return [True, captured]

    def play_pass_move(self):
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
        copy = self.copy()
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
        returns True if move is illegal ko move
        :param point: position of move
        :param player: player that makes the move
        :return: True if move is ko
        '''
        if(len(self.prevStates) < 2):
            return False
        copy = self.copy()
        copy.board[point[0]][point[1]] = player
        # erase captured stones from the board
        captured = copy.getCapturedStones(point, copy.turn)
        for pos in captured:
            copy.board[pos[0]][pos[1]] = 0
        if GoGame_Logic.board_state_equal(copy.board, self.prevStates[-2]):
            return True
        return False

    def getWin(self):
        if not self.game_finished():
            return 0
        territroy = self.count_score()
        if territroy[0] > territroy[1]:
            return 1
        elif territroy[0] < territroy[1]:
            return 2
        return 3


    def getAllAvailableMoves(self):
        moves = []
        for row in xrange(self.size):
            for col in xrange(self.size):
                move = [row, col]
                if self.is_legal(move) and not self.is_filling_self_eye(move):
                    moves.append(move)
        return moves

    def game_finished(self):
        return len(self.getAllAvailableMoves()) == 0

    def turn_color(self):
        return "Black" if self.turn == 1 else "White"

    def to_nn_input_arr(self):
        def getInputDataIndex(row, col, player, turn):
            player_off_set = 0
            if player != 0:
                if player == turn:
                    player_off_set = 1
                else:
                    player_off_set = 2
            row = self.size - row - 1
            return (row * self.size + col)*3 + player_off_set

        inputs = [0 for x in xrange((self.size*self.size*3))]
        for i in xrange(len(self.board)):
            for j in xrange(len(self.board[0])):
                inputs[getInputDataIndex(i,j,self.board[i][j], self.turn)] = 1.0

        return inputs

    @classmethod
    def createFromJson(cls, str_json):
        # def __init__(self, size):
        #     self.size = size
        #     self.board = [[0 for x in xrange(size)] for y in xrange(size)]
        #     self.prevStates = []  # stack of previous states of board (to undo moves and check for ko)
        #     self.turn = 1
        #     self.move_num = 1

        data = json.loads(str_json)
        instance = GoGame_Logic(1)
        instance.size = int(data['size'])
        instance.board = data['board']
        instance.turn = int(data['turn'])
        return instance

    def is_legal(self, move):

        return self.board[move[0]][move[1]] == 0 and not self.is_move_suicidal(move, self.turn) and not self.is_move_ko(move, self.turn)

    def is_filling_self_eye(self, move):
        territory = self.get_territory(move[0], move[1])
        if territory[self.turn-1] != 0:
            #print "eye filling"
            if territory[self.turn-1] <= 5:
                return True
        return False

    def printMe(self):
        for row in self.board:
            for val in row:
                print val , " ",
            print ""