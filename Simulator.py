from kivy.core.window import Window

from Go import BoardState
from random import randrange
from random import random

from NeuralNetwork import NeuralNetwork


class Simulator:

    @staticmethod
    def simulate(state, policy):
        """
        @type state BoardState
        """

        move = policy.get_move(state)
        passed_once = False
        passed_twice = False
        pass_counter = 0
        while not passed_twice: # game ends when two sides pass
            if pass_counter >= 20:
                print "pass overflow"
                return
            if move is None:
                state.play_pass_move()
                pass_counter += 1
               # print "pass:" , pass_counter
            else:
                if pass_counter >= 50:
                    print move
                state.playMove(move)

            move = policy.get_move(state)

            if move is None:

                if passed_once:
                    passed_twice = True
                else:
                    passed_once = True
            else:
                passed_once = False

        print state.board

class Policy():
    "defines a Go playing policy"

    def _get_moves_score(self, state):
        raise BaseException("Abstract method called")

    def get_move(self, state):
        """"
        @type state BoardState
        """
        # for row in xrange(state.size):
        #     for col in xrange(state.size):
        #

        sorted_moves_by_score = sorted(self._get_moves_score(state), key=lambda x: x[1])[::-1]

        for x in sorted_moves_by_score:
            if state.is_legal(x[0]) and not state.is_filling_self_eye(x[0]):
                return x[0]
        return None

class RandGoPolicy(Policy):

    def _get_moves_score(self, state):
        return [((x/state.size,x%state.size), random()) for x in xrange(state.size * state.size)]



class NeuralNetPolicy(Policy):

    def __init__(self):
        self.nn =  NeuralNetwork([(9*9*3) + 2, 80, 50, 80, 9*9])
        self.nn.load_from('nn_weights.txt')

    def _get_moves_score(self, state):
        #TODO: get outputs from neuralNet, try not to create it each time but to user a static NN or something to be shared across instances
        self.nn.set_inputs(state.to_nn_input_arr())
        self.nn.forward_propagation()
        outputs = self.nn.get_outpus()
        return [((x / state.size, x % state.size), outputs[x]) for x in xrange(state.size * state.size)]

# policy = RandGoPolicy()
# print RandGoPolicy().get_move(BoardState(13))
state = BoardState(9)
Simulator.simulate(state, NeuralNetPolicy())




from Go import GoScreen

from kivy.app import App
import json

def board_state_to_json(state):
    data = {'size': state.size, 'board': state.board, 'turn': state.turn}
    return json.dumps(data)

class GoApp(App):

    def build(self):
        screen = GoScreen(ui_testing = True, ai = True, spectating = True, board_state = board_state_to_json(state))
        def win_cb(window, width, height):
            screen.game.handleWindowResize()

        Window.bind(on_resize=win_cb)
        return screen


if __name__ == "__main__":
    GoApp().run()