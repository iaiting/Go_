import math
import random

from Game import Game
#from mcts_test.ticTacToeGame import TicTacToeGame
#from mcts_test.ticTacToeGame import TicTacToeGame
from policies import Tictactoe_random_rollout_policy, Tictactoe_random_expantion_policy, Tictactoe_Simulator, Go_random_expantion_policy, Go_random_rollout_policy, Go_Simulator, Go_NN_expansion_policy, Go_NN_rollout_policy
from GoGame_Logic import GoGame_Logic
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
        """
        @:type _gameState Game
        :param _playerNum:
        :param _gameState:
        :param _move:
        :param _parent:
        :param win:
        :param played:
        """
        self.children = []
        self.playerNum = _playerNum
        self.gameState = _gameState.copy()
        if len(_move) != 0:
            self.gameState.makeMove((_playerNum%2)+1, _move)

        self.move = [x for x in _move]
        self.parent = _parent
        self.wins = win
        self.plays = played


    def UCT(self):
        "returns the UCT value of this node for the selection stage"
        self.wins = float(self.wins)
        return (self.wins / self.plays) + (self.C * math.sqrt(math.log(self.parent.plays, math.e) / self.plays))

    def rollOut(self, simulator, rollout_policy):
        """plays a roll-out to the end of the game & back-propagates result to all parents
        @:type rollout_policy Rollout_policy
        """

        win = simulator.simulate(self.gameState, self.playerNum, rollout_policy)

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

    def set_children_moves(self, moves):
        self.children_moves = moves


class MCTS():
    def __init__(self, expansion_policy, rollout_policy, simulator):
        self.expansion_policy = expansion_policy
        self.rollout_policy = rollout_policy
        self.simulator = simulator

    def get_move(self, game_state, player, rollout_times):
        TIMES = rollout_times
        root = Node(player, game_state, (), None)
        root.set_children_moves(self.expansion_policy.get_moves(root.gameState))

        # to MCTS repeatedly 'TIMES' times
        for i in range(TIMES):
            print i
            self.mcts(root)

        maxScore = -100
        maxChild = None
        #  print "total playes:" , root.plays
        #print "num of childre:" , len(root.children)
        for child in root.children:
           # print child.UCT() ,child.wins, child.plays, child.move
            #child.gameState.printMe()

            # note: I changed that in the actual move selection (not travel down the tree) will chooce that move with the highest win rate (without taking the exploration factor into account)
            child_score = child.wins / float(child.plays)  # child.UCT()
            # if child_score == 1.0:
            #     self.simulator.simulate(child.gameState, (child.playerNum%2)+1, self.rollout_policy, True)
            if (child_score > maxScore):
                maxScore = child_score
                maxChild = child

        return maxChild.move

    def get_next_expansion_move(self, node):
        "returns [] if node has all children for all possible moves or [r,c] for possible move left without child"
        # todo: work with tuples and sets(use hash on tuples) to minimize search time
        #print "LEN", len(self.expansion_policy.get_moves(node.gameState))
       # print node.gameState.board
       #  for move in self.expansion_policy.get_moves(node.gameState): #node.gameState.getAllAvailableMoves():
       #      if move not in [(child.move[0],child.move[1]) for child in node.children]:
       #          return move
       #  return []

        for move in node.children_moves: #node.gameState.getAllAvailableMoves():
            if move not in [(child.move[0],child.move[1]) for child in node.children]:
                return move
        return []

    def mcts(self, node):
        "recursive monte carlo tree search for given node"

        if (node.gameState.game_finished()):  # if node is end game leaf
            node.rollOut(self.simulator, self.rollout_policy)
            return

        possibleMoveWithoutChild = self.get_next_expansion_move(node)
        # print possibleMoveWithoutChild

        if (len(possibleMoveWithoutChild) == 0):  # if this node has a child for every possible move from its position
            # SELECTION
            # go to child with max UCT value
            childToUct = {c: c.UCT() for c in node.children}  # dictionary child to its UCT score

            # get child with max UCT score
            maxScore = max(childToUct.values())
            maxChild = None
            for child in childToUct:

                if (maxScore == childToUct[child]):
                    maxChild = child
                    break
            self.mcts(maxChild)
        else:
            # EXPANTION

            newChild = Node((node.playerNum % 2) + 1, node.gameState, possibleMoveWithoutChild, node)
            newChild.set_children_moves(self.expansion_policy.get_moves(newChild.gameState))
            newChild.rollOut(self.simulator, self.rollout_policy)  # SIMULATION & BACK PROPAGATION
            #print "adding children to size:" , len(node.children)
            node.children = node.children + [newChild]

def pvcMCTS():
    #game = TicTacToeGame()
    game = GoGame_Logic(9)
   # mcts = MCTS(Tictactoe_random_expantion_policy(100), Tictactoe_random_rollout_policy(), Tictactoe_Simulator())#MCTS(NN_Expansion_Policy(), NN_Rollout_policy())
   #  mcts = MCTS(Go_random_expantion_policy(100), Go_random_rollout_policy(),
   #             Go_Simulator())  # MCTS(NN_Expansion_Policy(), NN_Rollout_policy())
    mcts = MCTS(Go_NN_expansion_policy(5, 'nn_weights.txt'), Go_NN_rollout_policy('nn_weights.txt'),
                Go_Simulator())  # MCTS(NN_Expansion_Policy(), NN_Rollout_policy())

    while (1):
        game.printMe()
        row, col = input("Enter <row>,<col>")
        game.makeMove(1, [row, col])
        if (game.getWin() != 0):
            break
        game.printMe()
        move = mcts.get_move(game, 2, 20)

        game.makeMove(2, [move[0], move[1]])
        if (game.getWin() != 0):
            break

    game.printMe()
    if (game.getWin() != 3):
        print "player", ('X' if game.getWin() == 1 else 'Y'), "won!"
    else:
        print "tie"

def MCTS_test_against_random():
    wins= 0
    lost = 0
    tie = 0
    games = 20
    #mcts = MCTS(Tictactoe_random_expantion_policy(100), Tictactoe_random_rollout_policy(), Tictactoe_Simulator())#MCTS(NN_Expansion_Policy(), NN_Rollout_policy())
    mcts = MCTS(Go_random_expantion_policy(100), Go_random_rollout_policy(), Go_Simulator())  # MCTS(NN_Expansion_Policy(), NN_Rollout_policy())
    for x in xrange(games):
        #game = TicTacToeGame()
        game = GoGame_Logic(5)
        while (1):
            game.printMe()
           # row, col = input("Enter <row>,<col>")
            move = random.choice(game.getAllAvailableMoves())
            game.makeMove(1, [move[0], move[1]])
            if (game.getWin() != 0):
                break
           # game.printMe()
            move = mcts.get_move(game, 2, 100)

            game.makeMove(2, [move[0], move[1]])
            if (game.getWin() != 0):
                break

      #  game.printMe()
        win_state = game.getWin()
        if win_state == 1:
           # game.printMe()
            lost += 1
            print "lost", lost
        elif win_state == 2:
            wins += 1
            print "won", wins
        else:
            print "tie"
            tie += 1

    print wins, lost, tie

#MCTS_test_against_random()
#pvcMCTS()