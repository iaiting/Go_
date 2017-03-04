from mcts_test.Game import Game


class TicTacToeGame(Game):
    board = [] #probably should remove this, this way its static (should be member) but is overriden to be member in c'tor
    SIZE = 3
    def __init__(self, _board = None):
        self.SIZE = 3
        #self.turn = 1
        if(_board != None):
            self.board = _board
        else:
            self.board = [[0 for x in xrange(self.SIZE)] for y in xrange(self.SIZE)]

    def copy(self):
        copyBoard = TicTacToeGame([[x for x in row] for row in self.board])
        return copyBoard

    def makeMove(self, player, move):
        #print "make move:" , self.turn, player
        if(self.board[move[0]][move[1]] != 0):
            raise Exception("Invalid Move")
        self.board[move[0]][move[1]] = player
        #self.switch_turn()

    # def switch_turn(self):
    #     self.turn = (self.turn%2)+1

    def undoMove(self, move):
        self.board[move[0]][move[1]] = 0


    def getWin(self):
        "3 draw, 0 not end of the game, 1 player1, 2 player2"
        def isWin(num):
            for r in self.board:
                if (r[0] == num and r[1] == num and r[2] == num):
                    return True
            for c in range(3):
                if (self.board[0][c] == num and self.board[1][c] == num and self.board[2][c] == num):
                    return True
            if (self.board[0][0] == num and self.board[1][1] == num and self.board[2][2] == num):
                return True
            if (self.board[0][2] == num and self.board[1][1] == num and self.board[2][0] == num):
                return True

        def isTie():
            for r in self.board:
                for val in r:
                    if val == 0:
                        return False
            return True


        if isWin(1):
            return 1
        if isWin(2):
            return 2
        if isTie():
            return 3
        return 0

    def game_finished(self):
        return self.getWin() != 0

    def get_size(self):
        return 3

    def getAllAvailableMoves(self):
        availMoves = []
        for r in xrange(self.SIZE):
            for c in xrange(self.SIZE):
                if(self.board[r][c] == 0):
                    availMoves.append([r,c])
        return availMoves


    def printMe(self):
        print "-" * 10
        for row in range(len(self.board)):
            strline = ""
            for col in range(len(self.board[row])):
                c = " "
                if (self.board[row][col] == 1):
                    c = "X"
                elif (self.board[row][col] == 2):
                    c = "Y"
                c += " " + "| " if (col != 2) else " "
                strline += c

            print strline

        print "-" * 10

# testing
# game = TicTacToeGame()
# game.makeMove(1,[0,0])
# game.makeMove(2,[0,1])
# game.makeMove(1,[0,2])
# game.makeMove(2,[1,0])
# game.makeMove(1,[1,1])
# game.makeMove(2,[1,2])
# game.makeMove(2,[2,0])
# game.makeMove(1,[2,1])
# game.makeMove(2,[2,2])
# game.printMe()
# print game.getWin()
#
# while(game.getWin() == 0):
#     game.printMe()
#     game.makeMove(1, choice(game.getAllAvailableMoves()))
#     if(game.getWin() != 0):
#         break
#     game.printMe()
#     game.makeMove(2, choice(game.getAllAvailableMoves()))
#
# game.printMe()
# print game.getWin()