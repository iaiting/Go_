class Game():
    "abstract class that represents a game"

    def copy(self):
        pass
    def get_size(self):
        pass
    def makeMove(self, player, move):
        pass
    # def undoMove(self, move):
    #     pass
    def getWin(self):
        pass
    def game_finished(self):
        pass
    def getAllAvailableMoves(self):
        pass
    def printMe(self):
        pass