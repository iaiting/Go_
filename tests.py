from Go import BoardState

def get_group_test():
    board = BoardState(10)
    board.playMove([3,3])
    board.playMove([4,3])
    board.playMove([2,3])

    board.playMove([1,3])
    board.playMove([9,3])
    board.playMove([1,2])
    #print board.getGroup([3,3])
    print "get_group_test:" , (len(board.getGroup([3,3])) == 2)

get_group_test()

