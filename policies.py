from random import random

from ai.NeuralNetwork import NeuralNetwork


class Move_scorer():
    def _get_moves_score(self, state):
        raise BaseException("abstract method called")

class Expansion_policy(Move_scorer):

    def __init__(self, max_expansion_size):
        self.max_expansion_size = max_expansion_size


    def legal_move(self, state, move):
        raise BaseException("abstract method called")

    def get_moves(self, game_state):
        sorted_moves_by_score = sorted(self._get_moves_score(game_state), key=lambda x: x[1])[::-1]
        moves = []
        index = 0
        for x in sorted_moves_by_score:
            if index >= self.max_expansion_size:
                break
            if self.legal_move(game_state, x[0]):
                moves.append(x[0])
                index += 1

        #print "returning moves LEN:" , len(moves)
        return moves

class Rollout_policy(Move_scorer):

    def legal_move(self, state, move):
        raise BaseException("abstract method called")

    def get_move(self, game_state):
        sorted_moves_by_score = sorted(self._get_moves_score(game_state), key=lambda x: x[1])[::-1]
        #print "num of moves:" , len(sorted_moves_by_score)
        for x in sorted_moves_by_score:
            #if game_state.is_legal(x[0]) and not game_state.is_filling_self_eye(x[0]):
            if self.legal_move(game_state, x[0]):
                return x[0]
        return None

class TicTictactoe_random_policy():
    def legal_move(self, game_state, move):
        return game_state.board[move[0]][move[1]] == 0

    def _get_moves_score(self, state):
        return [((x/state.get_size(),x%state.get_size()), random()) for x in xrange(state.get_size() * state.get_size())]


class Tictactoe_random_expantion_policy(TicTictactoe_random_policy, Expansion_policy):

    def __init__(self, max_expansion_size):

        Expansion_policy.__init__(self, max_expansion_size)


class Tictactoe_random_rollout_policy(TicTictactoe_random_policy, Rollout_policy):
    pass


class Go_random_policy():
    def legal_move(self, game_state, move):
        return game_state.is_legal(move) and not game_state.is_filling_self_eye(move)

    def _get_moves_score(self, state):
        return [((x/state.get_size(),x%state.get_size()), random()) for x in xrange(state.get_size() * state.get_size())]


class Go_random_expantion_policy(Go_random_policy, Expansion_policy):

    def __init__(self, max_expansion_size):

        Expansion_policy.__init__(self, max_expansion_size)


class Go_random_rollout_policy(Go_random_policy, Rollout_policy):
    pass


class Go_NN_policy():

    def __init__(self, nn_weights_file_path):
        self.neural_network = NeuralNetwork([(9 * 9 * 3) + 2, 80, 50, 80, 9 * 9])
        self.neural_network.load_from('nn_weights.txt')
    def legal_move(self, game_state, move):
        return game_state.is_legal(move) and not game_state.is_filling_self_eye(move)

    def _get_moves_score(self, state):
        self.neural_network.set_inputs(state.to_nn_input_arr())
        self.neural_network.forward_propagation()
        nn_outputs = self.neural_network.get_outpus()
        return [((x/state.get_size(),x%state.get_size()), nn_outputs[x]) for x in xrange(state.get_size() * state.get_size())]


class Go_NN_expansion_policy(Go_NN_policy, Expansion_policy):

    def __init__(self, max_expansion_size, nn_weights_file_path):

        Expansion_policy.__init__(self, max_expansion_size)
        Go_NN_policy.__init__(self,nn_weights_file_path)


class Go_NN_rollout_policy(Go_NN_policy, Rollout_policy):

    def __init__(self, nn_weights_file_path):
        Go_NN_policy.__init__(self,nn_weights_file_path)



class Simulator():
    def simulate(self, game_state, first_player, rollout_policy):
        raise BaseException("abstract method called")

class Tictactoe_Simulator(Simulator):
    def simulate(self, game_state, first_player, rollout_policy):
        """
        simulates game and returns result
        :param game_state: state that simulation starts from
        :param first_player: player that starts
        :param rollout_policy: policy that selects moves
        :return: 1 - p1 won, 2 - p2 won, 3 - tie
        """
        rollOutGame = game_state.copy()
        tempPlayer = first_player
        while (rollOutGame.getWin() == 0):
            moves = []
            # get all available moves
            # moves = rollOutGame.getAllAvailableMoves()
            # make random move
            # randMove = random.choice(moves)
            rollOutGame.makeMove(tempPlayer, rollout_policy.get_move(rollOutGame))
            tempPlayer = (tempPlayer % 2) + 1
        return rollOutGame.getWin()

class Go_Simulator(Simulator):
    def simulate(self, game_state_original, first_player, rollout_policy, dbg = False):
        """
        simulates game and returns result
        :param game_state: state that simulation starts from
        :param first_player: player that starts
        :param rollout_policy: policy that selects moves
        :return: 1 - p1 won, 2 - p2 won, 3 - tie
        """
        # todo: this simulation sometimes goes forever - FIX
        #print "started simulation"
        game_state = game_state_original.copy()
        move = rollout_policy.get_move(game_state)
        passed_once = False
        passed_twice = False
        #pass_counter = 0
        moves_counter = 0
        passes_white = 0
        passes_black = 0
        got_stuck_once = False
        tempPlayer = first_player
        while not passed_twice:  # game ends when two sides pass
            #print game_state.board
            # print_board_debug = dbg
            # if print_board_debug:
            # if False:
            #     for row in game_state.board:
            #         for val in row:
            #             print val, " ",
            #         print ""
            #     print ""
            #         #####################################################
            # if pass_counter >= 3:
            #     print "pass overflow"
            #     break
            if passes_white >= 2 and passes_black >= 2:
                print "pass overflow"
                break

               # break
            if move is None:
                if tempPlayer == 1:
                    passes_black += 1
                else:
                    passes_white += 1
                game_state.play_pass_move()
                #pass_counter += 1
                # print "pass:" , pass_counter
            else:

                game_state.makeMove(tempPlayer,move)
            moves_counter += 1
            tempPlayer = (tempPlayer % 2) + 1
            if moves_counter >= game_state.size * game_state.size * 3: #a game can go on forever in some cases, make a random move to prevent that

                print game_state.board
                if got_stuck_once:
                    print "moves overflow twice", moves_counter
                    return game_state.getWin()
                else:
                    print "moves overflow once", moves_counter
                    moves_counter = 0
                    move = Go_random_rollout_policy().get_move(game_state)
                    got_stuck_once = True
            else:
                move = rollout_policy.get_move(game_state)

            if move is None:

                if passed_once:
                    passed_twice = True
                else:
                    passed_once = True
            else:
                passed_once = False

        # print_board_debug = dbg
        # if print_board_debug:
        #     for row in game_state.board:
        #         for val in row:
        #             print val , " ",
        #         print ""
        #print "end simulation"
        # print "finished simulation with:" , moves_counter , " moves"
        # print game_state.board
        return game_state.getWin()

#TEST
# from GoGame import GoGame
# Go_Simulator().simulate(GoGame(5), 1, Go_random_rollout_policy())
