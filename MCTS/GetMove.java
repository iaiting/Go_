package MCTS;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.Arrays;
import java.util.Scanner;

import MCTS.Policies.GoNNAndCapturesExpansionPolicy;
import MCTS.Policies.GoNNRolloutPolicy;
import goTrain.GoLogic;
import neuralNetImproved.NeuralNetwork;

public class GetMove{

	
	/**
	 * @param args
	 * args[0] - string of board
	 * args[1] - current player turn
	 * args[2] - number of MCTS simulations
	 * args[3] - 0 to return move, 1 to return possible moves(children of MCTS root)
	 */
	public static void main(String[] args){
		
		

		MCTS mcts = new MCTS(new GoNNAndCapturesExpansionPolicy(5,"/nn_weights.txt"), new GoNNRolloutPolicy("/nn_weights.txt"), new GoSimulator());
		GoLogic game = new GoLogic(9);
		//parse from string to board array
		int row = 0, col = 0;
		for(int i = 0; i < args[0].length(); i++){
			char c = args[0].charAt(i);
			if(c == ',')
				col++;
			else if(c == '|'){
				row++;
				col = 0;
			}
			else{
				game.board[row][col] = Integer.parseInt(c+"");
			}
		}
		game.turn = Integer.valueOf(args[1]);
		if(args[3].equals("0")){ //return selected move after MCT search
//			System.out.println("---");
//			for(int i = 0; i < game.board.length; i++){
//					System.out.println(Arrays.toString(game.board[i]));
//			}
//			System.out.println("---");
			int[] move = mcts.getMove(game, Integer.valueOf(args[1]), Integer.valueOf(args[2]));
			System.out.println(move[0] + "," + move[1]);
		}else{ //return considerable moves
			for(int[] move : new GoNNAndCapturesExpansionPolicy(5, "/nn_weights.txt").getMoves(game)){
				System.out.println(move[0] + "," + move[1] +( move.length == 3 ? "," + move[2] : ""));
			}
		}
		
	
	}

	private static void initNnWeights(NeuralNetwork nn) {
	

	}

	/*
	 //generates code for nn weights
	private static void printStuff() {
		Scanner s;
		NeuralNetwork nn = new NeuralNetwork(new int[]{9*9*3, 80, 50, 80, 9*9});
		try {
			s = new Scanner(new File("nn_weights.txt"));
		} catch (FileNotFoundException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
			return;
		}
		String out = "";
		s.useDelimiter(",");
		StringBuilder sb = new StringBuilder();
		      try {
		    
		
		         
		         for(int beginLayer = 0; beginLayer < nn.weights.length; beginLayer++){
		        	 System.out.println(beginLayer);
		 			for(int neuronIndex = 0; neuronIndex < nn.weights[beginLayer].length; neuronIndex++){
		 				//System.out.println(neuronIndex);
		 				for(int neuronDest = 0; neuronDest < nn.weights[beginLayer][neuronIndex].length; neuronDest++){
		 					String next = s.next();
		 					nn.weights[beginLayer][neuronIndex][neuronDest] = Double.valueOf(next);
		 					sb.append("nn.weights["+beginLayer+"]["+neuronIndex+"]["+neuronDest+"] = " + Double.valueOf(next)+"\n");
		 					//out+="nn.weights["+beginLayer+"]["+neuronIndex+"]["+neuronDest+"] = " + Double.valueOf(next);
		 					//System.out.println("1");
		 					//System.out.println(weights[beginLayer][neuronIndex][neuronDest]); 
		 						
		 				}
		 			}
		 			
		 		}
		         
		      }finally {
		       
		         if (s != null) {
		            	s.close();
				}
		      }
		      System.out.println("writing to file");
		      try (Writer writer = new BufferedWriter(new OutputStreamWriter(
		              new FileOutputStream("code_for_weights.txt"), "utf-8"))) {
		   try {
			writer.write(sb.toString());
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		} catch (UnsupportedEncodingException e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
		} catch (FileNotFoundException e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
		} catch (IOException e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
		}
	}
	*/
}
