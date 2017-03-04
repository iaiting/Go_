import math
import random

from Game import Game


class Node():
    "A node for Monte Carlo Tree Search"
    playerNum = 0 #player num in this turn (player who makes the next move, didn't make this move)
    parent = None #parent of node
    children = [] #children of this node
    wins = 0.0 #number of games won from this position
    plays = 0.0 #total number of games played from this position
    gameState = None #board in the state of after the move this node represents was played
    move = [] #move from parent that lead to this node
    C = math.sqrt(0.2) #exploration constant

    def __init__(self, _playerNum, _gameState, _move, _parent, win = 0, played = 0):
        self.children = []
        self.playerNum = _playerNum

        self.gameState = _gameState.copy()
     #   print "copied gameSTate"
        self.move = [x for x in _move]
        self.parent = _parent
        self.wins = win
        self.plays = played


    def UCT(self):
        "returns the UCT value of this node for the selection stage"
        self.wins = float(self.wins)
        return (self.wins / self.plays) + (self.C * math.sqrt(math.log(self.parent.plays, math.e) / self.plays))

    def rollOut(self):
        "plays a roll-out to the end of the game & back-propagates result to all parents"

        rollOutGame = self.gameState.copy()
        tempPlayer = self.playerNum
        while(rollOutGame.getWin() == 0):
            moves = []
            #get all available moves
            moves = rollOutGame.getAllAvailableMoves()
            #make random move
            randMove = random.choice(moves)
            rollOutGame.makeMove(tempPlayer, randMove)
            tempPlayer = (tempPlayer%2) + 1


        win = rollOutGame.getWin()

        # back-propagate rollout to all parents statistics
        temp = self

        while(temp != None):
           # print "backprop to temp:" , temp.win , temp.played, temp.playerNum
            temp.plays += 1
            #if(temp.parent != None and win != 0 and temp.parent.playerNum == win):
            if (win != 0 and (temp.playerNum%2)+1 == win):
               # print "incremented win"
                temp.wins += 1
            if(win == 3):
                temp.wins += 0.5
            temp = temp.parent


def hasAllPossibleChildren(node):
    "returns [] if node has all children for all possible moves or [r,c] for possible move left without child"
    childrenLeft = node.children[:] #shallow copy of children list

    # check if node has child for each available move
    for move in node.gameState.getAllAvailableMoves():
    #    print "move", move
        # check if node already has a child for that move
        for child in childrenLeft:
            if(child.move[0] == move[0] and child.move[1] == move[1]):
           #     print "child got move:", move
                childrenLeft.remove(child)
                break
        else: #if loop finished without break - there's no child for current mvoe, return move

            return [move[0], move[1]]
  #  print "Returns empty"
    return []


def mcts(node):
    # print "MCTS"
    "recursive monte carlo tree search for given node"

    if(node.gameState.getWin() != 0): #if node is end game leaf
        node.rollOut()
        return

    possibleMoveWithoutChild = hasAllPossibleChildren(node)
    #print possibleMoveWithoutChild

    if(len(possibleMoveWithoutChild) == 0): #if this node has a child for every possible move from its position
        # SELECTION
        # go to child with max UCT value
        childToUct = {c : c.UCT() for c in node.children} #dictionary child to its UCT score

        # get child with max UCT score
        maxScore = max(childToUct.values())
        maxChild = None
        for child in childToUct:
            if(maxScore == childToUct[child]):
                maxChild = child
                break
        mcts(maxChild)
    else:
        # EXPANTION
        # node.board[possibleMoveWithoutChild[0]][possibleMoveWithoutChild[1]] = node.playerNum
        node.gameState.makeMove(node.playerNum, possibleMoveWithoutChild)
        newChild = Node((node.playerNum%2)+1,node.gameState, possibleMoveWithoutChild, node)

        node.gameState.undoMove(possibleMoveWithoutChild)
        #node.board[possibleMoveWithoutChild[0]][possibleMoveWithoutChild[1]] = 0

        newChild.rollOut() #SIMULATION & BACK PROPAGATION

        # else:

        node.children = node.children + [newChild]


def getMoveMCTS(gameState, player):
    TIMES = 1000
    root = Node(player, gameState, (), None)
    #to MCTS repeatedly 'TIMES' times
    for i in range(TIMES):
        mcts(root)

    maxScore = -100
    maxChild = None
  #  print "total playes:" , root.plays
    for child in root.children:
        print child.UCT() ,child.wins, child.plays, child.move
        if(child.UCT() > maxScore):
            maxScore = child.UCT()
            maxChild = child

    return maxChild.move


# testing
from ticTacToeGame import TicTacToeGame

globalBoard = None


def isWin(num, board):
    for r in board:
        if(r[0] == num and r[1] == num and r[2] == num):
            return True
    for c in range(3):
        if(board[0][c] == num and board[1][c] == num and board[2][c] == num):
            return True
    if(board[0][0] == num and board[1][1] == num and board[2][2] == num):
        return True
    if (board[0][2] == num and board[1][1] == num and board[2][0] == num):
        return True


def isTie(board):
    for r in board:
        for val in r:
            if val == 0:
                return False
    return True

def getWin(board):
    "3 draw, 0 not end of the game, 1 player1, 2 player2"
    if(isWin(1, board)):
        return 1
    if (isWin(2, board)):
        return 2
    if(isTie(board)):
        return 3
    return 0

def printBoard(board):
    print "-"*10
    for r in range(len(board)):
        strline = ""
        for col in range(len(board[r])):
            c = " "
            if(board[r][col] == 1):
                c = "X"
            elif(board[r][col] == 2):
                c = "Y"
            c+=" " + "| "if (col != 2) else " "
            strline += c

        print strline

    print "-" * 10
counter = 0
def getScoreAlphaBetta(player, depth, a, b):
    global counter
    global globalBoard
    counter+=1
   # printBoard()
    "alpha-betta pruning"
    if (getWin(globalBoard) == 1):
        return 100 - depth if player == 1 else 100 + depth
    elif (getWin(globalBoard) == 2):
        return -100 - depth if player == 1 else -100 + depth
    elif (getWin(globalBoard) == 3):
        return 0 - depth if player == 1 else 0 + depth

    if(player == 1):
        v = -1000
        for r in range(len(globalBoard)):
            for c in range(len(globalBoard[r])):
                if (globalBoard[r][c] == 0):
                    globalBoard[r][c] = 1
                    v = max(v, getScoreAlphaBetta(2, depth+1, a, b))
                    globalBoard[r][c] = 0
                    a = max(a,v)
                    if(b <= a):
                        break
            else:
                continue #if inner loop ended normally
            break #if inner loop was 'break'-ed
        return v
    else:
        v = 1000
        for r in range(len(globalBoard)):
            for c in range(len(globalBoard[r])):
                if (globalBoard[r][c] == 0):
                    globalBoard[r][c] = 2
                    v = min(v, getScoreAlphaBetta(1, depth + 1, a, b))
                    globalBoard[r][c] = 0
                    b = min(b, v)
                    if (b <= a):
                        break
            else:
                continue  # if inner loop ended normally
            break  # if inner loop was 'break'-ed
        return v

def getMoveAlphaBetta(player):
    "alpha betta pruning"
    "minmax"
    scores = []
    for r in range(len(globalBoard)):
        for c in range(len(globalBoard[r])):
            if (globalBoard[r][c] == 0):
                globalBoard[r][c] = player

                scores = scores + [(r, c, getScoreAlphaBetta((player % 2) + 1, 1, -1000, 1000))]
                globalBoard[r][c] = 0

    best_move = max(scores, key=lambda v: v[2]) if player == 1 else min(scores, key=lambda v: v[2])
    return best_move

def pvcMCTS():
    game = TicTacToeGame()
    while (1):
        game.printMe()
        row, col = input("Enter <row>,<col>")
        game.makeMove(1, [row, col])
        if (game.getWin() != 0):
            break
        game.printMe()
        move = getMoveMCTS(game, 2)

        game.makeMove(2, [move[0], move[1]])
        if (game.getWin() != 0):
            break

    game.printMe()
    if (game.getWin() != 3):
        print "player", ('X' if game.getWin() == 1 else 'Y'), "won!"
    else:
        print "tie"

def MCTSvsAlphaBetta():
    global globalBoard
    game = TicTacToeGame()
    while 1:
        globalBoard = game.board
        game.printMe()
        move  = getMoveAlphaBetta(1)
        game.makeMove(1, [move[0], move[1]])
        if (game.getWin() != 0):
            break
        game.printMe()
        move = getMoveMCTS(game, 2)

        game.makeMove(2, [move[0], move[1]])
        if (game.getWin() != 0):
            break

    game.printMe()
    if (game.getWin() != 3):
        print "player", ('X' if game.getWin() == 1 else 'Y'), "won!"
    else:
        print "tie"

pvcMCTS()
#MCTSvsAlphaBetta()