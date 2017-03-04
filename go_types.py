from Go import BoardState
import json

class Match:
    '''
    Represents a Go match
    '''

    def __init__(self, user_black, user_white, size, spectating = []):
        '''
        Constructor
        :param user_black: username of player that plays black
        :param user_white: username of player that plays white
        :param size: sie of board
        :param spectating: list of usernames that are spectating the game
        '''
        self.user_black = user_black
        self.user_white = user_white
        self.spectating = spectating
        self.state = BoardState(size)

    def get_opponent(self, username):
        '''

        :param username: username of player
        :return: username of given player's opponent
        '''
        print "get_opponent got:" , username , "returns:" , self.user_black if self.user_white == username else self.user_white
        return self.user_black if self.user_white == username else self.user_white

    def board_state_to_json(self):
        '''

        :return: JSON encoded string of match data
        '''
        data = {'size':self.state.size, 'board':self.state.board, 'turn':self.state.turn}
        return json.dumps(data)

class PendingMatch:
    '''
    Reresents a pending match (match that has not yet started)
    '''
    def __init__(self, user_black, size):
        self.user_black = user_black
        self.board_size = size
