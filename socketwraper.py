import socket
import sys
from thread import *
import time
import Queue
from socket_utils import *



class SocketWrapper():
    """
    A socket wrapper that uses inputs & queues for asynchronous input/output
    """
    UPDATES_DELAY_SEC = 0.1

    def __init__(self, sock):
        '''
        Constructor
        :param sock: socket to create the wrapper from
        '''
        self.socket = sock
        self.pending_outputs = Queue.Queue()
        self.pending_inputs= Queue.Queue()
        self.running = True
        start_new_thread(self._send_outputs, ())
        start_new_thread(self._receive_inputs, ())

    def _send_outputs(self):
        '''
        sends the top output in the pending queue through socket
        :return:
        '''
        while self.running:
            if self.pending_outputs.empty():
                time.sleep(self.UPDATES_DELAY_SEC)
                continue
            self.socket.sendall(self.pending_outputs.get())

    def _receive_inputs(self):

       '''
       checks socket for incoming input data. if exists, adds to input queue
       :return:
       '''
       while self.running:
           try:
                val = self.socket.recv(1024)
                if self.running:
                    self.pending_inputs.put(val)
           except socket.error as err:
               print "SOCKET ERROR:" , err
               return

    def send_output(self, out):
        '''
        adds given meesage to output Queue. given message will be sent through socket when it's the first in the queue.
        :param out:
        :return:
        '''
        self.pending_outputs.put(out)

    def get_input(self):
        '''

        :return: firt pending input in queue that was received or None if no input has been received.
        '''
        if self.pending_inputs.empty():
            return None
        return self.pending_inputs.get()



    def request_response(self, request, response_prefix, onResponse):
        '''A request-response callback combination.
        sends request, then calls onResponse when gets a response with matching 'response_prefix' prefix
        '''
        self.send_output(request)

        def wait_for_matching_response():
            "called in separate thread, waits for response that matches given prefix"
            found = False
            while not found:
                input = self.get_input()
                if input == None :
                    time.sleep(self.UPDATES_DELAY_SEC)
                    continue
                response_dict = SocketUtils.decode_request(input)
                if response_dict['prefix'] == response_prefix:
                    print "socketWrapper received matching response", input, "Sending to callback:",response_dict['prefix']
                    onResponse(response_dict)
                    found = True
                else:
                    self.pending_inputs.put(input)

        start_new_thread(wait_for_matching_response, ())

class SocketWrapperWithPush(SocketWrapper):
    '''
    A socket wrapper with push messages capability. extends the SocketWrapper.
    '''
    def __init__(self, sock):
        '''
        Constructor
        :param sock: socket the wrap with push capability.
        '''
        SocketWrapper.__init__(self, sock)
        self.push_callback = None # function that will be called when receives push message through socket

    def set_push_callback(self, push_callback):
        '''
        sends a push messgae to client.
        :param push_callback: callback to be caleld on push response.
        :return:
        '''
        self.push_callback = push_callback

    def _receive_inputs(self):
       '''overloaded receive inputs. adds input from socket to inputs queue'''
       while self.running:
           try:
                val = self.socket.recv(1024)
                if self.running:
                    # check if message is push
                    if ("push" in val) and (SocketUtils.decode_request(val)['push'] == 'True'):
                        if self.push_callback != None:
                            self.push_callback(SocketUtils.decode_request(val))
                    else:
                        self.pending_inputs.put(val)
           except socket.error as err:
               print "SOCKET ERROR:" , err
               return

class SocketWrapperSingleton():
    '''
    A singleton class that insures there is only one publicly available SocketWrapper singleton in the program's runtime.
    '''
    _instance = None

    @staticmethod
    def get(socket = None):
        """
        returns the Scoket Wrapper singleton.
        :param socket: socket to wrap. should be passed as parameter only on first user of this singleton. after that, should be left empty since the singelton has alread been created.
        :return: @type SocketWrapper
        """
        if(SocketWrapperSingleton._instance is None):
            if(socket is None):
                raise BaseException("Cannot instantiate SocketWrapperSingleton for first time without socket")
            SocketWrapperSingleton._instance = SocketWrapperWithPush(socket)
            SocketWrapperSingleton._instance.username = "UNDEFINED"

        return SocketWrapperSingleton._instance

