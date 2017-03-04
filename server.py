'''
    Go server
'''

import socket
import sys
from thread import *
import time
import Queue
from socketwraper import SocketWrapper
from go_types import Match, PendingMatch
from socket_utils import *

class Client(SocketWrapper):
    '''
    The client class. Extends ScocketWrapper. Responsible for wrapping the communication between: Client->Server
    '''
    def __init__(self, sock):
        '''
        Constructor
        :param sock: The socket of the client
        '''
        SocketWrapper.__init__(self, sock)
        self.username = "UNDEFINED"
        self.online = True


HOST = ''
PORT = 8888

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print "socket created"

try:
    server_socket.bind((HOST, PORT))
except socket.error as msg:
    print "bind failed"
    sys.exit()

print "socket bind complete"
# start listening from max 20 clients
server_socket.listen(20)



clients = []
pending_matches = []
current_matches = []
server_running = True

def get_client_by_username(username):
    '''

    :param username: username of cliet
    :return: ClientWrapper with matching username, or None if not found
    '''
    for client in clients:
        if client.username == username:
            return client
    return None
def match_offer_still_valid(creator_username):
    '''

    :param creator_username:
    :return: true if match offer is still valid"
    '''
    return True # todo remove
    for match in pending_matches:
        if match.user_black == creator_username:

            return True
    return False

def get_pending_match(creator_username):
    '''returns true if match offer is still valid'''
    for match in pending_matches:
        if match.user_black == creator_username:
            return match
    return None


def create_match(username, size):
    '''
    creates pending match from given data. adds to pending match queue.
    :param username: username that initiated the pending match
    :param size: size of the go board in the match
    :return:
    '''
    pending_matches.append(PendingMatch(username, size))


def get_players_pending_matches():
    '''returns a list of current players who want to play a match'''
    players = []
    for match in pending_matches:
        players.append(match.user_black)
    players.append("Test")
    return players

def get_players_current_matches():
    '''returns a list of current players who are playing in a match'''
    players = []
    for match in current_matches:
        players.append(match.user_black + " VS " + match.user_white)
    players.append("Test VS TESTY")
    return players

def get_current_match_of(username):
    '''
    returns the current match the the given player is playing at.
    :param username: username of  player
    :return: the match given player currently plays in.
    '''
    for match in current_matches:
        if match.user_black == username or match.user_white == username:
            return match
    return None

def handle_client(client_socketWrapper):
    '''
    handels communication between Server and a specific client. Should be threaded so it would not block the main thread.
    :param client_socketWrapper: SocketWrapper for communication with the client.
    :return:
    '''
    """
    @type client_socketWrapper Client
    """
    while(server_running and client_socketWrapper.online):
        request = client_socketWrapper.get_input()
        if request is None:
            time.sleep(SocketWrapper.UPDATES_DELAY_SEC)
            continue
        print "Server got:", request
        request_dict = SocketUtils.decode_request(request)
        #process client's request
        if request_dict['prefix'] == 'login':
            username = request_dict['username']
            print "Server got login with" , username
            client_socketWrapper.username = username
            client_socketWrapper.send_output(SocketUtils.incode_request({'prefix': 'login', 'status': 'OK'}))
        if request_dict['prefix'] == 'acceptMatch':
            creator_username = request_dict['creator'] # username that created the match offer
            match_offer = get_pending_match(creator_username)
            if match_offer: # if match offer still exists
                client_socketWrapper.send_output(SocketUtils.incode_request({'prefix': 'acceptMatch', 'status': 'OK', 'opponent': match_offer.user_black, 'size': str(match_offer.board_size)})) #TODO: put size instead of 19
                get_client_by_username(creator_username).send_output(SocketUtils.incode_request({'push': 'True', 'prefix': 'matchAccepted', 'opponent': client_socketWrapper.username, 'size': str(match_offer.board_size)}))
                pending_matches.remove(match_offer) # remove match from pending match
                current_matches.append(Match(creator_username, client_socketWrapper.username, match_offer.board_size)) #add match to current matches
            else:
                client_socketWrapper.send_output(SocketUtils.incode_request({'prefix': 'acceptMatch', 'status': 'FAIL'}))
                pass
        if request_dict['prefix'] == 'createMatch':
            create_match(client_socketWrapper.username, request_dict['size'])
        if request_dict['prefix'] == 'refresh':
            print "server got refresh"
            client_socketWrapper.send_output(SocketUtils.incode_request({'prefix':'refresh', 'available': get_players_pending_matches(), 'to_watch': get_players_current_matches()}))
        if request_dict['prefix'] == 'watchMatch':
            match = get_current_match_of(request_dict['user1'])
            if match:
                match.spectating.append(client_socketWrapper.username)
                client_socketWrapper.send_output(SocketUtils.incode_request(
                    {'prefix': 'watchMatch', 'status':'OK', 'boardState': match.board_state_to_json(), 'size':str(match.state.size)}))
            else:
                client_socketWrapper.send_output(SocketUtils.incode_request(
                    {'status': 'False'}))
        if request_dict['prefix'] == 'makeMove': # player updates that he made a move
            # send push update of move to opponent
            match = get_current_match_of(client_socketWrapper.username)
            match.state.playMove((int(request_dict['row']), int(request_dict['col'])))
            get_client_by_username(match.get_opponent(client_socketWrapper.username)).send_output(SocketUtils.incode_request({'push': 'True', 'prefix': 'makeMove', 'row':request_dict['row'], 'col': request_dict['col']}))
            # update spectators
            for spectator in match.spectating:
                get_client_by_username(spectator).send_output(
                    SocketUtils.incode_request(
                        {'push': 'True', 'prefix': 'makeMove', 'row': request_dict['row'], 'col': request_dict['col']}))

        if request_dict['prefix'] == 'makePassMove' or request_dict['prefix'] == 'make  ResignMove':
            # send push update of move to opponent
            match = get_current_match_of(client_socketWrapper.username)
            get_client_by_username(match.get_opponent(client_socketWrapper.username)).send_output(
                SocketUtils.incode_request(
                    {'push': 'True', 'prefix': request_dict['prefix']}))
        if request_dict['prefix'] == 'chat':
            match = get_current_match_of(client_socketWrapper.username)
            get_client_by_username(match.get_opponent(client_socketWrapper.username)).send_output(
                SocketUtils.incode_request(
                    {'push': 'True', 'prefix': 'chat', 'message':request_dict['message']}))
while 1:
    # wait for connection request, blocking
    conn, addr = server_socket.accept()
    print "connected with client"
    client_socketWrapper = Client(conn)
    clients.append(client_socketWrapper)
    start_new_thread(handle_client, (client_socketWrapper,))

server_socket.close()