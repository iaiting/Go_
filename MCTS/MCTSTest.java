package MCTS;

import java.util.Scanner;

import MCTS.Policies.GoNNExpantionPolicy;
import MCTS.Policies.GoNNRolloutPolicy;
import MCTS.Policies.GoNNAndCapturesExpansionPolicy;
import goTrain.GoLogic;

public class MCTSTest {

	public static void main(String[] args) {
		GoLogic game = new GoLogic(9);
		MCTS mcts = new MCTS(new GoNNAndCapturesExpansionPolicy(5,"nn_weights.txt"), new GoNNRolloutPolicy("nn_weights.txt"), new GoSimulator());
		Scanner s = new Scanner(System.in);
		while(true){
			game.printMe();
			int row = s.nextInt();
			int col = s.nextInt();
			game.makeMove(1, new int[]{row,col});
			if(game.getWin() != 0)
				break;
			game.printMe();
			int[] move = mcts.getMove(game, 2, 20);
			System.out.println("ai move:" + move[0] + "," + move[1]);
			//game.makeMove(2, new int[]{move[0],move[1]});
			row = s.nextInt();
			col = s.nextInt();
			game.makeMove(2, new int[]{row,col});
			if(game.getWin() != 0)
				break;
		}
		game.printMe();
		if(game.getWin() != 3)
			System.out.println("someone won");
		else
			System.out.println("tie");
	}

}
