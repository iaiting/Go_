import json
class SocketUtils():
    '''
    A calss that provides Utilities to be used with a Scoet.
    '''

    @staticmethod
    def incode_request(data):
        """
        :param data: dictionary of data
        :return: string of data incoded to JSON
        """
        return json.dumps(data)


    @staticmethod
    def decode_request(reqeust_str):
        """
        :param reqeust_str: request string sent over socket
        :return: dictionary decoded from JSON in request string
        """
        return json.loads(reqeust_str)
